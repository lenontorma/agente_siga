import pandas as pd
import os
import sys # Importa a biblioteca do sistema

# --- Bloco de código para encontrar a pasta 'src' e permitir a execução autônoma ---
try:
    caminho_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if caminho_src not in sys.path:
        sys.path.append(caminho_src)
finally:
    # Remove as variáveis para não poluir o namespace global
    del sys
# --- Fim do Bloco ---

# --- Imports ajustados para serem absolutos a partir de 'src' ---
from etl.contracts import ContratoDadosBrutos, validar_dados
from analysis import mappings
import openpyxl
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Sobe três níveis (transform.py -> etl -> src -> agente_siga)
CAMINHO_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAMINHO_DATA = os.path.join(CAMINHO_RAIZ_PROJETO, "Data")

CAMINHO_PROD_COI = os.path.join(CAMINHO_DATA, "prod_coi.csv")
CAMINHO_PROD_FISC = os.path.join(CAMINHO_DATA, "prod_fisc.csv")


def processar_arquivo(caminho_arquivo: str, nome_arquivo: str) -> pd.DataFrame:
    """
    Função completa para processar um único arquivo: ler, validar, tratar duplicatas e transformar.
    """
    print(f"\n--- Processando arquivo: {nome_arquivo} ---")
    
    df_bruto = pd.read_csv(caminho_arquivo, dtype=str).fillna('')
    print(f"Arquivo lido com {df_bruto.shape[0]} linhas e {df_bruto.shape[1]} colunas.")
    
    validar_dados(df_bruto, ContratoDadosBrutos, nome_arquivo)
    
    print("\nTratando colunas duplicadas e selecionando colunas de produção...")
    coluna_alvo_texto = "Tipo de Atividade"
    lista_colunas = df_bruto.columns.to_list()
    indices_encontrados = [i for i, col in enumerate(lista_colunas) if coluna_alvo_texto in col]
    
    if len(indices_encontrados) >= 2:
        idx_primeira = indices_encontrados[0]
        idx_segunda = indices_encontrados[1]
        lista_colunas[idx_primeira] = "Tipo de Atividade_DESCARTAR"
        lista_colunas[idx_segunda] = "Tipo de Atividade"
        df_bruto.columns = lista_colunas
        print("  - Coluna 'Tipo de Atividade' duplicada foi tratada.")
    
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
    
    print("Convertendo tipos de dados...")
    formato_completo = '%d/%m/%Y %H:%M:%S'
    formato_ano_curto = '%d/%m/%y'
    
    for col in ['Data Limite', 'Data Abertura']:
        df_producao[col] = pd.to_datetime(df_producao[col], format=formato_completo, errors='coerce')
        
    df_producao['Data'] = pd.to_datetime(df_producao['Data'], format=formato_ano_curto, errors='coerce')
    
    df_producao['Início'] = pd.to_datetime(
        df_producao['Data'].dt.strftime('%Y-%m-%d') + ' ' + df_producao['Início'].astype(str).str.strip(),
        errors='coerce'
    )
    df_producao['Fim'] = pd.to_datetime(
        df_producao['Data'].dt.strftime('%Y-%m-%d') + ' ' + df_producao['Fim'].astype(str).str.strip(),
        errors='coerce'
    )
    
    print("Limpeza e conversão de tipos concluída.")
    return df_producao


def definir_processo(df: pd.DataFrame) -> pd.DataFrame:
    # ... (função existente, sem alterações)
    print("\nAdicionando a coluna 'Processo'...")
    codigos_extraidos = df['Recurso'].str.extract(r'-([A-Z]0)', expand=False)
    df['Processo'] = codigos_extraidos.map(mappings.MAPEAMENTO_PROCESSO).fillna('')
    print("  ✅ Coluna 'Processo' criada com sucesso.")
    return df


