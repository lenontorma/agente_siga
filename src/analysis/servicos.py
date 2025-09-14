import pandas as pd
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

def encontrar_os_proximas_vencimento(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra o DataFrame para encontrar OS de Anexo IV que estão pendentes e que
    vencem HOJE (qualquer horário) ou AMANHÃ (até as 08:00).
    """
    print("\n--- INICIANDO DIAGNÓSTICO DE BUSCA POR OS PRÓXIMAS DO VENCIMENTO ---")
    
    # Define os status que consideramos como 'em andamento'
    status_pendentes = ['deslocamento', 'pendente', 'iniciado']
    
    # --- LÓGICA DE DATA E HORA PRECISA ---
    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
    
    agora = datetime.now(fuso_horario_brasil)
    amanha = agora + timedelta(days=1)
    amanha_as_8 = amanha.replace(hour=8, minute=0, second=0, microsecond=0)
    
    print(f"1. Referências de tempo (Fuso Horário: {fuso_horario_brasil}):")
    print(f"   - Agora: {agora.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"   - Limite do alerta: {amanha_as_8.strftime('%d/%m/%Y %H:%M:%S')}")

    # Garante que a coluna 'Data Limite' seja do tipo datetime (timezone-naive)
    df['Data Limite'] = pd.to_datetime(df['Data Limite'])
    
    # --- FILTROS INICIAIS (ANTES DA DATA) ---
    df_filtrado_inicial = df[
        (df['Anexo IV'] == 'Sim') &
        (df['Status da Atividade'].str.lower().isin(status_pendentes))
    ].copy()
    
    print(f"\n2. Resultado dos filtros iniciais (Anexo IV='Sim' e Status Pendente):")
    print(f"   - {len(df_filtrado_inicial)} OS encontradas ANTES do filtro de data.")

    if df_filtrado_inicial.empty:
        print("   - Nenhuma OS passou nos filtros iniciais. Verifique os status e a marcação 'Anexo IV'.")
        return df_filtrado_inicial

    print("   - Amostra das 'Datas Limite' encontradas (antes do filtro final):")
    print(df_filtrado_inicial[['Ordem de Serviço', 'Data Limite']].head().to_string(index=False))
    
    # --- FILTRO FINAL DE DATA ---
    # Converte os limites de tempo para timezone-naive para comparar com a coluna do DataFrame
    agora_naive = agora.replace(tzinfo=None)
    amanha_as_8_naive = amanha_as_8.replace(tzinfo=None)

    df_filtrado_final = df_filtrado_inicial[
        (df_filtrado_inicial['Data Limite'] >= agora_naive) &
        (df_filtrado_inicial['Data Limite'] <= amanha_as_8_naive)
    ].copy()

    print(f"\n3. Resultado do filtro final de data:")
    print(f"   - {len(df_filtrado_final)} OS encontradas COM VENCIMENTO até amanhã às 08:00.")
    print("--- FIM DO DIAGNÓSTICO ---\n")
    
    return df_filtrado_final.sort_values(by='Data Limite')


# A função buscar_ordem_servico continua a mesma aqui, se você a tiver neste arquivo.
def buscar_ordem_servico(df: pd.DataFrame, numero_os: str) -> str:
    # ... código existente ...
    pass