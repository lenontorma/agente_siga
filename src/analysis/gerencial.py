import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
import os

# Adiciona o 'src' ao path para encontrar os módulos irmãos
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    if 'sys' in locals(): del sys

from analysis import servicos
# Importa as funções auxiliares do novo arquivo de utilitários
from analysis.utils import gerar_html_base, categorizar_status

def gerar_relatorio_gerencial_html(df: pd.DataFrame) -> str:
    """Gera um relatório gerencial completo em HTML com múltiplas visões macro."""
    print("\nGerando relatório gerencial completo em HTML...")

    atividades_para_excluir = ["Intervalo para almoço", "Indisponibilidade"]
    df_produtivo = df[~df['Tipo de Atividade'].isin(atividades_para_excluir)].copy()
    
    # 1. Visão Geral de Status
    contagem_status = df_produtivo['Status da Atividade'].value_counts().reset_index()
    contagem_status.columns = ['Status', 'Quantidade']
    total_atividades = contagem_status['Quantidade'].sum()
    contagem_status['Percentual (%)'] = ((contagem_status['Quantidade'] / total_atividades) * 100).round(2)
    
    # 2. Resumo por Seccional e Processo
    df_categorizado_geral = categorizar_status(df_produtivo) 
    resumo_seccional = pd.pivot_table(df_categorizado_geral, index='Seccional', columns='categoria_status', aggfunc='size', fill_value=0)
    resumo_processo = pd.pivot_table(df_categorizado_geral[df_categorizado_geral['Processo']!=''], index='Processo', columns='categoria_status', aggfunc='size', fill_value=0)

    # 3. Resumo de Alertas
    alertas = servicos.classificar_os_para_alerta(df)
    resumo_alertas_data = {
        'Tipo de Alerta': ['Vencidas (Ação Imediata)', 'Vencendo Ainda Hoje', 'Vencendo Amanhã (até 08h)'],
        'Quantidade': [len(alertas['vencidas']), len(alertas['vencendo_hoje']), len(alertas['vencendo_amanha'])]
    }
    df_alertas = pd.DataFrame(resumo_alertas_data)

    # 4. Montagem do HTML
    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_horario_brasil)
    
    conteudo = f"<h2>Relatório Gerencial Consolidado</h2><h4>Gerado em: {agora.strftime('%d/%m/%Y %H:%M:%S')}</h4>"
    conteudo += "<h3>📊 Visão Geral de Status (Atividades Produtivas)</h3>"
    conteudo += contagem_status.to_html(index=False, classes='table', border=1)
    conteudo += "<h3>🏢 Resumo por Seccional</h3>"
    conteudo += resumo_seccional.to_html(classes='table', border=1)
    conteudo += "<h3>⚙️ Resumo por Processo</h3>"
    conteudo += resumo_processo.to_html(classes='table', border=1)
    conteudo += "<h3>🚨 Situação dos Alertas de Vencimento (Anexo IV)</h3>"
    conteudo += df_alertas.to_html(index=False, classes='table', border=1)

    return gerar_html_base("Relatório Gerencial", conteudo)