import os
import sys
import importlib
import logging
import traceback
from telegram import Update
from telegram.ext import Application, ContextTypes
from dotenv import load_dotenv

# --- Bloco de Inicialização para Execução Autônoma ---
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    if 'sys' in locals(): del sys

# --- CONFIGURAÇÃO DE LOGGING ---
# Configura o logger para imprimir informações úteis e erros no terminal
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


## --- NOVA FUNÇÃO: O TRATADOR DE ERROS GLOBAL --- ##
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Captura todas as exceções não tratadas e as registra, enviando uma
    mensagem de erro amigável ao usuário.
    """
    # 1. Registra o erro detalhado no seu terminal (para você depurar)
    logger.error("Exceção enquanto processava uma atualização:", exc_info=context.error)

    # Formata o traceback para um log mais detalhado
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    logger.error(f"Traceback completo:\n{tb_string}")

    # 2. Envia uma mensagem amigável para o usuário
    if isinstance(update, Update) and update.effective_chat:
        texto_erro = (
            "🤖 Ocorreu um erro inesperado ao processar sua solicitação.\n\n"
            "A equipe de desenvolvimento já foi notificada. Por favor, tente novamente mais tarde."
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=texto_erro)


def run_bot():
    """Inicia o bot do Telegram, registra os comandos e o tratador de erros."""
    print("--- Iniciando Bot do Telegram ---")
    
    # Carrega as variáveis de ambiente
    caminho_raiz_projeto = os.path.dirname(caminho_src)
    load_dotenv(os.path.join(caminho_raiz_projeto, '.env'))
    
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        print("ERRO CRÍTICO: BOT_TOKEN não encontrado no arquivo .env")
        return

    application = Application.builder().token(bot_token).build()

    # --- ADIÇÃO: REGISTRO DO TRATADOR DE ERROS ---
    # Esta linha garante que qualquer erro em qualquer comando será capturado.
    application.add_error_handler(error_handler)

    # --- LÓGICA DE REGISTRO DE COMANDOS (MAIS LIMPA) ---
    bot_dir = os.path.dirname(__file__)
    
    print("\nRegistrando comandos encontrados...")
    for filename in os.listdir(bot_dir):
        if filename.startswith('bot_') and filename.endswith('.py'):
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f'bot.{module_name}')
                
                if hasattr(module, 'handler'):
                    application.add_handler(module.handler)
                    cmd_name = getattr(module, 'COMMAND_NAME', module_name)
                    print(f"  - Comando /{cmd_name} (do arquivo {filename}) registrado com sucesso.")
                else:
                    print(f"  - [AVISO] Módulo '{module_name}' não possui um 'handler' exportado.")
            except Exception as e:
                print(f"  - [ERRO CRÍTICO] Falha ao carregar o comando '{module_name}':\n    {e}")
    
    print("\n--- Bot iniciado e aguardando mensagens ---")
    application.run_polling()

if __name__ == '__main__':
    run_bot()