import os
import sys
import importlib
from telegram.ext import Application
from dotenv import load_dotenv

# Adiciona a pasta 'src' ao caminho para garantir que os imports funcionem
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    del sys

def run_bot():
    """Inicia o bot do Telegram e registra todos os comandos da pasta 'bot'."""
    print("--- Iniciando Bot do Telegram ---")
    
    # Carrega as variáveis de ambiente
    caminho_raiz_projeto = os.path.dirname(caminho_src)
    load_dotenv(os.path.join(caminho_raiz_projeto, '.env'))
    
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        print("ERRO CRÍTICO: BOT_TOKEN não encontrado no arquivo .env")
        return

    application = Application.builder().token(bot_token).build()

    # --- LÓGICA DE DIAGNÓSTICO E REGISTRO ---
    bot_dir = os.path.dirname(__file__)
    
    print("\n--- Verificando arquivos na pasta 'src/bot/' ---")
    for filename in os.listdir(bot_dir):
        print(f"  - Encontrado: '{filename}'")
        # Verifica se o arquivo corresponde ao padrão de um módulo de comando
        if filename.startswith('bot_') and filename.endswith('.py'):
            print(f"    -> Corresponde ao padrão. Tentando registrar...")
            module_name = filename[:-3]
            try:
                # Importa o módulo (ex: bot.bot_produtividade)
                module = importlib.import_module(f'bot.{module_name}')
                
                if hasattr(module, 'handler'):
                    application.add_handler(module.handler)
                    cmd_name = getattr(module, 'COMMAND_NAME', module_name)
                    print(f"      ✅ Comando /{cmd_name} registrado com sucesso.")
                else:
                    print(f"      ❌ [AVISO] Módulo '{module_name}' não possui um 'handler' exportado.")
            except Exception as e:
                print(f"      ❌ [ERRO CRÍTICO] Falha ao carregar o comando '{module_name}':")
                print(f"         {e}")
        else:
            print(f"    -> Ignorando (não corresponde ao padrão 'bot_*.py').")
    
    print("\n--- Bot iniciado e aguardando mensagens ---")
    application.run_polling()

if __name__ == '__main__':
    run_bot()