from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler
from telegram.constants import ParseMode
import os
import importlib
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# Garante que os módulos da pasta 'bot' e 'analysis' possam ser importados
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    if 'sys' in locals(): del sys

from bot.logging_utils import log_command
from analysis.data_loader import carregar_dados

COMMAND_NAME = "start"

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para o comando /start.
    Gera a mensagem de ajuda e adiciona o "Selo de Validade" dos dados.
    """
    log_command(update)
    
    # --- LÓGICA DO SELO DE VALIDADE (CORRIGIDA) ---
    texto_status_dados = ""
    try:
        df = carregar_dados()
        if not df.empty and 'Data_Extracao' in df.columns:
            # Pega a data da extração mais recente (que vem sem fuso, ou 'naive')
            ultima_extracao_naive = df['Data_Extracao'].max()
            
            fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
            
            # Torna a data da extração "consciente" do fuso horário
            ultima_extracao_aware = ultima_extracao_naive.tz_localize(fuso_horario_brasil)
            
            # Pega o 'agora' também com fuso horário
            agora = datetime.now(fuso_horario_brasil)
            
            # Agora a subtração funciona, pois ambas as datas têm fuso horário
            diferenca = agora - ultima_extracao_aware
            
            minutos_atras = int(diferenca.total_seconds() / 60)

            if minutos_atras > 30:
                emoji_status = "⚠️"
                status = f"Atenção: Dados desatualizados (última atualização há {minutos_atras} minutos)."
            else:
                emoji_status = "✅"
                status = f"Dados atualizados (última atualização há {minutos_atras} minutos)."
            
            texto_status_dados = f"{emoji_status} *Status da Base:* {status}\n"
        else:
            texto_status_dados = "⚠️ *Status da Base:* Nenhuma base de dados encontrada.\n"
    except Exception as e:
        print(f"ERRO ao verificar status dos dados: {e}")
        texto_status_dados = "⚠️ *Status da Base:* Erro ao verificar a atualização dos dados.\n"

    # --- Montagem da Mensagem Final ---
    texto_boas_vindas = "Olá! Bem-vindo ao Bot de Consultas do SRD.\n\n"
    texto_comandos = "Use um dos comandos abaixo:\n"
    
    # Lógica de descoberta dinâmica (sem alterações)
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

    # Envia a mensagem final, agora incluindo o status dos dados no topo
    await update.message.reply_text(
        text=f"{texto_boas_vindas}{texto_status_dados}\n{texto_comandos}", 
        parse_mode=ParseMode.MARKDOWN
    )

handler = CommandHandler(COMMAND_NAME, command_handler)