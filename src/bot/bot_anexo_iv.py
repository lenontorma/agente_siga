from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler
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
from analysis import servicos

COMMAND_NAME = "anexo_iv"

# Apenas um estado, pois o menu tem um único passo
SELECTING_SECCIONAL = range(1)

async def start_anexo_iv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa e mostra o menu de Seccionais."""
    keyboard = [
        [InlineKeyboardButton("CENTRO SUL", callback_data="anexo_seccional:CENTRO SUL")],
        [InlineKeyboardButton("CAMPANHA", callback_data="anexo_seccional:CAMPANHA")],
        [InlineKeyboardButton("SUL", callback_data="anexo_seccional:SUL")],
        [InlineKeyboardButton("LITORAL SUL", callback_data="anexo_seccional:LITORAL SUL")],
        [InlineKeyboardButton("TODAS", callback_data="anexo_seccional:TODAS")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔎 Por favor, escolha uma seccional para ver os vencimentos de Anexo IV:", reply_markup=reply_markup)
    return SELECTING_SECCIONAL

async def generate_and_send_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a Seccional, gera o relatório HTML e o envia."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    await query.edit_message_text(text="Gerando relatório de vencimentos, por favor aguarde...")
    
    seccional_escolhida = query.data.split(':')[1]
    seccional_filtro = None if seccional_escolhida.upper() == 'TODAS' else seccional_escolhida

    try:
        df = carregar_dados()
        
        # Chama a nova função de análise
        relatorio_html = servicos.gerar_relatorio_vencimentos_anexo_iv(df, seccional=seccional_filtro)
        
        caminho_raiz_projeto = os.path.dirname(os.path.dirname(caminho_src))
        caminho_data = os.path.join(caminho_raiz_projeto, "Data")
        caminho_saida = os.path.join(caminho_data, "relatorio_vencimentos_anexo_iv.html")
        
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.write(relatorio_html)

        await context.bot.send_message(chat_id=chat_id, text="Seu relatório de vencimentos está pronto! 👇")
        with open(caminho_saida, 'rb') as relatorio_file:
            await context.bot.send_document(chat_id=chat_id, document=relatorio_file)
            
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