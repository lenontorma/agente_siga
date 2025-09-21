from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CommandHandler, 
    CallbackQueryHandler, 
    ConversationHandler
)
from telegram.constants import ParseMode
import os
import sys
from logging_utils import log_command

# Garante que os módulos da pasta 'analysis' possam ser importados
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    if 'sys' in locals(): del sys

from analysis.data_loader import carregar_dados
from analysis import produtividade

COMMAND_NAME = "produtividade"

# Define os "estados" da conversa
SELECTING_SECCIONAL, SELECTING_PROCESSO, SELECTING_EQUIPE = range(3)

async def start_produtividade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa e mostra o primeiro menu (Seccionais)."""
    log_command(update)
    keyboard = [
        [InlineKeyboardButton("CENTRO SUL", callback_data="seccional:CENTRO SUL")],
        [InlineKeyboardButton("CAMPANHA", callback_data="seccional:CAMPANHA")],
        [InlineKeyboardButton("SUL", callback_data="seccional:SUL")],
        [InlineKeyboardButton("LITORAL SUL", callback_data="seccional:LITORAL SUL")],
        [InlineKeyboardButton("TODAS", callback_data="seccional:TODAS")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📊 Por favor, escolha uma seccional:", reply_markup=reply_markup)
    return SELECTING_SECCIONAL

async def select_processo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a Seccional e mostra o segundo menu (Processos)."""
    query = update.callback_query
    await query.answer()
    seccional_escolhida = query.data.split(':')[1]
    
    context.user_data['seccional'] = seccional_escolhida
    
    keyboard = [
        [InlineKeyboardButton("CORTE", callback_data=f"processo:CORTE")],
        [InlineKeyboardButton("LIGAÇÃO NOVA", callback_data=f"processo:LIGACAO NOVA")],
        [InlineKeyboardButton("EMERGÊNCIAL", callback_data=f"processo:EMERGENCIAL")],
        [InlineKeyboardButton("TODOS", callback_data=f"processo:TODOS")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    seccional_texto = seccional_escolhida if seccional_escolhida != "TODAS" else "Todas as Seccionais"
    await query.edit_message_text(
        text=f"Seccional: *{seccional_texto}*.\n\nAgora, escolha o processo:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_PROCESSO

async def show_team_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o Processo, busca as equipes e mostra o menu de seleção com a opção de Resumo."""
    query = update.callback_query
    await query.answer()
    
    processo_escolhido = query.data.split(':')[1]
    seccional_escolhida = context.user_data.get('seccional')
    
    # Guarda o processo na memória da conversa
    context.user_data['processo'] = processo_escolhido
    
    await query.edit_message_text(text="Buscando equipes para os filtros selecionados, por favor aguarde...")

    df = carregar_dados()
    
    seccional_filtro = None if seccional_escolhida.upper() == 'TODAS' else seccional_escolhida
    processo_filtro = None if processo_escolhido.upper() == 'TODOS' else processo_escolhido
    
    lista_equipes = produtividade.obter_equipes_por_filtro(df, seccional_filtro, processo_filtro)

    if not lista_equipes:
        await query.edit_message_text(text="Nenhuma equipe encontrada para os filtros selecionados.")
        return ConversationHandler.END

    # --- LÓGICA DO NOVO MENU ---
    # 1. Cria o botão de Resumo primeiro
    keyboard = [
        [InlineKeyboardButton("📊 Ver Resumo HTML", callback_data="resumo_html")]
    ]
    
    # 2. Cria os botões para cada equipe e os adiciona ao teclado
    for equipe in lista_equipes:
        keyboard.append([InlineKeyboardButton(equipe, callback_data=f"equipe_select:{equipe}")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    seccional_texto = seccional_escolhida if seccional_escolhida != "TODAS" else "Todas"
    processo_texto = processo_escolhido if processo_escolhido != "TODOS" else "Todos"

    await query.edit_message_text(
        text=f"Filtros: *{seccional_texto}* | *{processo_texto}*\n\n"
             f"Encontradas *{len(lista_equipes)}* equipes. Escolha uma para ver os detalhes ou veja o resumo em HTML:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_EQUIPE

async def generate_team_report_and_map(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a equipe, gera o resumo em texto E o mapa, e envia ambos."""
    query = update.callback_query
    await query.answer()
    
    equipe_escolhida = query.data.split(':')[1]
    await query.edit_message_text(text=f"Gerando resumo e mapa para a equipe `{equipe_escolhida}`...", parse_mode='Markdown')

    df = carregar_dados()
    
    # Gera e envia o resumo em texto
    resposta_texto = produtividade.gerar_resumo_por_equipe(df, equipe_escolhida)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=resposta_texto, parse_mode=ParseMode.MARKDOWN)
    
    # Gera o mapa
    mapa_html = produtividade.gerar_mapa_por_equipe_html(df, equipe_escolhida)
    
    if mapa_html:
        caminho_raiz_projeto = os.path.dirname(os.path.dirname(caminho_src))
        caminho_data = os.path.join(caminho_raiz_projeto, "Data")
        caminho_saida_mapa = os.path.join(caminho_data, f"mapa_{equipe_escolhida}.html")
        
        with open(caminho_saida_mapa, 'w', encoding='utf-8') as f: f.write(mapa_html)
            
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Localização das atividades da equipe no mapa: 👇")
        with open(caminho_saida_mapa, 'rb') as mapa_file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=mapa_file)
        
        os.remove(caminho_saida_mapa)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="_Nenhuma atividade com coordenadas encontradas para esta equipe._", parse_mode=ParseMode.MARKDOWN)
        
    context.user_data.clear()
    return ConversationHandler.END

async def generate_summary_html_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gera e envia o relatório HTML com base nos filtros da conversa."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    seccional = context.user_data.get('seccional')
    processo = context.user_data.get('processo')
    
    await query.edit_message_text(text="Gerando relatório HTML, por favor aguarde...")
    
    try:
        df = carregar_dados()
        seccional_filtro = None if seccional == 'TODAS' else seccional
        processo_filtro = None if processo == 'TODOS' else processo

        relatorio_html = produtividade.gerar_relatorio_principal_html(df, seccional=seccional_filtro, processo=processo_filtro)
        
        caminho_raiz_projeto = os.path.dirname(os.path.dirname(caminho_src))
        caminho_data = os.path.join(caminho_raiz_projeto, "Data")
        caminho_saida = os.path.join(caminho_data, "relatorio_produtividade_filtrado.html")
        
        with open(caminho_saida, 'w', encoding='utf-8') as f: f.write(relatorio_html)

        await context.bot.send_message(chat_id=chat_id, text="Seu relatório HTML está pronto! 👇")
        with open(caminho_saida, 'rb') as relatorio_file:
            await context.bot.send_document(chat_id=chat_id, document=relatorio_file)
            
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Ocorreu um erro: {e}")
        
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query: await query.edit_message_text(text="Operação cancelada.")
    else: await update.message.reply_text(text="Operação cancelada.")
    context.user_data.clear()
    return ConversationHandler.END

handler = ConversationHandler(
    entry_points=[CommandHandler(COMMAND_NAME, start_produtividade)],
    states={
        SELECTING_SECCIONAL: [CallbackQueryHandler(select_processo, pattern="^seccional:")],
        SELECTING_PROCESSO: [CallbackQueryHandler(show_team_menu, pattern="^processo:")],
        SELECTING_EQUIPE: [
            CallbackQueryHandler(generate_team_report_and_map, pattern="^equipe_select:"),
            CallbackQueryHandler(generate_summary_html_report, pattern="^resumo_html$")
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)