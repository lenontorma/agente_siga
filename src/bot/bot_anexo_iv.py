from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler
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
from analysis import servicos

COMMAND_NAME = "anexo_iv"

SELECTING_SECCIONAL = range(1)

async def start_anexo_iv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Relatório com serviços de ANEXO IV."""
    log_command(update) # <-- ADICIONA A LINHA DE LOG
    keyboard = [
        [InlineKeyboardButton("CENTRO SUL", callback_data="anexo_seccional:CENTRO SUL")],
        [InlineKeyboardButton("CAMPANHA", callback_data="anexo_seccional:CAMPANHA")],
        [InlineKeyboardButton("SUL", callback_data="anexo_seccional:SUL")],
        [InlineKeyboardButton("LITORAL SUL", callback_data="anexo_seccional:LITORAL SUL")],
        [InlineKeyboardButton("TODAS (Arquivo HTML)", callback_data="anexo_seccional:TODAS")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔎 Escolha uma seccional para o resumo de vencimentos de Anexo IV, ou 'TODAS' para o relatório completo:", reply_markup=reply_markup)
    return SELECTING_SECCIONAL

async def generate_and_send_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a Seccional e decide se envia um texto ou um arquivo HTML."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    seccional_escolhida = query.data.split(':')[1]
    
    await query.edit_message_text(text=f"Gerando relatório para '{seccional_escolhida}', por favor aguarde...")
    
    try:
        df = carregar_dados()
        
        # --- LÓGICA CONDICIONAL APLICADA AQUI ---
        if seccional_escolhida.upper() == 'TODAS':
            # Gera e envia o arquivo HTML completo
            relatorio_html = servicos.gerar_relatorio_vencimentos_anexo_iv(df, seccional=None)
            
            caminho_raiz_projeto = os.path.dirname(os.path.dirname(caminho_src))
            caminho_data = os.path.join(caminho_raiz_projeto, "Data")
            caminho_saida = os.path.join(caminho_data, "relatorio_vencimentos_anexo_iv.html")
            
            with open(caminho_saida, 'w', encoding='utf-8') as f:
                f.write(relatorio_html)

            await context.bot.send_message(chat_id=chat_id, text="Seu relatório HTML completo está pronto! 👇")
            with open(caminho_saida, 'rb') as relatorio_file:
                await context.bot.send_document(chat_id=chat_id, document=relatorio_file)
        else:
            # Gera e envia a mensagem de texto resumida
            resposta_texto = servicos.gerar_resumo_vencimentos_texto(df, seccional=seccional_escolhida)
            await context.bot.send_message(chat_id=chat_id, text=resposta_texto, parse_mode=ParseMode.MARKDOWN)
        
        # Apaga a mensagem do menu ("Gerando relatório...")
        await query.delete_message()
            
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Ocorreu um erro ao gerar o relatório: {e}")
        
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a operação."""
    query = update.callback_query
    if query:
        await query.edit_message_text(text="Operação cancelada.")
    else:
        await update.message.reply_text(text="Operação cancelada.")
    return ConversationHandler.END

handler = ConversationHandler(
    entry_points=[CommandHandler(COMMAND_NAME, start_anexo_iv)],
    states={
        SELECTING_SECCIONAL: [CallbackQueryHandler(generate_and_send_report, pattern="^anexo_seccional:")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False
)