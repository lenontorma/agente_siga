import pandas as pd
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import sys
import folium

# --- Bloco de Inicialização para Execução Autônoma ---
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    if 'sys' in locals(): del sys

# Importa o módulo de serviços para reutilizar a lógica de alertas
from analysis import servicos 
from analysis import mappings
from analysis.utils import gerar_html_base, categorizar_status

def gerar_resumo_produtividade(df: pd.DataFrame, seccional: Optional[str] = None, processo: Optional[str] = None) -> str:
    """Filtra e gera um resumo simples de produtividade por status para o bot."""
    atividades_para_excluir = ["Intervalo para almoço", "Indisponibilidade"]
    df_filtrado = df[~df['Tipo de Atividade'].isin(atividades_para_excluir)].copy()
    
    filtros_aplicados = []
    if seccional:
        df_filtrado = df_filtrado[df_filtrado['Seccional'].str.strip().str.upper() == seccional.strip().upper()]
        filtros_aplicados.append(f"Seccional = '{seccional}'")
    if processo:
        df_filtrado = df_filtrado[df_filtrado['Processo'].str.strip().str.upper() == processo.strip().upper()]
        filtros_aplicados.append(f"Processo = '{processo}'")
    if df_filtrado.empty:
        return f"Nenhuma atividade produtiva encontrada para os filtros: {', '.join(filtros_aplicados)}." if filtros_aplicados else "Nenhuma atividade produtiva encontrada."
    
    contagem_status = df_filtrado['Status da Atividade'].value_counts()
    total_atividades = len(df_filtrado)
    titulo_filtro = f"para filtros: {', '.join(filtros_aplicados)}" if filtros_aplicados else "geral"
    resposta = f"📊 *Resumo de Produtividade ({titulo_filtro})*\n\n"
    resposta += f"Total de Atividades: *{total_atividades}*\n-----------------------------------\n"
    for status, contagem in contagem_status.items():
        percentual = (contagem / total_atividades) * 100
        resposta += f"- *{status}:* {contagem} ({percentual:.2f}%)\n"
    return resposta


def gerar_relatorio_principal_html(df: pd.DataFrame,
                                   seccional: Optional[str] = None,
                                   processo: Optional[str] = None) -> str:
    """Gera o HTML para a página principal com o resumo e os links para os detalhes."""
    print(f"\nGerando relatório INTERATIVO com filtros: Seccional='{seccional or 'Todas'}', Processo='{processo or 'Todos'}'...")

    df_filtrado = df.copy()
    if seccional:
        df_filtrado = df_filtrado[df_filtrado['Seccional'].str.strip().str.upper() == seccional.strip().upper()]
    if processo:
        df_filtrado = df_filtrado[df_filtrado['Processo'].str.strip().str.upper() == processo.strip().upper()]

    df_equipes = df_filtrado[df_filtrado['Recurso'].str.startswith('RS-', na=False)].copy()
    atividades_para_excluir = ["Intervalo para almoço", "Indisponibilidade"]
    df_produtivo = df_equipes[~df_equipes['Tipo de Atividade'].isin(atividades_para_excluir)].copy()
    df_produtivo = df_produtivo[df_produtivo['Processo'] != 'CORTE MOTO']
    
    if df_produtivo.empty:
        return gerar_html_base("Relatório de Produtividade", "<h1>Relatório de Produtividade</h1><p>Nenhuma atividade produtiva encontrada para os filtros aplicados.</p>")
        
    df_categorizado = categorizar_status(df_produtivo)

    if df_categorizado.empty:
        return gerar_html_base("Relatório de Produtividade", "<h1>Relatório de Produtividade</h1><p>Nenhuma atividade com status relevante encontrada.</p>")

    relatorio = df_categorizado.groupby(['Processo', 'Recurso'])['categoria_status'].value_counts().unstack(fill_value=0)
    for cat in ['Concluído', 'Não Concluído', 'Pendentes', 'Cancelado']:
        if cat not in relatorio.columns: relatorio[cat] = 0
    relatorio['Total'] = relatorio['Concluído'] + relatorio['Não Concluído']
    ordem_colunas = ['Concluído', 'Não Concluído', 'Total', 'Pendentes', 'Cancelado']
    relatorio = relatorio[ordem_colunas]
    relatorio = relatorio.sort_values(by=['Processo', 'Total'], ascending=[True, False])
    relatorio = relatorio.reset_index()

    def criar_link(recurso): return f'<a href="reports/{recurso}.html">{recurso}</a>'
    def formatar_celula_total(valor): return f'<span class="total-column">{valor}</span>'
    
    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo"); agora = datetime.now(fuso_horario_brasil)
    tabela_principal_html = relatorio.to_html(
        index=False, escape=False, classes='table', border=1,
        formatters={'Recurso': criar_link, 'Total': formatar_celula_total}
    )
    filtros_texto = f"Filtros Aplicados: Seccional='{seccional or 'Todas'}', Processo='{processo or 'Todos'}'"
    conteudo = f"<h2>Relatório de Produtividade por Equipe</h2><h4>{filtros_texto}</h4><h4>Gerado em: {agora.strftime('%d/%m/%Y %H:%M:%S')}</h4>{tabela_principal_html}"
    return gerar_html_base("Relatório de Produtividade", conteudo)