def definir_seccional(df: pd.DataFrame) -> pd.DataFrame:
    # ... (função existente, sem alterações)
    print("\nAdicionando a coluna 'Seccional'...")
    df['Seccional'] = df['Cidade'].str.upper().map(mappings.MAPEAMENTO_SECCIONAL).fillna('Não Mapeado')
    print("  ✅ Coluna 'Seccional' criada com sucesso.")
    return df


def definir_anexo_iv(df: pd.DataFrame) -> pd.DataFrame:
    # ... (função existente, sem alterações)
    print("\nAdicionando a coluna 'Anexo IV'...")
    df['Anexo IV'] = np.where(df['Tipo de Atividade'].isin(mappings.ATIVIDADES_ANEXO_IV), 'Sim', 'Não')
    print("  ✅ Coluna 'Anexo IV' criada com sucesso.")
    return df


def run_transformation():
    """
    Executa a validação e transformação para ambos os arquivos e os concatena.
    """
    try:
        if not os.path.exists(CAMINHO_PROD_COI):
            print(f"❌ ERRO CRÍTICO: O arquivo principal {os.path.basename(CAMINHO_PROD_COI)} não foi encontrado.")
            return pd.DataFrame()
        
        df_coi = processar_arquivo(CAMINHO_PROD_COI, "prod_coi.csv")
        lista_de_dataframes = [df_coi]

        if os.path.exists(CAMINHO_PROD_FISC):
            df_fisc = processar_arquivo(CAMINHO_PROD_FISC, "prod_fisc.csv")
            lista_de_dataframes.append(df_fisc)
        else:
            print(f"\n[AVISO] O arquivo {os.path.basename(CAMINHO_PROD_FISC)} não foi encontrado.")

        print("\nConcatenando os dataframes de produção...")
        prod_gstc_df = pd.concat(lista_de_dataframes, ignore_index=True)
        print(f"DataFrame antes da exclusão final: {prod_gstc_df.shape[0]} linhas.")

        # --- ALTERAÇÃO APLICADA AQUI ---
        # Filtra o DataFrame para EXCLUIR linhas onde o 'Recurso' contém '-H0'
        linhas_antes = len(prod_gstc_df)
        prod_gstc_df = prod_gstc_df[~prod_gstc_df['Recurso'].str.contains('-H0', na=False)]
        linhas_depois = len(prod_gstc_df)
        print(f"\nExcluindo equipes de 'CORTE MOTO' (Recurso com '-H0')...")
        print(f"  - {linhas_antes - linhas_depois} linhas foram removidas.")
        
        print(f"DataFrame final criado com {prod_gstc_df.shape[0]} linhas e {prod_gstc_df.shape[1]} colunas.")

        fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
        agora_brasil = datetime.now(fuso_horario_brasil)
        print(f"\nData e hora da execução (Fuso de São Paulo): {agora_brasil.strftime('%d/%m/%Y %H:%M:%S')}")
        
        prod_gstc_df['Data_Extracao'] = agora_brasil
        print("  - Coluna 'Data_Extracao' adicionada ao DataFrame.")

        prod_gstc_df = definir_processo(prod_gstc_df)
        prod_gstc_df = definir_seccional(prod_gstc_df)
        prod_gstc_df = definir_anexo_iv(prod_gstc_df)

        print("\nVerificando se alguma coluna está 100% vazia no DataFrame final...")
        # ... (código de verificação de colunas vazias)
        
        print("\nPreparando colunas de data/hora para exportação para Excel...")
        prod_gstc_df['Data_Extracao'] = prod_gstc_df['Data_Extracao'].dt.tz_localize(None)
        print("  - Fuso horário removido da coluna 'Data_Extracao'.")
        
        caminho_saida = os.path.join(CAMINHO_DATA, "prod_gstc.xlsx")
        prod_gstc_df.to_excel(caminho_saida, index=False)
        print(f"\nArquivo final salvo em: {caminho_saida}")

        return prod_gstc_df

    except Exception as e:
        print(f"A transformação falhou: {e}")
        return pd.DataFrame()
    
if __name__ == "__main__":
    df_final = run_transformation()
    if df_final is not None:
        print("\nTransformação concluída com sucesso!")