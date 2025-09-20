import pandas as pd
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import shutil

# As funções gerar_resumo_produtividade, _gerar_html_base, _categorizar_status
# e gerar_relatorio_detalhado_equipe_html continuam exatamente as mesmas.
# Omiti o código delas aqui para focar na alteração, mas elas devem
# permanecer no seu arquivo como estavam.

def gerar_resumo_produtividade(df: pd.DataFrame, seccional: Optional[str] = None, processo: Optional[str] = None) -> str:
    """Filtra e gera um resumo simples de produtividade por status."""
    df_filtrado = df.copy()
    filtros_aplicados = []
    if seccional:
        df_filtrado = df_filtrado[df_filtrado['Seccional_Equipe'].str.strip().str.upper() == seccional.strip().upper()]
        filtros_aplicados.append(f"Seccional = '{seccional}'")
    if processo:
        df_filtrado = df_filtrado[df_filtrado['Processo'].str.strip().str.upper() == processo.strip().upper()]
        filtros_aplicados.append(f"Processo = '{processo}'")
    if df_filtrado.empty:
        return f"Nenhuma atividade encontrada para os filtros: {', '.join(filtros_aplicados)}." if filtros_aplicados else "Nenhuma atividade encontrada."
    contagem_status = df_filtrado['Status da Atividade'].value_counts()
    total_atividades = len(df_filtrado)
    titulo_filtro = f"para filtros: {', '.join(filtros_aplicados)}" if filtros_aplicados else "geral"
    resposta = f"📊 *Resumo de Produtividade ({titulo_filtro})*\n\n"
    resposta += f"Total de Atividades: *{total_atividades}*\n-----------------------------------\n"
    for status, contagem in contagem_status.items():
        percentual = (contagem / total_atividades) * 100
        resposta += f"- *{status}:* {contagem} ({percentual:.2f}%)\n"
    return resposta