def gerar_relatorio_detalhado_equipe_html(df: pd.DataFrame, nome_equipe: str) -> str:
    """Gera o HTML para a página de detalhes de uma única equipe."""
    df_equipe = df[df['Recurso'] == nome_equipe].copy()
    atividades_para_excluir = ["Intervalo para almoço", "Indisponibilidade"]
    df_produtivo = df_equipe[~df_equipe['Tipo de Atividade'].isin(atividades_para_excluir)].copy()
    df_categorizado = categorizar_status(df_produtivo)
    if df_categorizado.empty:
        return gerar_html_base(f"Detalhes - {nome_equipe}", f"<h2>Detalhes da Equipe: {nome_equipe}</h2><p>Nenhuma atividade produtiva com status relevante encontrada.</p>")
    detalhe = df_categorizado.groupby(['Tipo de Atividade'])['categoria_status'].value_counts().unstack(fill_value=0)
    for cat in ['Concluído', 'Não Concluído', 'Pendentes', 'Cancelado']:
        if cat not in detalhe.columns: detalhe[cat] = 0
    detalhe['Total'] = detalhe['Concluído'] + detalhe['Não Concluído']
    ordem_colunas = ['Concluído', 'Não Concluído', 'Total', 'Pendentes', 'Cancelado']
    detalhe = detalhe[ordem_colunas]
    detalhe = detalhe.reset_index()
    def formatar_celula_total(valor): return f'<span class="total-column">{valor}</span>'
    tabela_detalhes_html = detalhe.to_html(index=False, escape=False, classes='table', border=1, formatters={'Total': formatar_celula_total})
    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo"); agora = datetime.now(fuso_horario_brasil)
    conteudo = f"""
        <h2>Detalhes da Equipe: {nome_equipe}</h2>
        <h4>Gerado em: {agora.strftime('%d/%m/%Y %H:%M:%S')}</h4>
        <a href="../relatorio_produtividade.html" class="voltar-btn">&lt; Voltar para o Relatório Principal</a>
        <h3>Contagem por Tipo de Atividade</h3>
        {tabela_detalhes_html}
    """
    return gerar_html_base(f"Detalhes - {nome_equipe}", conteudo)


