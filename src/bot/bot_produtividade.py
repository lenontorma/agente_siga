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
    keyboard = [
        [InlineKeyboardButton("CENTRO SUL", callback_data="seccional:CENTRO SUL")],
        [InlineKeyboardButton("CAMPANHA", callback_data="seccional:CAMPANHA")],
        [InlineKeyboardButton("SUL", callback_data="seccional:SUL")],
        [InlineKeyboardButton("LITORAL SUL", callback_data="seccional:LITORAL SUL")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📊 Por favor, escolha uma seccional:", reply_markup=reply_markup)
    return SELECTING_SECCIONAL

async def select_processo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a Seccional e mostra o segundo menu (Processos)."""
    query = update.callback_query
    await query.answer()
    seccional_escolhida = query.data.split(':')[1]
    
    # Guarda a seccional na memória da conversa para o próximo passo
    context.user_data['seccional'] = seccional_escolhida
    
    keyboard = [
        [InlineKeyboardButton("CORTE", callback_data=f"processo:CORTE")],
        [InlineKeyboardButton("LIGACAO NOVA", callback_data=f"processo:LIGACAO NOVA")],
        [InlineKeyboardButton("EMERGENCIAL", callback_data=f"processo:EMERGENCIAL")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"Seccional: *{seccional_escolhida}*.\n\nAgora, escolha o processo para detalhar por equipe:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_PROCESSO

async def show_team_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o Processo, busca as equipes e mostra o menu de seleção de equipes."""
    query = update.callback_query
    await query.answer()
    
    processo_escolhido = query.data.split(':')[1]
    seccional_escolhida = context.user_data.get('seccional')
    
    await query.edit_message_text(text="Buscando equipes, por favor aguarde...")

    df = carregar_dados()
    lista_equipes = produtividade.obter_equipes_por_filtro(df, seccional_escolhida, processo_escolhido)

    if not lista_equipes:
        await query.edit_message_text(text="Nenhuma equipe encontrada para os filtros selecionados.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(equipe, callback_data=f"equipe_select:{equipe}")] for equipe in lista_equipes]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"Seccional: *{seccional_escolhida}* | Processo: *{processo_escolhido}*\n\nAgora, escolha a equipe:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_EQUIPE

async def generate_team_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Recebe a equipe, gera o resumo em texto E o mapa, e envia ambos.
    """
    query = update.callback_query
    await query.answer()
    
    equipe_escolhida = query.data.split(':')[1]
    await query.edit_message_text(text=f"Gerando resumo e mapa para a equipe `{equipe_escolhida}`...", parse_mode='Markdown')

    df = carregar_dados()
    
    # 1. Gera e envia o resumo em texto
    resposta_texto = produtividade.gerar_resumo_por_equipe(df, equipe_escolhida)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=resposta_texto, parse_mode=ParseMode.MARKDOWN)
    
    # 2. Gera o mapa
    mapa_html = produtividade.gerar_mapa_por_equipe_html(df, equipe_escolhida)
    
    if mapa_html:
        # Define um caminho temporário para salvar o mapa
        caminho_raiz_projeto = os.path.dirname(os.path.dirname(caminho_src))
        caminho_data = os.path.join(caminho_raiz_projeto, "Data")
        caminho_saida_mapa = os.path.join(caminho_data, f"mapa_{equipe_escolhida}.html")
        
        with open(caminho_saida_mapa, 'w', encoding='utf-8') as f:
            f.write(mapa_html)
            
        # Envia o arquivo do mapa
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Localização das atividades da equipe no mapa: 👇")
        with open(caminho_saida_mapa, 'rb') as mapa_file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=mapa_file)
        
        # Opcional: remover o arquivo de mapa após o envio para não acumular arquivos
        os.remove(caminho_saida_mapa)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="_Nenhuma atividade com coordenadas encontradas para esta equipe._", parse_mode=ParseMode.MARKDOWN)
        
    # Limpa a memória da conversa
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela e encerra a conversa."""
    query = update.callback_query
    if query: 
        await query.edit_message_text(text="Operação cancelada.")
    else: 
        await update.message.reply_text(text="Operação cancelada.")
    context.user_data.clear()
    return ConversationHandler.END

handler = ConversationHandler(
    entry_points=[CommandHandler(COMMAND_NAME, start_produtividade)],
    states={
        SELECTING_SECCIONAL: [CallbackQueryHandler(select_processo, pattern="^seccional:")],
        SELECTING_PROCESSO: [CallbackQueryHandler(show_team_menu, pattern="^processo:")],
        SELECTING_EQUIPE: [CallbackQueryHandler(generate_team_report, pattern="^equipe_select:")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False,
)