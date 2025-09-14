import pandas as pd
import os

def carregar_dados() -> pd.DataFrame:
    """
    Carrega o arquivo Excel final ('prod_gstc.xlsx') e garante que os tipos de
    dados estejam corretos para a análise.

    Esta função é projetada para NUNCA retornar None. Em caso de qualquer erro,
    retorna um DataFrame vazio.
    """
    print("Carregando base de dados de 'prod_gstc.xlsx'...")
    
    try:
        # Encontra o caminho do arquivo de dados de forma robusta
        caminho_script = os.path.abspath(__file__)
        caminho_analysis = os.path.dirname(caminho_script)
        caminho_src = os.path.dirname(caminho_analysis)
        caminho_raiz_projeto = os.path.dirname(caminho_src)
        caminho_dados = os.path.join(caminho_raiz_projeto, "Data", "prod_gstc.xlsx")

        if not os.path.exists(caminho_dados):
            raise FileNotFoundError(f"Arquivo de dados não encontrado em {caminho_dados}")

        # Define as colunas que devem ser lidas como datas
        colunas_de_data = [
            'Data', 'Início', 'Fim', 'Data Limite', 'Data Abertura', 'Data_Extracao'
        ]

        # Lê o Excel, já convertendo as datas para otimizar
        df = pd.read_excel(caminho_dados, parse_dates=colunas_de_data)
        
        print(f"Base de dados carregada com sucesso ({len(df)} linhas).")
        return df

    except Exception as e:
        # Se qualquer erro ocorrer (arquivo não encontrado, erro de leitura, etc.),
        # imprime o erro e retorna um DataFrame vazio.
        print(f"ERRO CRÍTICO ao carregar os dados: {e}")
        print("Retornando um DataFrame vazio.")
        return pd.DataFrame()