def gerar_relatorio_gerencial_html(df: pd.DataFrame) -> str:
    """Gera um relatório gerencial completo em HTML com múltiplas visões macro."""
    print("\nGerando relatório gerencial completo em HTML...")
    atividades_para_excluir = ["Intervalo para almoço", "Indisponibilidade"]
    df_produtivo = df[~df['Tipo de Atividade'].isin(atividades_para_excluir)].copy()
    contagem_status = df_produtivo['Status da Atividade'].value_counts().reset_index()
    contagem_status.columns = ['Status', 'Quantidade']
    total_atividades = contagem_status['Quantidade'].sum()
    contagem_status['Percentual (%)'] = ((contagem_status['Quantidade'] / total_atividades) * 100).round(2)
    df_categorizado_geral = categorizar_status(df_produtivo) 
    resumo_seccional = pd.pivot_table(df_categorizado_geral, index='Seccional', columns='categoria_status', aggfunc='size', fill_value=0)
    resumo_processo = pd.pivot_table(df_categorizado_geral[df_categorizado_geral['Processo']!=''], index='Processo', columns='categoria_status', aggfunc='size', fill_value=0)
    alertas = servicos.classificar_os_para_alerta(df)
    resumo_alertas_data = {
        'Tipo de Alerta': ['Vencidas (Ação Imediata)', 'Vencendo Ainda Hoje', 'Vencendo Amanhã (até 08h)'],
        'Quantidade': [len(alertas['vencidas']), len(alertas['vencendo_hoje']), len(alertas['vencendo_amanha'])]
    }
    df_alertas = pd.DataFrame(resumo_alertas_data)
    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo"); agora = datetime.now(fuso_horario_brasil)
    conteudo = f"<h2>Relatório Gerencial Consolidado</h2><h4>Gerado em: {agora.strftime('%d/%m/%Y %H:%M:%S')}</h4>"
    conteudo += "<h3>📊 Visão Geral de Status (Atividades Produtivas)</h3>" + contagem_status.to_html(index=False, classes='table', border=1)
    conteudo += "<h3>🏢 Resumo por Seccional</h3>" + resumo_seccional.to_html(classes='table', border=1)
    conteudo += "<h3>⚙️ Resumo por Processo</h3>" + resumo_processo.to_html(classes='table', border=1)
    conteudo += "<h3>🚨 Situação dos Alertas de Vencimento (Anexo IV)</h3>" + df_alertas.to_html(index=False, classes='table', border=1)
    return gerar_html_base("Relatório Gerencial", conteudo)


## --- FUNÇÕES PARA O DRILL-DOWN POR EQUIPE (RESTAURADAS) --- ##

def obter_equipes_por_filtro(df: pd.DataFrame, seccional: str, processo: Optional[str] = None) -> list:
    """
    Retorna uma lista de equipes (Recursos) únicos com base nos filtros de
    seccional DA EQUIPE e, opcionalmente, de processo.
    """
    df_filtrado = df.copy()
    
    df_filtrado = df_filtrado[df_filtrado['Seccional_Equipe'].str.strip().str.upper() == seccional.strip().upper()]
    
    if processo:
        df_filtrado = df_filtrado[df_filtrado['Processo'].str.strip().str.upper() == processo.strip().upper()]
    
    df_filtrado = df_filtrado[df_filtrado['Recurso'].str.startswith('RS-', na=False)]

    if df_filtrado.empty:
        return []

    return sorted(df_filtrado['Recurso'].unique())


