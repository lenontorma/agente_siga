from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CommandHandler, 
    CallbackQueryHandler, 
    ConversationHandler
)
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
SELECTING_SECCIONAL, SELECTING_PROCESSO = range(2)

async def start_produtividade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa de produtividade e mostra o primeiro menu (Seccionais)."""
    keyboard = [
        [InlineKeyboardButton("CENTRO SUL", callback_data="seccional:CENTRO SUL")],
        [InlineKeyboardButton("CAMPANHA", callback_data="seccional:CAMPANHA")],
        [InlineKeyboardButton("SUL", callback_data="seccional:SUL")],
        [InlineKeyboardButton("LITORAL SUL", callback_data="seccional:LITORAL SUL")],
        [InlineKeyboardButton("TODAS AS SECCIONAIS", callback_data="seccional:TODAS")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📊 Por favor, escolha uma seccional para o relatório:", reply_markup=reply_markup)
    return SELECTING_SECCIONAL

async def select_processo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a Seccional e mostra o segundo menu (Processos)."""
    query = update.callback_query
    await query.answer()
    seccional_escolhida = query.data.split(':')[1]
    
    keyboard = [
        [InlineKeyboardButton("CORTE", callback_data=f"processo:CORTE:{seccional_escolhida}"),
         InlineKeyboardButton("LIGACAO NOVA", callback_data=f"processo:LIGACAO NOVA:{seccional_escolhida}")],
        [InlineKeyboardButton("EMERGENCIAL", callback_data=f"processo:EMERGENCIAL:{seccional_escolhida}"),
         InlineKeyboardButton("TODOS", callback_data=f"processo:TODOS:{seccional_escolhida}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    seccional_texto = "Todas" if seccional_escolhida == "TODAS" else seccional_escolhida
    await query.edit_message_text(
        text=f"Seccional escolhida: *{seccional_texto}*.\n\nAgora, escolha o processo:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_PROCESSO

async def generate_and_send_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe os filtros, gera o relatório HTML, os detalhes, e envia o arquivo principal."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    _, processo_escolhido, seccional_escolhida = query.data.split(':', 2)
    
    seccional_filtro = None if seccional_escolhida.upper() == 'TODAS' else seccional_escolhida
    processo_filtro = None if processo_escolhido.upper() == 'TODOS' else processo_escolhido

    try:
        df = carregar_dados()
        # Prepara caminhos
        caminho_src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho_raiz_projeto = os.path.dirname(caminho_src_dir)
        caminho_data = os.path.join(caminho_raiz_projeto, "Data")
        caminho_relatorios_detalhados = os.path.join(caminho_data, "reports")
        os.makedirs(caminho_relatorios_detalhados, exist_ok=True)

        # Gera o HTML principal com os filtros
        relatorio_principal_html = produtividade.gerar_relatorio_detalhado_html(df, seccional=seccional_filtro, processo=processo_filtro)
        caminho_saida_principal = os.path.join(caminho_data, "relatorio_produtividade.html")
        with open(caminho_saida_principal, 'w', encoding='utf-8') as f:
            f.write(relatorio_principal_html)

        # Gera os detalhes (necessário para os links)
        df_equipes_para_relatorio = df[df['Processo'] != 'CORTE MOTO']
        equipes_unicas = df_equipes_para_relatorio[df_equipes_para_relatorio['Recurso'].str.startswith('RS-', na=False)]['Recurso'].unique()
        for equipe in equipes_unicas:
            relatorio_detalhe_html = produtividade.gerar_relatorio_detalhado_html(df, equipe)
            nome_arquivo_detalhe = f"{equipe}.html"
            caminho_saida_detalhe = os.path.join(caminho_relatorios_detalhados, nome_arquivo_detalhe)
            with open(caminho_saida_detalhe, 'w', encoding='utf-8') as f:
                f.write(relatorio_detalhe_html)

        await context.bot.send_message(chat_id=chat_id, text="Seu relatório está pronto! 👇")
        with open(caminho_saida_principal, 'rb') as relatorio_file:
            await context.bot.send_document(chat_id=chat_id, document=relatorio_file)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Ocorreu um erro ao gerar o relatório: {e}")
        
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.edit_message_text(text="Operação cancelada.")
    else:
        await update.message.reply_text(text="Operação cancelada.")
    return ConversationHandler.END

handler = ConversationHandler(
    entry_points=[CommandHandler(COMMAND_NAME, start_produtividade)],
    states={
        SELECTING_SECCIONAL: [CallbackQueryHandler(select_processo, pattern="^seccional:")],
        SELECTING_PROCESSO: [CallbackQueryHandler(generate_and_send_report, pattern="^processo:")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False
)