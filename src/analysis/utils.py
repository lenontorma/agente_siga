import pandas as pd

def gerar_html_base(titulo: str, conteudo_body: str) -> str:
    """
    Função auxiliar centralizada para criar a estrutura base de um arquivo HTML.
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
            table {{ border-collapse: collapse; width: auto; min-width: 80%; margin-top: 20px; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            a {{ color: #007bff; text-decoration: none; font-weight: bold; }}
            a:hover {{ text-decoration: underline; }}
            .total-column {{ background-color: #e0e0e0; font-weight: bold; }}
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

def categorizar_status(df: pd.DataFrame) -> pd.DataFrame:
    """Função auxiliar centralizada para categorizar os status das atividades."""
    df_categorizado = df.copy()
    status_concluido = ['concluído']
    status_nao_concluido = ['não concluído']
    status_pendentes = ['deslocamento', 'pendente', 'iniciado']
    df_lower_status = df_categorizado['Status da Atividade'].str.lower()
    
    # Renomeia a categoria 'Outros' para 'Cancelado'
    df_categorizado['categoria_status'] = 'Cancelado'
    df_categorizado.loc[df_lower_status.isin(status_concluido), 'categoria_status'] = 'Concluído'
    df_categorizado.loc[df_lower_status.isin(status_nao_concluido), 'categoria_status'] = 'Não Concluído'
    df_categorizado.loc[df_lower_status.isin(status_pendentes), 'categoria_status'] = 'Pendentes'
    
    categorias_relevantes = ['Concluído', 'Não Concluído', 'Pendentes', 'Cancelado']
    return df_categorizado[df_categorizado['categoria_status'].isin(categorias_relevantes)]