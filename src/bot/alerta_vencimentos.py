import os
import sys
import pandas as pd
import telebot
from dotenv import load_dotenv

# --- Bloco de código para encontrar a pasta 'src' ---
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    del sys

from analysis.data_loader import carregar_dados
from analysis.servicos import encontrar_os_proximas_vencimento

def formatar_mensagem(df_seccional: pd.DataFrame, nome_seccional: str) -> str:
    """Formata a lista de OS para uma seccional específica."""
    
    # --- CABEÇALHO ESPECÍFICO DA SECCIONAL ---
    mensagem = f"📍 *Seccional: {nome_seccional.upper()}*\n"
    mensagem += "-----------------------------------\n"

    for _, os_info in df_seccional.iterrows():
        data_limite = os_info['Data Limite'].strftime('%d/%m/%Y %H:%M')
        
        mensagem += f"🔩 *Instalação:* `{os_info['Instalação']}`\n"
        mensagem += f"   - *Tipo:* {os_info['Tipo de Atividade']}\n"
        mensagem += f"   - *Status Atual:* {os_info['Status da Atividade']}\n"
        mensagem += f"   - *Vencimento:* {data_limite}\n"
        mensagem += f"   - *Equipe:* {os_info['Recurso']}\n"
        mensagem += f"   - *Cidade:* {os_info['Cidade']}\n\n"
    
    return mensagem

def enviar_alertas():
    """
    Função principal do script de alertas.
    """
    print("--- Iniciando script de alerta de vencimentos ---")
    
    caminho_raiz_projeto = os.path.dirname(caminho_src)
    load_dotenv(os.path.join(caminho_raiz_projeto, '.env'))
    
    bot_token = os.getenv("BOT_TOKEN")
    user_ids_str = os.getenv("TELEGRAM_USER_IDS")

    if not bot_token or not user_ids_str:
        print("ERRO: BOT_TOKEN ou TELEGRAM_USER_IDS não encontrados no arquivo .env")
        return

    lista_de_ids = [uid.strip() for uid in user_ids_str.split(',')]
    
    try:
        df_completo = carregar_dados()
        if df_completo.empty:
            print("Não foi possível carregar os dados. Abortando alertas.")
            return

        df_para_alertar = encontrar_os_proximas_vencimento(df_completo)

        if df_para_alertar.empty:
            print("Nenhuma OS próxima do vencimento encontrada. Nenhuma mensagem enviada.")
            return

        # --- LÓGICA DE AGRUPAMENTO POR SECCIONAL ---
        
        # 1. Encontra a lista de seccionais únicas que têm alertas
        seccionais_com_alerta = df_para_alertar['Seccional'].unique()
        
        mensagem_final_completa = "🚨 *Alerta de Vencimento de OS (Anexo IV)* 🚨\n\n"
        
        # 2. Faz um loop por cada seccional
        for seccional in seccionais_com_alerta:
            # Filtra o DataFrame apenas para a seccional atual
            df_da_seccional = df_para_alertar[df_para_alertar['Seccional'] == seccional]
            
            # 3. Formata um bloco de mensagem para esta seccional
            bloco_mensagem_seccional = formatar_mensagem(df_da_seccional, seccional)
            mensagem_final_completa += bloco_mensagem_seccional
        
        bot = telebot.TeleBot(bot_token)
        
        print(f"Enviando alertas agrupados por seccional para {len(lista_de_ids)} usuários...")
        for user_id in lista_de_ids:
            try:
                # 4. Envia a mensagem completa e agrupada
                bot.send_message(user_id, mensagem_final_completa, parse_mode='Markdown')
                print(f"  - Alerta enviado com sucesso para o usuário ID: {user_id}")
            except Exception as e:
                print(f"  - Falha ao enviar para o usuário ID: {user_id}. Erro: {e}")

        print("--- Script de alerta finalizado com sucesso! ---")

    except FileNotFoundError:
        print("ERRO: Arquivo 'prod_gstc.xlsx' não foi encontrado. Execute a transformação primeiro.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado no script de alertas: {e}")

if __name__ == "__main__":
    enviar_alertas()