from telegram import Update, ReplyKeyboardRemove # Importa a ferramenta de remoção
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler
from telegram.constants import ParseMode
import os
import importlib
import sys

# Garante que os módulos da pasta 'bot' possam ser importados
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    if 'sys' in locals(): del sys

from bot.logging_utils import log_command

# O comando que o usuário digita no Telegram
COMMAND_NAME = "start"

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para o comando /start.
    Gera a mensagem de ajuda dinamicamente e remove qualquer teclado persistente.
    """
    log_command(update)
    
    texto_boas_vindas = "Olá! Bem-vindo ao Bot de Alertas e Consultas do SRD.\n"
    texto_comandos = "\nUse um dos comandos abaixo:\n"
    
    # --- LÓGICA DE DESCOBERTA DINÂMICA (sem alterações) ---
    try:
        comandos_encontrados = []
        bot_dir = os.path.dirname(__file__)

        for filename in sorted(os.listdir(bot_dir)):
            arquivos_para_ignorar = ['bot_start.py', 'main.py', 'logging_utils.py', '__init__.py', 'alerta_vencimentos.py']
            if filename.startswith('bot_') and filename.endswith('.py') and filename not in arquivos_para_ignorar:
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'bot.{module_name}')
                    if hasattr(module, 'handler'):
                        cmd_name = getattr(module, 'COMMAND_NAME', module_name.replace('bot_', ''))
                        docstring = ""
                        if isinstance(module.handler, ConversationHandler):
                            if module.handler.entry_points:
                                docstring = module.handler.entry_points[0].callback.__doc__
                        elif isinstance(module.handler, CommandHandler):
                            docstring = module.handler.callback.__doc__
                        
                        primeira_linha_doc = docstring.strip().split('\n')[0] if docstring else f"Executa o comando /{cmd_name}"
                        comandos_encontrados.append(f"➡️ */{cmd_name}* - {primeira_linha_doc}")
                except Exception as e:
                    print(f"  - [AVISO] Falha ao processar o comando '{module_name}': {e}")

        if comandos_encontrados:
            texto_comandos += "\n".join(comandos_encontrados)
        else:
            texto_comandos += "_Nenhum comando adicional encontrado._"

    except Exception as e:
        print(f"ERRO ao gerar menu /start dinâmico: {e}")
        texto_comandos = "Não foi possível carregar a lista de comandos."

    # --- ALTERAÇÃO APLICADA AQUI ---
    # Envia a mensagem final junto com o comando para remover o teclado
    await update.message.reply_text(
        text=f"{texto_boas_vindas}{texto_comandos}", 
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove() # <-- Esta linha remove o menu
    )

# A variável que o main.py procura para registrar o comando
handler = CommandHandler(COMMAND_NAME, command_handler)