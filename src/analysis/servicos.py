import pandas as pd
from typing import Dict, Optional
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import os
import sys
import numpy as np

# --- Bloco de Inicialização para Execução Autônoma ---
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    if 'sys' in locals(): del sys

## --- FUNÇÃO DE GERAÇÃO DE HTML ADICIONADA INTERNAMENTE --- ##
def _gerar_html_base(titulo: str, conteudo_body: str) -> str:
    """
    Função auxiliar interna para criar a estrutura base de um arquivo HTML.
    """
    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>{titulo}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h2, h3, h4 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 15px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        {conteudo_body}
    </body>
    </html>
    """

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
        return _gerar_html_base("Vencimentos Anexo IV", f"<h2>Vencimentos Anexo IV - {seccional or 'Todas'}</h2><p>Nenhuma OS de Anexo IV com vencimento próximo encontrada.</p>")

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
        
    return _gerar_html_base("Vencimentos Anexo IV", conteudo)