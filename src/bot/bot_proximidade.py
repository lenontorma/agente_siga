from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
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

COMMAND_NAME = "proximidade"

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para o comando /proximidade.
    Uso: /proximidade <ID da OS ou Instalação>
    """
    log_command(update)
    chat_id = update.effective_chat.id
    
    if not context.args:
        await update.message.reply_text("Por favor, forneça o número da OS ou da Instalação.\nExemplo: `/proximidade 12345678`", parse_mode='Markdown')
        return
        
    id_referencia = context.args[0]
    await context.bot.send_message(chat_id=chat_id, text=f"Buscando serviços próximos à referência '{id_referencia}', por favor aguarde...")
    
    try:
        df = carregar_dados()
        if df.empty:
            await context.bot.send_message(chat_id=chat_id, text="A base de dados não pôde ser carregada.")
            return

        # Chama a nova função de análise para gerar o mapa
        resultado_mapa = servicos.gerar_mapa_proximidade(df, id_referencia)
        
        # Verifica se a função retornou um HTML ou uma mensagem de erro em texto
        if resultado_mapa.strip().startswith('<'): # É um HTML
            caminho_raiz_projeto = os.path.dirname(os.path.dirname(caminho_src))
            caminho_data = os.path.join(caminho_raiz_projeto, "Data")
            caminho_saida = os.path.join(caminho_data, "mapa_proximidade.html")
            
            with open(caminho_saida, 'w', encoding='utf-8') as f:
                f.write(resultado_mapa)

            await context.bot.send_message(chat_id=chat_id, text="Mapa de proximidade gerado! 👇")
            with open(caminho_saida, 'rb') as mapa_file:
                await context.bot.send_document(chat_id=chat_id, document=mapa_file)
        else: # É uma mensagem de erro
            await context.bot.send_message(chat_id=chat_id, text=resultado_mapa)
            
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Ocorreu um erro ao gerar o mapa: {e}")

# Exporta o handler para que o main.py possa registrá-lo
handler = CommandHandler(COMMAND_NAME, command_handler)