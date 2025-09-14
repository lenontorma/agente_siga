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
from analysis.servicos import classificar_os_para_alerta

def formatar_linhas_os(df_linhas: pd.DataFrame) -> str:
    """Função auxiliar que formata as linhas de um DataFrame de OS para texto."""
    texto = ""
    # Ordena por Data Limite para a mensagem ficar cronológica
    for _, os_info in df_linhas.sort_values(by='Data Limite').iterrows():
        data_limite = os_info['Data Limite'].strftime('%d/%m/%Y %H:%M')
        
        texto += f"🔩 *Instalação:* `{os_info['Instalação']}`\n"
        texto += f"   - *Tipo:* {os_info['Tipo de Atividade']}\n"
        texto += f"   - *Status Atual:* {os_info['Status da Atividade']}\n"
        texto += f"   - *Vencimento:* {data_limite}\n"
        texto += f"   - *Equipe:* {os_info['Recurso']}\n"
        texto += f"   - *Cidade:* {os_info['Cidade']}\n\n"
    return texto

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

        alertas_classificados = classificar_os_para_alerta(df_completo)

        df_vencidas = alertas_classificados["vencidas"]
        df_hoje = alertas_classificados["vencendo_hoje"]
        df_amanha = alertas_classificados["vencendo_amanha"]
        
        df_para_alertar_total = pd.concat([df_vencidas, df_hoje, df_amanha])
        
        if df_para_alertar_total.empty:
            print("Nenhuma OS para alertar. Nenhuma mensagem enviada.")
            return

        mensagem_final = "🚨 *Alerta de Vencimento de OS (Anexo IV)* 🚨\n"
        
        seccionais_com_alerta = df_para_alertar_total['Seccional'].unique()
        
        for seccional in sorted(seccionais_com_alerta):
            mensagem_final += f"\n\n📍 *Seccional: {seccional.upper()}*"
            mensagem_final += "\n-----------------------------------"
            
            # Filtra os alertas para a seccional atual
            df_vencidas_sec = df_vencidas[df_vencidas['Seccional'] == seccional]
            df_hoje_sec = df_hoje[df_hoje['Seccional'] == seccional]
            df_amanha_sec = df_amanha[df_amanha['Seccional'] == seccional]
            
            if not df_vencidas_sec.empty:
                mensagem_final += "\n\n🆘 *VENCIDAS* 🆘\n"
                mensagem_final += formatar_linhas_os(df_vencidas_sec)

            # --- LÓGICA DE UNIFICAÇÃO APLICADA AQUI ---
            # 1. Concatena os DataFrames de vencimentos próximos
            df_proximos_sec = pd.concat([df_hoje_sec, df_amanha_sec])

            # 2. Se a lista combinada não estiver vazia, cria a nova seção
            if not df_proximos_sec.empty:
                mensagem_final += "\n⚠️ *VENCIMENTO PRÓXIMO* ⚠️\n"
                mensagem_final += formatar_linhas_os(df_proximos_sec)

        bot = telebot.TeleBot(bot_token)
        print(f"Enviando alertas agrupados para {len(lista_de_ids)} usuários...")
        for user_id in lista_de_ids:
            try:
                bot.send_message(user_id, mensagem_final, parse_mode='Markdown')
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