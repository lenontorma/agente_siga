import pandas as pd
from typing import Dict, Optional
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import os
import numpy as np # Garante que o numpy está importado

def classificar_os_para_alerta(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Classifica OS de Anexo IV pendentes em categorias de vencimento."""
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
    return {"vencidas": df_vencidas, "vencendo_hoje": df_vencendo_hoje, "vencendo_amanha": df_vencendo_amanha}


def encontrar_os_vencendo_em_x_horas(df: pd.DataFrame, horas: int = 8) -> pd.DataFrame:
    """
    Filtra o DataFrame para encontrar OS de Anexo IV pendentes que vencem
    dentro da janela de 'horas' especificada a partir de agora, incluindo as já vencidas.
    """
    print(f"\nBuscando por OS de Anexo IV vencendo nas próximas {horas} horas...")
    
    status_pendentes = ['deslocamento', 'pendente', 'iniciado']
    
    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_horario_brasil)
    agora_naive = agora.replace(tzinfo=None)
    
    limite_futuro = agora_naive + timedelta(hours=horas)
    
    df['Data Limite'] = pd.to_datetime(df['Data Limite'])
    
    df_base = df[(df['Anexo IV'] == 'Sim') & (df['Status da Atividade'].str.lower().isin(status_pendentes))].copy()

    df_filtrado = df_base[df_base['Data Limite'] < limite_futuro].copy()
    
    df_filtrado['Alerta_Tipo'] = np.where(
        df_filtrado['Data Limite'] < agora_naive,
        'VENCIDA',
        'PRÓXIMO DO VENCIMENTO'
    )
    
    print(f"  - {len(df_filtrado)} OS encontradas.")
    return df_filtrado.sort_values(by=['Alerta_Tipo', 'Data Limite'])


def buscar_ordem_servico(df: pd.DataFrame, numero_os: str) -> str:
    """Busca por uma Ordem de Serviço específica e retorna seus detalhes."""
    # ... (código existente, sem alterações)
    if not numero_os: return "Por favor, forneça um número de Ordem de Serviço."
    termo_busca = str(numero_os).strip()
    resultado = df[df['Ordem de Serviço'].astype(str).str.strip() == termo_busca]
    if resultado.empty: return f"❌ Nenhuma OS encontrada com o número: '{termo_busca}'"
    if len(resultado) > 1: return f"⚠️ Alerta: Encontradas {len(resultado)} OS com o número '{termo_busca}'."
    servico = resultado.iloc[0]
    data_limite_formatada = servico['Data Limite'].strftime('%d/%m/%Y %H:%M') if pd.notna(servico['Data Limite']) else 'N/A'
    resposta = f"✅ *OS Encontrada: `{servico['Ordem de Serviço']}`*\n\n"
    resposta += f"*Serviço:*\n- *Tipo:* {servico['Tipo de Atividade']}\n- *Status:* {servico['Status da Atividade']}\n- *Processo:* {servico['Processo']}\n\n"
    resposta += f"*Localização:*\n- *Cidade:* {servico['Cidade']}\n- *Seccional:* {servico['Seccional']}\n- *Recurso:* {servico['Recurso']}\n\n"
    resposta += f"*Prazos:*\n- *Data Limite:* {data_limite_formatada}\n"
    return resposta