from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

COMMAND_NAME = "start"

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /start."""
    texto = (
        "Use um dos comandos abaixo:\n"
        "/produtividade - Exibe um relatório interativo de produtividade.\n"
        "/os <NUMERO_OS> - Busca os detalhes de uma Ordem de Serviço."
    )
    await update.message.reply_text(texto)

handler = CommandHandler(COMMAND_NAME, command_handler)