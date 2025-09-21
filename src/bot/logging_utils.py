import os
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update

def log_command(update: Update, context=None):
    """
    Registra o uso de um comando ou clique em botão em um arquivo CSV.
    """
    user = update.effective_user
    # Se não houver usuário, não há o que registrar.
    if not user:
        return

    # Extrai a informação do usuário
    user_id = user.id
    username = user.username or "N/A"
    full_name = user.full_name
    
    # Determina a ação com base no tipo de update
    action = "Ação Desconhecida"
    if update.message and update.message.text:
        # É uma mensagem de texto (comando)
        action = update.message.text.split(' ')[0]
    elif update.callback_query and update.callback_query.data:
        # É um clique em um botão
        action = f"Clique: {update.callback_query.data}"

    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
    timestamp = datetime.now(fuso_horario_brasil).strftime('%Y-%m-%d %H:%M:%S')

    try:
        caminho_script = os.path.abspath(__file__)
        caminho_bot = os.path.dirname(caminho_script)
        caminho_src = os.path.dirname(caminho_bot)
        caminho_raiz_projeto = os.path.dirname(caminho_src)
        caminho_data = os.path.join(caminho_raiz_projeto, "Data")
        log_filepath = os.path.join(caminho_data, "log_de_uso_bot.csv")

        os.makedirs(caminho_data, exist_ok=True)
        
        header = ['timestamp', 'user_id', 'username', 'full_name', 'action']
        file_exists = os.path.isfile(log_filepath)
        
        with open(log_filepath, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(header)
            
            writer.writerow([timestamp, user_id, username, full_name, action])
        
        print(f"[LOG] Ação '{action}' do usuário '{full_name}' (ID: {user_id}) foi registrada.")

    except Exception as e:
        print(f"!!! ERRO CRÍTICO no logger: Não foi possível escrever no arquivo de log. Causa: {e}")