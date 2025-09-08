import pandas as pd
import os
from contracts import ContratoDadosBrutos, validar_dados
import openpyxl

# --- CONFIGURAÇÃO DE CAMINHOS ---
CAMINHO_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAMINHO_DATA = os.path.join(CAMINHO_RAIZ_PROJETO, "Data")

CAMINHO_PROD_COI = os.path.join(CAMINHO_DATA, "prod_coi.csv")
CAMINHO_PROD_FISC = os.path.join(CAMINHO_DATA, "prod_fisc.csv")


def processar_arquivo(caminho_arquivo: str, nome_arquivo: str) -> pd.DataFrame:
    """
    Função completa para processar um único arquivo: ler, validar a estrutura bruta e depois limpar e transformar.
    """
    print(f"\n--- Processando arquivo: {nome_arquivo} ---")
    
    # 1. Leitura do arquivo bruto, tratando vazios como strings vazias
    df_bruto = pd.read_csv(caminho_arquivo).fillna('')
    print(f"Arquivo lido com {df_bruto.shape[0]} linhas e {df_bruto.shape[1]} colunas.")
    
    # 2. VALIDAÇÃO ESTRUTURAL (BRONZE)
    validar_dados(df_bruto, ContratoDadosBrutos, nome_arquivo)
    
    # 3. TRANSFORMAÇÃO E LIMPEZA
    colunas_producao = [
        "Recurso", "Data", "Status da Atividade", "Cidade", "Início", "Fim",
        "Duração", "Tempo de Deslocamento", "Tipo de Atividade", "Ordem de Serviço",
        "Abrangência", "Tipo de Natureza - Text", "Tipo de Causa - Text", 
        "SubTipo de Causa - Text", "Tipo de Conclusão Executada", "Tipo de Conclusão",
        "Tipo de Conclusão Não Executada", "Latitude", "Longitude", "Posição na Rota",
        "Status da Coordenada", "Área de Deslocamento", "Data Limite", "Data Abertura",
        "Valor Total Contrato", "Valor", "Code", "Número Ocorrência", "Número da Nota",
        "Número de Clientes Interrompidos", "Medidor Retirado", "Medidor Instalado",
        "Observação", "Tipo de Indisponibilidade", "Instalação"
    ]
    df_producao = df_bruto[colunas_producao].copy()
    
    # Converte colunas de data/hora
    formato_completo = '%d/%m/%Y %H:%M:%S'
    formato_ano_curto = '%d/%m/%y'
    
    for col in ['Data Limite', 'Data Abertura']:
        df_producao[col] = pd.to_datetime(df_producao[col], format=formato_completo, errors='coerce')
        
    df_producao['Data'] = pd.to_datetime(df_producao['Data'], format=formato_ano_curto, errors='coerce')
    df_producao['Início'] = df_producao['Início'].astype(str).str.strip()
    df_producao['Fim'] = df_producao['Fim'].astype(str).str.strip()
    
    df_producao['Início'] = pd.to_datetime(
        df_producao['Data'].dt.strftime('%Y-%m-%d') + ' ' + df_producao['Início'],
        errors='coerce'
    )
    df_producao['Fim'] = pd.to_datetime(
        df_producao['Data'].dt.strftime('%Y-%m-%d') + ' ' + df_producao['Fim'],
        errors='coerce'
    )
    
    return df_producao


def run_transformation():
    """
    Executa a validação e transformação para ambos os arquivos e os concatena.
    """
    try:
        if not os.path.exists(CAMINHO_PROD_COI):
            print(f"❌ ERRO CRÍTICO: O arquivo principal {os.path.basename(CAMINHO_PROD_COI)} não foi encontrado.")
            return None
        
        df_coi = processar_arquivo(CAMINHO_PROD_COI, "prod_coi.csv")
        lista_de_dataframes = [df_coi]

        if os.path.exists(CAMINHO_PROD_FISC):
            df_fisc = processar_arquivo(CAMINHO_PROD_FISC, "prod_fisc.csv")
            lista_de_dataframes.append(df_fisc)
        else:
            print(f"\n[AVISO] O arquivo {os.path.basename(CAMINHO_PROD_FISC)} não foi encontrado.")

        # --- CONCATENAÇÃO FINAL ---
        prod_gstc_df = pd.concat(lista_de_dataframes, ignore_index=True)
        print(f"DataFrame final criado com {prod_gstc_df.shape[0]} linhas e {prod_gstc_df.shape[1]} colunas.")

        # --- VALIDAÇÃO FINAL: VERIFICAR COLUNAS 100% VAZIAS ---
        print("\nVerificando se alguma coluna está 100% vazia no DataFrame final...")
        colunas_vazias_series = prod_gstc_df.isnull().all()
        colunas_totalmente_vazias = colunas_vazias_series[colunas_vazias_series].index.tolist()

        if colunas_totalmente_vazias:
            print(f"  [ALERTA DE QUALIDADE] As seguintes colunas estão 100% vazias (sem nenhum valor):")
            # Usa um loop para imprimir uma por linha, para melhor visualização
            for coluna in colunas_totalmente_vazias:
                print(f"    - {coluna}")
        else:
            print("  ✅ Nenhuma coluna está 100% vazia. Verificação de qualidade aprovada.")
        
        # --- SALVANDO ARQUIVO FINAL ---
        caminho_saida = os.path.join(CAMINHO_DATA, "prod_gstc.xlsx")
        prod_gstc_df.to_excel(caminho_saida, index=False)
        print(f"\nArquivo final salvo em: {caminho_saida}")

        return prod_gstc_df

    except Exception as e:
        print(f"A transformação falhou: {e}")
        return None
    
if __name__ == "__main__":
    df_final = run_transformation()
    if df_final is not None:
        print("\nTransformação concluída com sucesso!")