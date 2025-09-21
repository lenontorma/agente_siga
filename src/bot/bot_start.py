from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler
from telegram.constants import ParseMode
import os
import importlib
from logging_utils import log_command # Importa nossa nova função

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /start."""
    log_command(update) # <-- ADICIONA A LINHA DE LOG

# O comando que o usuário digita no Telegram
COMMAND_NAME = "start"

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para o comando /start.
    Gera a mensagem de ajuda dinamicamente, descobrindo outros comandos.
    """
    
    texto_boas_vindas = " "
    texto_comandos = "Use um dos comandos abaixo:\n"
    
    # --- LÓGICA DE DESCOBERTA DINÂMICA CORRIGIDA ---
    try:
        comandos_encontrados = []
        bot_dir = os.path.dirname(__file__)

        for filename in sorted(os.listdir(bot_dir)):
            if filename.startswith('bot_') and filename.endswith('.py') and 'start' not in filename:
                module_name = filename[:-3]
                
                try:
                    module = importlib.import_module(f'bot.{module_name}')
                    
                    if hasattr(module, 'handler'):
                        cmd_name = getattr(module, 'COMMAND_NAME', module_name.replace('bot_', ''))
                        docstring = ""

                        # Verifica se o handler é de conversação ou simples
                        if isinstance(module.handler, ConversationHandler):
                            # Pega a docstring do primeiro ponto de entrada
                            if module.handler.entry_points:
                                docstring = module.handler.entry_points[0].callback.__doc__
                        elif isinstance(module.handler, CommandHandler):
                            docstring = module.handler.callback.__doc__
                        
                        # Usa a primeira linha da docstring como descrição
                        if docstring:
                            primeira_linha_doc = docstring.strip().split('\n')[0]
                        else:
                            primeira_linha_doc = f"Executa o comando /{cmd_name}"

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

    # Envia a mensagem final
    await update.message.reply_text(f"{texto_boas_vindas}\n{texto_comandos}", parse_mode=ParseMode.MARKDOWN)


# A variável que o main.py procura para registrar o comando
handler = CommandHandler(COMMAND_NAME, command_handler)