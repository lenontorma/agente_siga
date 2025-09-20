from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode

# O comando que o usuário digita no Telegram
COMMAND_NAME = "start"

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /start."""
    
    # --- TEXTO ATUALIZADO COM O NOVO COMANDO ---
    texto = (
        "Olá! Bem-vindo ao Bot de Alertas e Consultas do SRD.\n\n"
        "Use um dos comandos abaixo:\n\n"
        "📊 */produtividade* - Abre um menu interativo para gerar o relatório de produtividade em HTML.\n\n"
        "🔎 */os* `<NUMERO_OS>` - Busca os detalhes de uma Ordem de Serviço específica. Ex: `/os 123456`\n\n"
        "⚠️ */anexo_iv* - Abre um menu para gerar o relatório de vencimentos de OS de Anexo IV."
    )
    
    # Usamos ParseMode.MARKDOWN para que a formatação com * e ` funcione.
    await update.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN)

# A variável que o main.py procura para registrar o comando
handler = CommandHandler(COMMAND_NAME, command_handler)