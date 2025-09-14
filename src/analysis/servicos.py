import pandas as pd
from typing import Dict
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import os

def classificar_os_para_alerta(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Filtra e classifica OS de Anexo IV pendentes em três categorias:
    'vencidas', 'vencendo_hoje', e 'vencendo_amanha'.
    Retorna um dicionário de DataFrames.
    """
    print("\nClassificando OS de Anexo IV para alertas...")
    
    status_pendentes = ['deslocamento', 'pendente', 'iniciado']
    
    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_horario_brasil)
    
    # Remove o fuso horário para comparações diretas com o DataFrame
    agora_naive = agora.replace(tzinfo=None)
    amanha = agora_naive + timedelta(days=1)
    amanha_as_8 = amanha.replace(hour=8, minute=0, second=0, microsecond=0)
    
    df['Data Limite'] = pd.to_datetime(df['Data Limite'])
    
    # Filtro base: Pega todas as OS que são Anexo IV e estão pendentes
    df_base = df[
        (df['Anexo IV'] == 'Sim') &
        (df['Status da Atividade'].str.lower().isin(status_pendentes))
    ].copy()

    # --- LÓGICA DE FILTRO CORRIGIDA ---

    # Categoria 1: VENCIDAS
    # A Data Limite é qualquer data/hora ANTERIOR a agora.
    df_vencidas = df_base[
        df_base['Data Limite'] < agora_naive
    ].sort_values(by='Data Limite')

    # Categoria 2: VENCENDO HOJE
    # A Data Limite é para hoje e ainda está no futuro.
    df_vencendo_hoje = df_base[
        (df_base['Data Limite'] >= agora_naive) &
        (df_base['Data Limite'].dt.date == agora_naive.date())
    ].sort_values(by='Data Limite')
    
    # Categoria 3: VENCENDO AMANHÃ
    # A Data Limite é para amanhã, até as 08:00.
    df_vencendo_amanha = df_base[
        (df_base['Data Limite'].dt.date == amanha.date()) &
        (df_base['Data Limite'] < amanha_as_8)
    ].sort_values(by='Data Limite')

    print(f"  - Encontradas {len(df_vencidas)} OS vencidas (de hoje ou dias anteriores).")
    print(f"  - Encontradas {len(df_vencendo_hoje)} OS vencendo ainda hoje.")
    print(f"  - Encontradas {len(df_vencendo_amanha)} OS vencendo amanhã até as 08:00.")
    
    return {
        "vencidas": df_vencidas, # Nome da chave atualizado
        "vencendo_hoje": df_vencendo_hoje,
        "vencendo_amanha": df_vencendo_amanha
    }


# A função buscar_ordem_servico continua a mesma aqui, se você a tiver neste arquivo.
def buscar_ordem_servico(df: pd.DataFrame, numero_os: str) -> str:
    # ... código existente ...
    pass