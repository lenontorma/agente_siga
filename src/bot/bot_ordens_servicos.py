from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode

from analysis.data_loader import carregar_dados
from analysis import servicos

COMMAND_NAME = "os"

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /os."""
    try:
        if not context.args:
            await update.message.reply_text("Por favor, digite o número da OS após o comando.\nEx: `/os 123456`")
            return
        
        df = carregar_dados()
        if df.empty:
            await update.message.reply_text("A base de dados não pôde ser carregada.")
            return

        numero_os_busca = context.args[0]
        resposta_analise = servicos.buscar_ordem_servico(df, numero_os_busca)
        
        await update.message.reply_text(resposta_analise, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        await update.message.reply_text(f"Ocorreu um erro ao buscar a OS: {e}")

handler = CommandHandler(COMMAND_NAME, command_handler)