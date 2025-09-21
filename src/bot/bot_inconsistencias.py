from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.constants import ParseMode
import pandas as pd
import sys
import os
from logging_utils import log_command

# Garante que os módulos da pasta 'analysis' possam ser importados
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    if 'sys' in locals(): del sys

from analysis.data_loader import carregar_dados
from analysis import inconsistencias

COMMAND_NAME = "inconsistencias"

SELECTING_CHECK = range(1)

def _formatar_inconsistencias_texto(df_resultado: pd.DataFrame, titulo: str) -> str:
    """Função auxiliar para formatar os resultados de inconsistência em texto."""
    if df_resultado.empty:
        return "" # Retorna vazio se não houver dados
        
    resposta = f"\n*{titulo} ({len(df_resultado)} encontrada(s)):*\n"
    resposta += "-----------------------------------\n"
    
    for _, linha in df_resultado.iterrows():
        resposta += f"  - *OS:* `{linha['Ordem de Serviço']}`\n"
        resposta += f"    - *Equipe:* {linha['Recurso']}\n"
        resposta += f"    - *Cidade:* {linha['Cidade']}\n"
        resposta += f"    - *Tipo de OS:* {linha['Tipo de Atividade']}\n"
        # Mostra os campos problemáticos
        if 'Observação' in linha:
            resposta += f"    - *Observação:* _{linha['Observação']}_\n"
        resposta += "\n"
        
    return resposta


async def start_inconsistencias(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa e mostra o menu de verificações."""
    log_command(update)
    keyboard = [
        [InlineKeyboardButton("Conclusões Incorretas", callback_data="inconsistencia:conclusoes")],
        [InlineKeyboardButton("Cancelamentos por equipe", callback_data="inconsistencia:cancelamentos")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔎 *Menu de Verificação de Inconsistências*\n\nEscolha a verificação:", reply_markup=reply_markup, parse_mode='Markdown')
    return SELECTING_CHECK

async def send_inconsistency_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a escolha, gera o relatório em TEXTO e o envia."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    await query.edit_message_text(text="Executando verificação, por favor aguarde...")
    
    check_type = query.data.split(':')[1]
    
    try:
        df = carregar_dados()
        resposta_final = ""
        
        if df.empty:
            resposta_final = "A base de dados não pôde ser carregada ou está vazia."
        elif check_type == "conclusoes":
            df_resultado = inconsistencias.encontrar_conclusoes_improprias(df)
            if df_resultado.empty:
                resposta_final = "✅ Nenhuma inconsistência encontrada para 'Conclusões Incorretas'."
            else:
                resposta_final = _formatar_inconsistencias_texto(df_resultado, "Inconsistência: Tipos de Conclusão Incorretas")
                
        elif check_type == "cancelamentos":
            df_resultado = inconsistencias.encontrar_cancelamentos_suspeitos(df)
            if df_resultado.empty:
                resposta_final = "✅ Nenhuma inconsistência encontrada para 'Cancelamentos por equipe'."
            else:
                resposta_final = _formatar_inconsistencias_texto(df_resultado, "Inconsistência: Cancelamentos por equipe")

        # Apaga a mensagem do menu ("Executando verificação...")
        await query.delete_message()
        # Envia a resposta final como uma nova mensagem
        await context.bot.send_message(chat_id=chat_id, text=resposta_final, parse_mode=ParseMode.MARKDOWN)
            
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
    entry_points=[CommandHandler(COMMAND_NAME, start_inconsistencias)],
    states={
        SELECTING_CHECK: [CallbackQueryHandler(send_inconsistency_report, pattern="^inconsistencia:")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False
)