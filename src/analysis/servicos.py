import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import sys

# --- Bloco de Inicialização para Execução Autônoma ---
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    if 'sys' in locals(): del sys

from analysis.utils import gerar_html_base

def classificar_os_para_alerta(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    # ... (código existente, sem alterações)
    print("\nClassificando OS de Anexo IV para alertas...")
    status_pendentes = ['deslocamento', 'pendente', 'iniciado']
    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_horario_brasil)
    agora_naive = agora.replace(tzinfo=None)
    amanha = agora_naive + timedelta(days=1)
    amanha_as_8 = amanha.replace(hour=8, minute=0, second=0, microsecond=0)
    df['Data Limite'] = pd.to_datetime(df['Data Limite'])
    df_base = df[(df['Anexo IV'] == 'Sim') & (df['Status da Atividade'].str.lower().isin(status_pendentes))].copy()
    df_vencidas = df_base[df_base['Data Limite'] < agora_naive].sort_values(by='Data Limite')
    df_vencendo_hoje = df_base[(df_base['Data Limite'] >= agora_naive) & (df_base['Data Limite'].dt.date == agora_naive.date())].sort_values(by='Data Limite')
    df_vencendo_amanha = df_base[(df_base['Data Limite'].dt.date == amanha.date()) & (df_base['Data Limite'] <= amanha_as_8)].sort_values(by='Data Limite')
    print(f"  - Encontradas {len(df_vencidas)} OS vencidas.")
    print(f"  - Encontradas {len(df_vencendo_hoje)} OS vencendo ainda hoje.")
    print(f"  - Encontradas {len(df_vencendo_amanha)} OS vencendo amanhã até as 08:00.")
    return {"vencidas": df_vencidas, "vencendo_hoje": df_vencendo_hoje, "vencendo_amanha": df_vencendo_amanha}


def gerar_relatorio_vencimentos_anexo_iv(df: pd.DataFrame, seccional: Optional[str] = None) -> str:
    # ... (código existente, sem alterações)
    pass


def gerar_resumo_vencimentos_texto(df: pd.DataFrame, seccional: str) -> str:
    """
    Filtra por Anexo IV e Seccional, classifica os vencimentos e retorna um resumo em TEXTO.
    """
    print(f"\nGerando resumo de vencimentos em TEXTO para a seccional: '{seccional}'...")
    
    df_filtrado = df[df['Seccional'].str.strip().str.upper() == seccional.strip().upper()].copy()
    
    alertas = classificar_os_para_alerta(df_filtrado)
    df_vencidas = alertas["vencidas"]
    df_hoje = alertas["vencendo_hoje"]
    df_amanha = alertas["vencendo_amanha"]
    
    total = len(df_vencidas) + len(df_hoje) + len(df_amanha)
    if total == 0:
        return f"✅ *Vencimentos Anexo IV - {seccional.upper()}*\n\nNenhuma OS com vencimento próximo encontrada."

    resposta = f"🚨 *Vencimentos Anexo IV - {seccional.upper()}* 🚨\n"
    
    # Função auxiliar interna para não repetir código
    def formatar_bloco(df_bloco):
        texto = ""
        for _, os in df_bloco.iterrows():
            texto += f"  - `{os['Instalação']}` (Equipe: {os['Recurso']})\n"
            texto += f"    - *Tipo:* {os['Tipo de Atividade']}\n"
            texto += f"    - *Status:* {os['Status da Atividade']}\n"
            texto += f"    - *Cidade:* {os['Cidade']}\n"
        return texto

    if not df_vencidas.empty:
        resposta += "\n🆘 *VENCIDAS* 🆘\n"
        resposta += formatar_bloco(df_vencidas)
            
    if not df_hoje.empty:
        resposta += "\n⚠️ *Vencendo AINDA HOJE* ⚠️\n"
        resposta += formatar_bloco(df_hoje)

    if not df_amanha.empty:
        resposta += "\n🗓️ *Vencendo AMANHÃ (até 08:00)* 🗓️\n"
        resposta += formatar_bloco(df_amanha)
            
    # --- NOVO BLOCO DE TOTALIZAÇÃO ---
    resposta += "\n-----------------------------------\n"
    resposta += f"*Resumo Total para {seccional.upper()}:*\n"
    resposta += f"  - Vencidas: *{len(df_vencidas)}*\n"
    resposta += f"  - Vencendo Hoje: *{len(df_hoje)}*\n"
    resposta += f"  - Vencendo Amanhã: *{len(df_amanha)}*\n"
    resposta += f"  - *TOTAL EM ALERTA:* *{total}*"
    
    return resposta