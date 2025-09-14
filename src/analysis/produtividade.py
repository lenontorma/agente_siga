import pandas as pd
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import shutil

def gerar_resumo_produtividade(df: pd.DataFrame, 
                               seccional: Optional[str] = None, 
                               processo: Optional[str] = None) -> str:
    # ... (Esta função continua a mesma)
    # ... (código oculto para brevidade)
    return "Resumo de Produtividade..." # Implementação completa omitida


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
            th, td {{ border: 1px solid #ddd; padding: 0; text-align: left; vertical-align: middle; }} /* Padding removido para o span preencher */
            th {{ background-color: #f2f2f2; padding: 8px; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            a {{ color: #007bff; text-decoration: none; font-weight: bold; }}
            a:hover {{ text-decoration: underline; }}
            td > span {{ display: block; padding: 8px; }} /* Span preenche a célula */
            .total-cell {{ background-color: #e0e0e0; font-weight: bold; }}
            .voltar-btn {{
                display: inline-block; padding: 10px 15px; margin-bottom: 20px;
                background-color: #007bff; color: white; text-decoration: none;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        {conteudo_body}
    </body>
    </html>
    """

def _categorizar_status(df: pd.DataFrame) -> pd.DataFrame:
    """Função auxiliar para categorizar os status das atividades."""
    # ... (código existente, sem alterações)
    df_categorizado = df.copy()
    status_concluido = ['concluído']
    status_nao_concluido = ['não concluído']
    status_pendentes = ['deslocamento', 'pendente', 'iniciado']
    df_lower_status = df_categorizado['Status da Atividade'].str.lower()
    df_categorizado['categoria_status'] = 'Ignorado'
    df_categorizado.loc[df_lower_status.isin(status_concluido), 'categoria_status'] = 'Concluído'
    df_categorizado.loc[df_lower_status.isin(status_nao_concluido), 'categoria_status'] = 'Não Concluído'
    df_categorizado.loc[df_lower_status.isin(status_pendentes), 'categoria_status'] = 'Pendentes'
    return df_categorizado[df_categorizado['categoria_status'] != 'Ignorado']


def gerar_relatorio_detalhado_equipe_html(df: pd.DataFrame, nome_equipe: str) -> str:
    """Gera o HTML para a página de detalhes de uma única equipe."""
    
    df_equipe = df[df['Recurso'] == nome_equipe].copy()
    df_categorizado = _categorizar_status(df_equipe)

    if df_categorizado.empty:
        return _gerar_html_base(f"Detalhes - {nome_equipe}", f"<h2>Detalhes da Equipe: {nome_equipe}</h2><p>Nenhuma atividade com status relevante encontrada.</p>")

    detalhe = df_categorizado.groupby(['Tipo de Atividade'])['categoria_status'].value_counts().unstack(fill_value=0)
    
    for cat in ['Concluído', 'Não Concluído', 'Pendentes']:
        if cat not in detalhe.columns:
            detalhe[cat] = 0
            
    detalhe['Total'] = detalhe['Concluído'] + detalhe['Não Concluído']
    ordem_colunas = ['Concluído', 'Não Concluído', 'Total', 'Pendentes']
    detalhe = detalhe[ordem_colunas]
    detalhe = detalhe.reset_index()

    # Função de formatação para destacar a célula do Total
    def formatar_celula_total(valor):
        return f'<span class="total-cell">{valor}</span>'

    tabela_detalhes_html = detalhe.to_html(
        index=False,
        escape=False,
        classes='table',
        border=1,
        formatters={'Total': formatar_celula_total} # Aplica o destaque
    )

    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_horario_brasil)
    
    conteudo = f"""
        <h2>Detalhes da Equipe: {nome_equipe}</h2>
        <h4>Gerado em: {agora.strftime('%d/%m/%Y %H:%M:%S')}</h4>
        <a href="../relatorio_produtividade.html" class="voltar-btn">&lt; Voltar para o Relatório Principal</a>
        <h3>Contagem por Tipo de Atividade</h3>
        {tabela_detalhes_html}
    """
    
    return _gerar_html_base(f"Detalhes - {nome_equipe}", conteudo)


def gerar_relatorio_principal_html(df: pd.DataFrame) -> str:
    """Gera o HTML para a página principal com o resumo e os links para os detalhes."""
    print("\nGerando relatório de produtividade principal em formato HTML...")

    df_equipes = df[df['Recurso'].str.startswith('RS-', na=False)].copy()
    atividades_para_excluir = ["Intervalo para almoço", "Indisponibilidade"]
    df_produtivo = df_equipes[~df_equipes['Tipo de Atividade'].isin(atividades_para_excluir)].copy()
    df_produtivo = df_produtivo[df_produtivo['Processo'] != 'CORTE MOTO']
    
    if df_produtivo.empty:
        return "<h1>Relatório de Produtividade</h1><p>Nenhuma atividade produtiva encontrada para exibir.</p>"
        
    df_categorizado = _categorizar_status(df_produtivo)

    if df_categorizado.empty:
        return "<h1>Relatório de Produtividade</h1><p>Nenhuma atividade com status relevante encontrada.</p>"

    relatorio = df_categorizado.groupby(['Processo', 'Recurso'])['categoria_status'].value_counts().unstack(fill_value=0)
    
    for cat in ['Concluído', 'Não Concluído', 'Pendentes']:
        if cat not in relatorio.columns:
            relatorio[cat] = 0
            
    relatorio['Total'] = relatorio['Concluído'] + relatorio['Não Concluído']
    ordem_colunas = ['Concluído', 'Não Concluído', 'Total', 'Pendentes']
    relatorio = relatorio[ordem_colunas]
    
    relatorio = relatorio.sort_values(by=['Processo', 'Total'], ascending=[True, False])
    relatorio = relatorio.reset_index()

    def criar_link(recurso):
        return f'<a href="reports/{recurso}.html">{recurso}</a>'
    
    # Função de formatação para destacar a célula do Total
    def formatar_celula_total(valor):
        return f'<span class="total-cell">{valor}</span>'
        
    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_horario_brasil)
    
    tabela_principal_html = relatorio.to_html(
        index=False,
        escape=False,
        classes='table',
        border=1,
        formatters={
            'Recurso': criar_link,
            'Total': formatar_celula_total # Aplica o destaque na coluna Total
        }
    )
    
    conteudo = f"""
        <h2>Relatório de Produtividade por Equipe</h2>
        <h4>Gerado em: {agora.strftime('%d/%m/%Y %H:%M:%S')}</h4>
        {tabela_principal_html}
    """
    
    return _gerar_html_base("Relatório de Produtividade", conteudo)


# --- Bloco para Teste e Geração de TODOS os relatórios ---
if __name__ == '__main__':
    # ... (o bloco de teste continua o mesmo)
    print("--- Iniciando geração completa dos relatórios de produtividade ---")
    try:
        caminho_script = os.path.abspath(__file__)
        caminho_analysis = os.path.dirname(caminho_script)
        caminho_src = os.path.dirname(caminho_analysis)
        caminho_raiz_projeto = os.path.dirname(caminho_src)
        caminho_data = os.path.join(caminho_raiz_projeto, "Data")
        caminho_relatorios_detalhados = os.path.join(caminho_data, "reports")
        caminho_dados_excel = os.path.join(caminho_data, "prod_gstc.xlsx")
        
        if os.path.exists(caminho_relatorios_detalhados):
            shutil.rmtree(caminho_relatorios_detalhados)
        os.makedirs(caminho_relatorios_detalhados, exist_ok=True)
        print(f"  - Pasta de relatórios '{os.path.basename(caminho_relatorios_detalhados)}' está limpa e pronta.")

        if not os.path.exists(caminho_dados_excel):
            raise FileNotFoundError(f"Arquivo de dados não encontrado em {caminho_dados_excel}")

        df_completo = pd.read_excel(caminho_dados_excel)
        
        for col in ['Data', 'Início', 'Fim', 'Data Limite', 'Data Abertura', 'Data_Extracao']:
            if col in df_completo.columns:
                df_completo[col] = pd.to_datetime(df_completo[col])
        
        print(f"Base de dados carregada com {len(df_completo)} linhas.")
        
        relatorio_principal_html = gerar_relatorio_principal_html(df_completo)
        caminho_saida_principal = os.path.join(caminho_data, "relatorio_produtividade.html")
        with open(caminho_saida_principal, 'w', encoding='utf-8') as f:
            f.write(relatorio_principal_html)
        print(f"\n✅ Relatório principal salvo em: {caminho_saida_principal}")

        print("\nGerando relatórios detalhados por equipe...")
        df_equipes_para_relatorio = df_completo[df_completo['Processo'] != 'CORTE MOTO']
        equipes_unicas = df_equipes_para_relatorio[df_equipes_para_relatorio['Recurso'].str.startswith('RS-', na=False)]['Recurso'].unique()
        
        for equipe in equipes_unicas:
            relatorio_detalhe_html = gerar_relatorio_detalhado_equipe_html(df_completo, equipe)
            nome_arquivo_detalhe = f"{equipe}.html"
            caminho_saida_detalhe = os.path.join(caminho_relatorios_detalhados, nome_arquivo_detalhe)
            with open(caminho_saida_detalhe, 'w', encoding='utf-8') as f:
                f.write(relatorio_detalhe_html)
        
        print(f"✅ {len(equipes_unicas)} relatórios detalhados salvos na pasta: {os.path.basename(caminho_relatorios_detalhados)}")
        
    except FileNotFoundError as e:
        print(f"\nERRO: {e}")
        print("Certifique-se de que o script de transformação foi executado primeiro.")
    except Exception as e:
        print(f"\nOcorreu um erro durante o teste: {e}")