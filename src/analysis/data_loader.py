import pandas as pd
import os

def carregar_dados() -> pd.DataFrame:
    """
    Carrega o arquivo Excel final em um DataFrame do Pandas e faz uma limpeza básica,
    servindo como a fonte única de dados para todos os módulos de análise.
    """
    print("Carregando base de dados de 'prod_gstc.xlsx'...")
    
    # Encontra o caminho do arquivo de dados de forma robusta
    try:
        caminho_script = os.path.abspath(__file__)
        caminho_analysis = os.path.dirname(caminho_script)
        caminho_src = os.path.dirname(caminho_analysis)
        caminho_raiz_projeto = os.path.dirname(caminho_src)
        caminho_dados = os.path.join(caminho_raiz_projeto, "Data", "prod_gstc.xlsx")

        if not os.path.exists(caminho_dados):
            raise FileNotFoundError(f"Arquivo de dados não encontrado em {caminho_dados}")

        df = pd.read_excel(caminho_dados)
        
        # Garante que as colunas de data mais comuns sejam do tipo datetime
        # Adicione outras colunas de data aqui se necessário
        for col in ['Data', 'Início', 'Fim', 'Data Limite', 'Data Abertura', 'Data_Extracao']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        print(f"Base de dados carregada com sucesso ({len(df)} linhas).")
        return df

    except Exception as e:
        print(f"ERRO ao carregar os dados: {e}")
        # Retorna um DataFrame vazio em caso de erro para não quebrar os scripts que o chamam
        return pd.DataFrame()