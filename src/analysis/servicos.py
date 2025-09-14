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


def buscar_ordem_servico(df: pd.DataFrame, numero_os: str) -> str:
    """
    Busca por uma Ordem de Serviço específica no DataFrame e retorna uma
    string formatada com seus detalhes.
    """
    if not numero_os:
        return "Por favor, forneça um número de Ordem de Serviço para a busca."

    termo_busca = str(numero_os).strip()
    coluna_busca = df['Ordem de Serviço'].astype(str).str.strip()
    resultado = df[coluna_busca == termo_busca]

    if resultado.empty:
        return f"❌ Nenhuma Ordem de Serviço encontrada com o número: '{termo_busca}'"
    if len(resultado) > 1:
        return f"⚠️ Alerta: Encontradas {len(resultado)} Ordens de Serviço com o número '{termo_busca}'."

    servico = resultado.iloc[0]
    data_limite_formatada = servico['Data Limite'].strftime('%d/%m/%Y %H:%M') if pd.notna(servico['Data Limite']) else 'N/A'

    resposta = f"✅ *OS Encontrada: `{servico['Ordem de Serviço']}`*\n\n"
    resposta += "*Serviço:*\n"
    resposta += f"- *Tipo:* {servico['Tipo de Atividade']}\n"
    resposta += f"- *Status:* {servico['Status da Atividade']}\n"
    resposta += f"- *Processo:* {servico['Processo']}\n\n"
    resposta += "*Localização:*\n"
    resposta += f"- *Cidade:* {servico['Cidade']}\n"
    resposta += f"- *Seccional:* {servico['Seccional']}\n"
    resposta += f"- *Recurso:* {servico['Recurso']}\n\n"
    resposta += "*Prazos:*\n"
    resposta += f"- *Data Limite:* {data_limite_formatada}\n"
    return resposta


# --- Bloco para Teste Independente ---
if __name__ == '__main__':
    # Este bloco pode ser usado para testes manuais, se necessário.
    print("Este arquivo contém funções de análise e não deve ser executado diretamente.")
    print("Execute os scripts de teste em 'produtividade.py' ou 'alerta_vencimentos.py'.")
    pass
