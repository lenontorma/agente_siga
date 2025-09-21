from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.constants import ParseMode
import sys
import os
from logging_utils import log_command


try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    if 'sys' in locals(): del sys

from analysis.data_loader import carregar_dados
from analysis import gerencial # <-- Importa do novo módulo gerencial

COMMAND_NAME = "gerencial"

SELECTING_REPORT = range(1)

async def start_gerencial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Resumo geral."""
    log_command(update)
    keyboard = [
        [InlineKeyboardButton("📊 Relatório Gerencial HTML", callback_data="gerencial:report_html")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📈 *Menu Gerencial*\n\nClique abaixo para gerar o relatório consolidado:", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    return SELECTING_REPORT

async def generate_macro_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Chama a função de análise para gerar e enviar o relatório HTML."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    await query.edit_message_text(text="Gerando relatório gerencial completo, por favor aguarde...")
    
    try:
        df = carregar_dados()
        
        if df.empty:
            await query.edit_message_text(text="A base de dados não pôde ser carregada ou está vazia.")
            return ConversationHandler.END

        # Chama a função do módulo 'gerencial' para criar o HTML
        relatorio_html = gerencial.gerar_relatorio_gerencial_html(df)
        
        caminho_raiz_projeto = os.path.dirname(os.path.dirname(caminho_src))
        caminho_data = os.path.join(caminho_raiz_projeto, "Data")
        caminho_saida = os.path.join(caminho_data, "relatorio_gerencial.html")
        
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.write(relatorio_html)

        await context.bot.send_message(chat_id=chat_id, text="Seu relatório gerencial consolidado está pronto! 👇")
        with open(caminho_saida, 'rb') as relatorio_file:
            await context.bot.send_document(chat_id=chat_id, document=relatorio_file)
        
        # Remove a mensagem de menu ("Gerando relatório...")
        await query.delete_message()
        
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
    entry_points=[CommandHandler(COMMAND_NAME, start_gerencial)],
    states={
        SELECTING_REPORT: [CallbackQueryHandler(generate_macro_report, pattern="^gerencial:")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False
)