def _gerar_html_base(titulo: str, conteudo_body: str) -> str:
    """Função auxiliar para criar a estrutura base de um arquivo HTML."""
    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>{titulo}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h2, h4 {{ color: #333; }}
            table {{ border-collapse: collapse; width: auto; min-width: 80%; margin-top: 20px; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .total-column {{ background-color: #e0e0e0; font-weight: bold; }}
        </style>
    </head>
    <body>
        {conteudo_body}
    </body>
    </html>
    """

def _categorizar_status(df: pd.DataFrame) -> pd.DataFrame:
    """Função auxiliar para categorizar os status das atividades."""
    df_categorizado = df.copy()
    status_concluido = ['concluído']
    status_nao_concluido = ['não concluído']
    status_pendentes = ['deslocamento', 'pendente', 'iniciado']
    df_lower_status = df_categorizado['Status da Atividade'].str.lower()
    df_categorizado['categoria_status'] = 'Ignorado'
    df_categorizado.loc[df_lower_status.isin(status_concluido), 'categoria_status'] = 'Concluído'
    df_categorizado.loc[df_lower_status.isin(status_nao_concluido), 'categoria_status'] = 'Não Concluído'
    df_categorizado.loc[df_lower_status.isin(status_pendentes), 'categoria_status'] = 'Pendentes'
    categorias_relevantes = ['Concluído', 'Não Concluído', 'Pendentes']
    return df_categorizado[df_categorizado['categoria_status'].isin(categorias_relevantes)]


def gerar_relatorio_detalhado_html(df: pd.DataFrame,
                                   seccional: Optional[str] = None,
                                   processo: Optional[str] = None) -> str:
    """
    Filtra os dados e gera o HTML principal com o resumo, SEM links.
    """

    df_filtrado = df.copy()
    if seccional:
        df_filtrado = df_filtrado[df_filtrado['Seccional_Equipe'].str.strip().str.upper() == seccional.strip().upper()]
    if processo:
        df_filtrado = df_filtrado[df_filtrado['Processo'].str.strip().str.upper() == processo.strip().upper()]

    df_equipes = df_filtrado[df_filtrado['Recurso'].str.startswith('RS-', na=False)].copy()
    atividades_para_excluir = ["Intervalo para almoço", "Indisponibilidade"]
    df_produtivo = df_equipes[~df_equipes['Tipo de Atividade'].isin(atividades_para_excluir)].copy()
    df_produtivo = df_produtivo[df_produtivo['Processo'] != 'CORTE MOTO']
    
    if df_produtivo.empty:
        return _gerar_html_base("Relatório de Produtividade", "<h1>Relatório de Produtividade</h1><p>Nenhuma atividade produtiva encontrada para os filtros aplicados.</p>")
        
    df_categorizado = _categorizar_status(df_produtivo)

    if df_categorizado.empty:
        return _gerar_html_base("Relatório de Produtividade", "<h1>Relatório de Produtividade</h1><p>Nenhuma atividade com status relevante encontrada.</p>")

    relatorio = df_categorizado.groupby(['Processo', 'Recurso'])['categoria_status'].value_counts().unstack(fill_value=0)
    for cat in ['Concluído', 'Não Concluído', 'Pendentes']:
        if cat not in relatorio.columns: relatorio[cat] = 0
    relatorio['Total'] = relatorio['Concluído'] + relatorio['Não Concluído']
    ordem_colunas = ['Concluído', 'Não Concluído', 'Total', 'Pendentes']
    relatorio = relatorio[ordem_colunas]
    relatorio = relatorio.sort_values(by=['Processo', 'Total'], ascending=[True, False])
    relatorio = relatorio.reset_index()

    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo"); agora = datetime.now(fuso_horario_brasil)
    
    # --- ALTERAÇÃO APLICADA AQUI ---
    # Removemos a função 'criar_link' e o argumento 'formatters' para não gerar links.
    # Também removemos a pasta 'reports' já que não haverá mais detalhes.
    tabela_principal_html = relatorio.to_html(
        index=False,
        escape=False,
        classes='table',
        border=1
    )
    
    filtros_texto = f"Filtros Aplicados: Seccional='{seccional or 'Todas'}', Processo='{processo or 'Todos'}'"
    conteudo = f"<h2>Relatório de Produtividade por Equipe</h2><h4>{filtros_texto}</h4><h4>Gerado em: {agora.strftime('%d/%m/%Y %H:%M:%S')}</h4>{tabela_principal_html}"
    return _gerar_html_base("Relatório de Produtividade", conteudo)

## --- NOVAS FUNÇÕES GERENCIAIS ADICIONADAS AQUI --- ##

def gerar_visao_geral_status(df: pd.DataFrame) -> str:
    """Gera um resumo com a contagem total de cada status de atividade."""
    atividades_para_excluir = ["Intervalo para almoço", "Indisponibilidade"]
    df_produtivo = df[~df['Tipo de Atividade'].isin(atividades_para_excluir)]
    if df_produtivo.empty: 
        return "Nenhuma atividade produtiva encontrada."
        
    contagem = df_produtivo['Status da Atividade'].value_counts()
    total = contagem.sum()
    
    resposta = "📊 *Visão Geral de Status (Todas as OS)*\n\n"
    for status, qtd in contagem.items():
        percentual = (qtd / total) * 100
        resposta += f"- *{status}:* {qtd} ({percentual:.2f}%)\n"
    resposta += f"\n*Total de Atividades Produtivas:* {total}"
    return resposta

def gerar_resumo_por_seccional(df: pd.DataFrame) -> str:
    """Gera um resumo de atividades pendentes e concluídas por seccional."""
    status_concluidos = ['concluído', 'não concluído']
    status_pendentes = ['deslocamento', 'pendente', 'iniciado']
    
    df_copy = df.copy() # Garante que o dataframe original não seja modificado
    df_copy['categoria_status'] = 'Outros'
    df_lower_status = df_copy['Status da Atividade'].str.lower()
    df_copy.loc[df_lower_status.isin(status_concluidos), 'categoria_status'] = 'Concluídos'
    df_copy.loc[df_lower_status.isin(status_pendentes), 'categoria_status'] = 'Pendentes'
    
    resumo = df_copy.groupby('Seccional_Equipe')['categoria_status'].value_counts().unstack(fill_value=0)
    
    if 'Concluídos' not in resumo.columns: resumo['Concluídos'] = 0
    if 'Pendentes' not in resumo.columns: resumo['Pendentes'] = 0
    
    resumo = resumo[['Concluídos', 'Pendentes']].sort_values(by='Pendentes', ascending=False)
    
    resposta = "🏢 *Resumo por Seccional*\n\n"
    for seccional, dados in resumo.iterrows():
        resposta += f"*{seccional}:*\n"
        resposta += f"  - ✅ Concluídos: {dados['Concluídos']}\n"
        resposta += f"  - ⏳ Pendentes: {dados['Pendentes']}\n\n"
        
    return resposta

def gerar_resumo_por_processo(df: pd.DataFrame) -> str:
    """Gera um resumo de atividades pendentes e concluídas por processo."""
    status_concluidos = ['concluído', 'não concluído']
    status_pendentes = ['deslocamento', 'pendente', 'iniciado']
    
    df_copy = df.copy() # Garante que o dataframe original não seja modificado
    df_copy['categoria_status'] = 'Outros'
    df_lower_status = df_copy['Status da Atividade'].str.lower()
    df_copy.loc[df_lower_status.isin(status_concluidos), 'categoria_status'] = 'Concluídos'
    df_copy.loc[df_lower_status.isin(status_pendentes), 'categoria_status'] = 'Pendentes'
    
    df_filtrado = df_copy[df_copy['Processo'] != '']
    
    resumo = df_filtrado.groupby('Processo')['categoria_status'].value_counts().unstack(fill_value=0)
    
    if 'Concluídos' not in resumo.columns: resumo['Concluídos'] = 0
    if 'Pendentes' not in resumo.columns: resumo['Pendentes'] = 0
    
    resumo = resumo[['Concluídos', 'Pendentes']].sort_values(by='Pendentes', ascending=False)
    
    resposta = "⚙️ *Resumo por Processo*\n\n"
    for processo, dados in resumo.iterrows():
        resposta += f"*{processo}:*\n"
        resposta += f"  - ✅ Concluídos: {dados['Concluídos']}\n"
        resposta += f"  - ⏳ Pendentes: {dados['Pendentes']}\n\n"
        
    return resposta

# --- Bloco para Teste e Geração do relatório principal ---
if __name__ == '__main__':
    print("--- Iniciando geração do relatório de produtividade ---")
    try:
        caminho_script = os.path.abspath(__file__)
        caminho_analysis = os.path.dirname(caminho_script)
        caminho_src = os.path.dirname(caminho_analysis)
        caminho_raiz_projeto = os.path.dirname(caminho_src)
        caminho_data = os.path.join(caminho_raiz_projeto, "Data")
        caminho_dados_excel = os.path.join(caminho_data, "prod_gstc.xlsx")
        
        # --- ALTERAÇÃO APLICADA AQUI ---
        # Não precisamos mais criar ou limpar a pasta 'reports'
        if not os.path.exists(caminho_dados_excel):
            raise FileNotFoundError(f"Arquivo de dados não encontrado em {caminho_dados_excel}")

        df_completo = pd.read_excel(caminho_dados_excel)
        
        for col in ['Data', 'Início', 'Fim', 'Data Limite', 'Data Abertura', 'Data_Extracao']:
            if col in df_completo.columns:
                df_completo[col] = pd.to_datetime(df_completo[col])
        
        print(f"Base de dados carregada com {len(df_completo)} linhas.")
        
        # Gera e salva o relatório principal (agora sem links)
        relatorio_principal_html = gerar_relatorio_detalhado_html(df_completo)
        caminho_saida_principal = os.path.join(caminho_data, "relatorio_produtividade.html")
        with open(caminho_saida_principal, 'w', encoding='utf-8') as f:
            f.write(relatorio_principal_html)
        print(f"\n✅ Relatório principal salvo em: {caminho_saida_principal}")

    except FileNotFoundError as e:
        print(f"\nERRO: {e}")
        print("Certifique-se de que o script de transformação foi executado primeiro.")
    except Exception as e:
        print(f"\nOcorreu um erro durante o teste: {e}")