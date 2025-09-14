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
from analysis.servicos import encontrar_os_vencendo_em_x_horas
from analysis import mappings

def formatar_mensagem_seccional(df_seccional: pd.DataFrame, nome_seccional: str) -> str:
    """Formata a mensagem para uma seccional específica, agrupando por tipo de alerta."""
    
    mensagem = f"🚨 *Alerta de Vencimento de OS (Anexo IV) - Seccional: {nome_seccional.upper()}* 🚨\n"

    df_vencidas = df_seccional[df_seccional['Alerta_Tipo'] == 'VENCIDA']
    df_proximas = df_seccional[df_seccional['Alerta_Tipo'] == 'PRÓXIMO DO VENCIMENTO']
    
    if not df_vencidas.empty:
        mensagem += "\n🆘 *VENCIDAS* 🆘\n"
        for _, os in df_vencidas.iterrows():
            # --- MENSAGEM ATUALIZADA COM MAIS DETALHES ---
            mensagem += f"  - *Instalação:* `{str(os['Instalação'])}`\n"
            mensagem += f"  - *Tipo de Nota:* {str(os['Tipo de Atividade'])}\n"
            mensagem += f"  - *Status:* {str(os['Status da Atividade'])}\n"
            mensagem += f"  - *Cidade:* {str(os['Cidade'])}\n"
            mensagem += f"  - *Equipe:* {str(os['Recurso'])}\n"
            mensagem += f"  - *Venceu em:* {os['Data Limite'].strftime('%d/%m/%Y %H:%M')}\n\n"
    
    if not df_proximas.empty:
        mensagem += "\n⚠️ *PRÓXIMAS DO VENCIMENTO (nas próximas 8h)* ⚠️\n"
        for _, os in df_proximas.iterrows():
            # --- MENSAGEM ATUALIZADA COM MAIS DETALHES ---
            mensagem += f"  - *Instalação:* `{str(os['Instalação'])}`\n"
            mensagem += f"  - *Tipo de Nota:* {str(os['Tipo de Atividade'])}\n"
            mensagem += f"  - *Status:* {str(os['Status da Atividade'])}\n"
            mensagem += f"  - *Cidade:* {str(os['Cidade'])}\n"
            mensagem += f"  - *Equipe:* {str(os['Recurso'])}\n"
            mensagem += f"  - *Vence às:* {os['Data Limite'].strftime('%d/%m/%Y %H:%M')}\n\n"

    return mensagem

def enviar_alertas_direcionados():
    """Função principal do script de alertas direcionados."""
    print("--- Iniciando script de alerta de vencimentos direcionados ---")
    
    caminho_raiz_projeto = os.path.dirname(caminho_src)
    load_dotenv(os.path.join(caminho_raiz_projeto, '.env'))
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("ERRO: BOT_TOKEN não encontrado no arquivo .env"); return

    try:
        df_completo = carregar_dados()
        if df_completo.empty:
            print("Não foi possível carregar os dados. Abortando."); return

        df_para_alertar = encontrar_os_vencendo_em_x_horas(df_completo, horas=8)

        if df_para_alertar.empty:
            print("Nenhuma OS para alertar. Nenhuma mensagem enviada."); return

        bot = telebot.TeleBot(bot_token)
        seccionais_com_alerta = df_para_alertar['Seccional'].unique()
        ids_gerais = mappings.MAPEAMENTO_ALERTAS_SECCIONAL.get('GERAL', [])

        for seccional in seccionais_com_alerta:
            print(f"\nProcessando alertas para a Seccional: {seccional}...")
            df_da_seccional = df_para_alertar[df_para_alertar['Seccional'] == seccional]
            
            if df_da_seccional.empty:
                continue

            mensagem_seccional = formatar_mensagem_seccional(df_da_seccional, seccional)
            ids_seccional = mappings.MAPEAMENTO_ALERTAS_SECCIONAL.get(seccional.upper(), [])
            ids_para_notificar = set(ids_seccional + ids_gerais)
            
            if not ids_para_notificar:
                print(f"  - [AVISO] Nenhum usuário cadastrado para receber alertas da seccional '{seccional}'.")
                continue
            
            print(f"  - Enviando {len(df_da_seccional)} alerta(s) para {len(ids_para_notificar)} usuário(s)...")
            for user_id in ids_para_notificar:
                try:
                    # O Telegram tem um limite de 4096 caracteres por mensagem.
                    # Se a mensagem for muito longa, ela será dividida.
                    if len(mensagem_seccional) > 4096:
                        for i in range(0, len(mensagem_seccional), 4096):
                            bot.send_message(user_id, mensagem_seccional[i:i+4096], parse_mode='Markdown')
                    else:
                        bot.send_message(user_id, mensagem_seccional, parse_mode='Markdown')
                    
                    print(f"    - Alerta para '{seccional}' enviado com sucesso para o ID: {user_id}")
                except Exception as e:
                    print(f"    - Falha ao enviar para o ID: {user_id}. Erro: {e}")

        print("\n--- Script de alerta finalizado com sucesso! ---")

    except Exception as e:
        print(f"Ocorreu um erro inesperado no script de alertas: {e}")

if __name__ == "__main__":
    enviar_alertas_direcionados()