import pandas as pd
from typing import Dict, Optional
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import os
import sys
import numpy as np
import folium
from math import radians, sin, cos, sqrt, asin

# --- Bloco de Inicialização para Execução Autônoma ---
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    if 'sys' in locals(): del sys

# Importa a função auxiliar do nosso módulo de utilitários
from analysis.utils import gerar_html_base
from analysis import mappings

def classificar_os_para_alerta(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Filtra e classifica OS de Anexo IV pendentes em três categorias:
    'vencidas', 'vencendo_hoje', e 'vencendo_amanha'.
    """
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
    
    return {
        "vencidas": df_vencidas,
        "vencendo_hoje": df_vencendo_hoje,
        "vencendo_amanha": df_vencendo_amanha
    }


def buscar_ordem_servico(df: pd.DataFrame, numero_os: str) -> str:
    """Busca por uma Ordem de Serviço específica e retorna seus detalhes."""
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


def gerar_relatorio_vencimentos_anexo_iv(df: pd.DataFrame, seccional: Optional[str] = None) -> str:
    """
    Filtra por Anexo IV e Seccional, classifica os vencimentos e retorna um relatório HTML limpo.
    """
    print(f"\nGerando relatório de vencimentos Anexo IV para a seccional: '{seccional or 'Todas'}'...")
    
    df_filtrado = df.copy()
    
    if seccional:
        df_filtrado = df_filtrado[df_filtrado['Seccional'].str.strip().str.upper() == seccional.strip().upper()]

    alertas_classificados = classificar_os_para_alerta(df_filtrado)
    
    df_vencidas = alertas_classificados["vencidas"]
    df_hoje = alertas_classificados["vencendo_hoje"]
    df_amanha = alertas_classificados["vencendo_amanha"]

    if df_vencidas.empty and df_hoje.empty and df_amanha.empty:
        return gerar_html_base("Vencimentos Anexo IV", f"<h2>Vencimentos Anexo IV - {seccional or 'Todas'}</h2><p>Nenhuma OS de Anexo IV com vencimento próximo encontrada.</p>")

    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_horario_brasil)

    conteudo = f"<h2>Relatório de Vencimentos - Anexo IV</h2>"
    conteudo += f"<h4>Seccional: {seccional or 'Todas'}</h4>"
    conteudo += f"<h4>Gerado em: {agora.strftime('%d/%m/%Y %H:%M:%S')}</h4>"

    colunas_importantes = [
        'Instalação', 'Tipo de Atividade', 'Status da Atividade', 'Data Limite', 'Recurso', 'Cidade'
    ]
    formatters = {'Data Limite': lambda x: x.strftime('%d/%m/%Y %H:%M')}

    if not df_vencidas.empty:
        conteudo += "<h3>🆘 VENCIDAS</h3>"
        conteudo += df_vencidas[colunas_importantes].to_html(index=False, classes='table', border=1, formatters=formatters)

    if not df_hoje.empty:
        conteudo += "<h3>⚠️ Vencendo AINDA HOJE</h3>"
        conteudo += df_hoje[colunas_importantes].to_html(index=False, classes='table', border=1, formatters=formatters)

    if not df_amanha.empty:
        conteudo += "<h3>🗓️ Vencendo AMANHÃ (até 08:00)</h3>"
        conteudo += df_amanha[colunas_importantes].to_html(index=False, classes='table', border=1, formatters=formatters)
        
    return gerar_html_base("Vencimentos Anexo IV", conteudo)


def gerar_resumo_alertas(df: pd.DataFrame) -> str:
    """
    Reutiliza a lógica de alertas para fornecer uma contagem rápida e
    formatada para o menu gerencial.
    """
    alertas_classificados = classificar_os_para_alerta(df)
    
    df_vencidas = alertas_classificados["vencidas"]
    df_hoje = alertas_classificados["vencendo_hoje"]
    df_amanha = alertas_classificados["vencendo_amanha"]

    total = len(df_vencidas) + len(df_hoje) + len(df_amanha)
    
    if total == 0:
        return "✅ *Situação dos Alertas de Vencimento*\n\nNenhuma OS de Anexo IV com vencimento próximo."

    resposta = "🚨 *Situação dos Alertas de Vencimento (Anexo IV)*\n\n"
    resposta += f"🆘 *Vencidas:* {len(df_vencidas)}\n"
    resposta += f"⚠️ *Vencendo Hoje:* {len(df_hoje)}\n"
    resposta += f"🗓️ *Vencendo Amanhã (até 08h):* {len(df_amanha)}\n"
    resposta += f"\n*Total de OS em Alerta:* {total}"
    
    return resposta


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
            
    resposta += "\n-----------------------------------\n"
    resposta += f"*Resumo Total para {seccional.upper()}:*\n"
    resposta += f"  - Vencidas: *{len(df_vencidas)}*\n"
    resposta += f"  - Vencendo Hoje: *{len(df_hoje)}*\n"
    resposta += f"  - Vencendo Amanhã: *{len(df_amanha)}*\n"
    resposta += f"  - *TOTAL EM ALERTA:* *{total}*"
    
    return resposta


def _haversine(lat1, lon1, lat2, lon2):
    """Calcula a distância em km entre dois pontos geográficos."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def gerar_mapa_proximidade(df: pd.DataFrame, id_referencia: str) -> str:
    """
    Gera um mapa HTML mostrando as 3 equipes/serviços pendentes mais próximos
    de uma OS ou Instalação de referência.
    """
    print(f"\nGerando mapa de proximidade para a referência: '{id_referencia}'...")
    
    # --- ALTERAÇÃO APLICADA AQUI ---
    
    # 1. Limpa a entrada do usuário
    id_referencia_limpo = str(id_referencia).strip()

    # 2. Normaliza as colunas de busca do DataFrame para garantir a correspondência
    # Remove o '.0' de números que foram convertidos para float
    df['Instalação_norm'] = df['Instalação'].astype(str).str.split('.').str[0]
    df['OS_norm'] = df['Ordem de Serviço'].astype(str).str.strip()

    # 3. Faz a busca usando as colunas normalizadas
    df_ref = df[
        (df['OS_norm'] == id_referencia_limpo) |
        (df['Instalação_norm'] == id_referencia_limpo)
    ].copy()

    # --- Fim da Alteração ---

    if df_ref.empty:
        return f"Referência '{id_referencia}' não encontrada na base de dados."
    
    servico_ref = df_ref.iloc[0]
    lat_ref = pd.to_numeric(servico_ref['Latitude'], errors='coerce')
    lon_ref = pd.to_numeric(servico_ref['Longitude'], errors='coerce')

    if pd.isna(lat_ref) or pd.isna(lon_ref):
        return f"A referência '{id_referencia}' não possui coordenadas geográficas válidas."

    status_pendentes = ['deslocamento', 'pendente', 'iniciado']
    df_candidatos = df[
        (df['Status da Atividade'].str.lower().isin(status_pendentes)) &
        (df['Ordem de Serviço'] != servico_ref['Ordem de Serviço'])
    ].copy()
    
    df_candidatos['Latitude'] = pd.to_numeric(df_candidatos['Latitude'], errors='coerce')
    df_candidatos['Longitude'] = pd.to_numeric(df_candidatos['Longitude'], errors='coerce')
    df_candidatos.dropna(subset=['Latitude', 'Longitude'], inplace=True)

    if df_candidatos.empty:
        return f"Nenhum outro serviço pendente com coordenadas encontrado para comparação."

    df_candidatos['Distancia_km'] = df_candidatos.apply(
        lambda row: _haversine(lat_ref, lon_ref, row['Latitude'], row['Longitude']),
        axis=1
    )
    
    df_proximos = df_candidatos.sort_values(by='Distancia_km').head(3)

    mapa = folium.Map(location=[lat_ref, lon_ref], zoom_start=12)
    
    popup_ref_html = f"""
    <b>Referência (OS):</b> {servico_ref['Ordem de Serviço']}<br>
    <b>Equipe:</b> {servico_ref['Recurso']}<br>
    <b>Tipo:</b> {servico_ref['Tipo de Atividade']}<br>
    <b>Status:</b> {servico_ref['Status da Atividade']}
    """
    folium.Marker(
        location=[lat_ref, lon_ref],
        popup=folium.Popup(popup_ref_html, max_width=300),
        tooltip="SERVIÇO DE REFERÊNCIA",
        icon=folium.Icon(color='blue', icon='star')
    ).add_to(mapa)

    for _, os_proxima in df_proximos.iterrows():
        distancia = round(os_proxima['Distancia_km'], 2)
        status = str(os_proxima['Status da Atividade']).lower().strip()
        cor_pin = mappings.MAPEAMENTO_CORES_STATUS.get(status, mappings.MAPEAMENTO_CORES_STATUS['default'])
        
        popup_proximo_html = f"""
        <b>Equipe:</b> {os_proxima['Recurso']}<br>
        <b>OS:</b> {os_proxima['Ordem de Serviço']}<br>
        <b>Tipo:</b> {os_proxima['Tipo de Atividade']}<br>
        <b>Status:</b> {os_proxima['Status da Atividade']}<br>
        <b>Distância:</b> {distancia} km
        """
        folium.Marker(
            location=[os_proxima['Latitude'], os_proxima['Longitude']],
            popup=folium.Popup(popup_proximo_html, max_width=300),
            tooltip=f"{os_proxima['Recurso']} ({distancia} km)",
            icon=folium.Icon(color=cor_pin, icon='info-sign')
        ).add_to(mapa)
        
        folium.PolyLine(locations=[[lat_ref, lon_ref], [os_proxima['Latitude'], os_proxima['Longitude']]], color='gray', weight=1.5, opacity=0.8).add_to(mapa)
    
    map_html_path = 'mapa_proximidade_temp.html'
    mapa.save(map_html_path)
    with open(map_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    os.remove(map_html_path)
    
    return html_content