def gerar_mapa_por_equipe_html(df: pd.DataFrame, nome_equipe: str) -> Optional[str]:
    """
    Gera um mapa HTML interativo para uma equipe específica, com pinos coloridos
    de acordo com o status da atividade.
    """
    print(f"\nGerando mapa de atividades para a equipe: {nome_equipe}...")

    # 1. FILTRAGEM DOS DADOS
    df_equipe = df[df['Recurso'] == nome_equipe].copy()
    
    # Remove linhas onde a latitude ou longitude são nulas ou inválidas
    df_equipe.dropna(subset=['Latitude', 'Longitude'], inplace=True)
    df_equipe = df_equipe[pd.to_numeric(df_equipe['Latitude'], errors='coerce').notna()]
    df_equipe = df_equipe[pd.to_numeric(df_equipe['Longitude'], errors='coerce').notna()]
    df_equipe['Latitude'] = df_equipe['Latitude'].astype(float)
    df_equipe['Longitude'] = df_equipe['Longitude'].astype(float)

    if df_equipe.empty:
        print("  - Nenhuma atividade com coordenadas válidas encontrada para esta equipe.")
        return None # Retorna None se não houver dados para mapear

    print(f"  - {len(df_equipe)} atividades com coordenadas válidas encontradas.")

    # 2. CRIAÇÃO DO MAPA
    mapa_centro = [df_equipe['Latitude'].mean(), df_equipe['Longitude'].mean()]
    mapa = folium.Map(location=mapa_centro, zoom_start=10)

    # 3. ADIÇÃO DOS MARCADORES COLORIDOS
    for _, atividade in df_equipe.iterrows():
        status = str(atividade['Status da Atividade']).lower().strip()
        # Pega a cor do nosso mapeamento, ou a cor padrão se o status não for encontrado
        cor_pin = mappings.MAPEAMENTO_CORES_STATUS.get(status, mappings.MAPEAMENTO_CORES_STATUS['default'])
        
        popup_html = f"""
        <b>OS:</b> {atividade['Ordem de Serviço']}<br>
        <b>Tipo:</b> {atividade['Tipo de Atividade']}<br>
        <b>Status:</b> {atividade['Status da Atividade']}
        """
        
        folium.Marker(
            location=[atividade['Latitude'], atividade['Longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{atividade['Tipo de Atividade']} ({atividade['Status da Atividade']})",
            icon=folium.Icon(color=cor_pin) # Define a cor do marcador
        ).add_to(mapa)

    # 4. SALVAR O MAPA EM UMA STRING HTML
    map_html_path = 'mapa_temp.html'
    mapa.save(map_html_path)
    with open(map_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    os.remove(map_html_path)

    print("  ✅ Mapa HTML da equipe gerado com sucesso.")
    return html_content

def gerar_resumo_por_equipe(df: pd.DataFrame, nome_equipe: str) -> str:
    """
    Gera um resumo para uma única equipe, com contagem por tipo de OS,
    detalhando os status de cada tipo.
    """
    df_equipe = df[df['Recurso'] == nome_equipe].copy()
    
    atividades_para_excluir = ["Intervalo para almoço", "Indisponibilidade"]
    df_produtivo = df_equipe[~df_equipe['Tipo de Atividade'].isin(atividades_para_excluir)]

    if df_produtivo.empty:
        return f"Nenhuma atividade produtiva encontrada para a equipe `{nome_equipe}`."

    contagem_detalhada = df_produtivo.groupby(['Tipo de Atividade', 'Status da Atividade']).size().reset_index(name='Quantidade')
    
    # --- ALTERAÇÃO APLICADA AQUI ---
    # Garante que a coluna 'Cidade' só contenha texto antes de ordenar
    cidades_atuacao = ", ".join(sorted(df_produtivo['Cidade'].dropna().astype(str).unique()))
    
    total_atividades = len(df_produtivo)
    info_equipe = df_produtivo.iloc[0]

    resposta = f"👤 *Resumo da Equipe:* `{nome_equipe}`\n"
    resposta += f"*- Seccional da Equipe:* {info_equipe['Seccional_Equipe']}\n"
    resposta += f"*- Processo:* {info_equipe['Processo']}\n\n"
    
    resposta += f"🏙️ *Cidades de Atuação:*\n_{cidades_atuacao}_\n\n"
    
    resposta += f"🛠️ *Resumo de Atividades ({total_atividades} no total):*\n"
    resposta += "-----------------------------------\n"
    
    for tipo_os in contagem_detalhada['Tipo de Atividade'].unique():
        total_tipo_os = contagem_detalhada[contagem_detalhada['Tipo de Atividade'] == tipo_os]['Quantidade'].sum()
        resposta += f"\n- *{tipo_os}* (Total: {total_tipo_os})\n"
        
        status_deste_tipo = contagem_detalhada[contagem_detalhada['Tipo de Atividade'] == tipo_os]
        
        for _, linha in status_deste_tipo.iterrows():
            resposta += f"    • {linha['Status da Atividade']}: {linha['Quantidade']}\n"
            
    return resposta