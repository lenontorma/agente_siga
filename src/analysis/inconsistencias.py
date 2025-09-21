import pandas as pd
from typing import List

def encontrar_conclusoes_improprias(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encontra atividades cuja 'Tipo de Conclusão Executada' parece ser uma
    descrição de problema em vez de um tipo de conclusão.
    """
    print("Buscando por tipos de conclusão impróprios...")
    
    # Lista de frases a serem procuradas (insensível a maiúsculas/minúsculas)
    frases_improprias = [
        "DISJUNTOR DESARMADO"
        # Adicione outras frases aqui se necessário
    ]
    
    # Cria uma máscara booleana para encontrar as linhas
    # na=False garante que valores vazios não causem erro
    mask = df['Tipo de Conclusão Executada'].str.lower().isin(
        [frase.lower() for frase in frases_improprias],
    ).fillna(False)
    
    return df[mask]


def encontrar_cancelamentos_suspeitos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encontra atividades canceladas cuja observação contém palavras-chave
    que indicam motivos não operacionais (almoço, fim de turno, etc.).
    """
    print("Buscando por cancelamentos com observações suspeitas...")
    
    # Palavras-chave a serem procuradas na coluna 'Observação'
    palavras_chave = ['intervalo', 'almoco', 'almoço', 'fim de turno', 'fora de rota']
    
    # Cria um padrão regex para encontrar qualquer uma das palavras (insensível a maiúsculas/minúsculas)
    regex_pattern = '|'.join(palavras_chave)
    
    # Filtro 1: Status deve ser 'Cancelado'
    mask_status = df['Status da Atividade'].str.strip().str.lower() == 'cancelado'
    
    # Filtro 2: Observação deve conter uma das palavras-chave
    mask_obs = df['Observação'].str.contains(regex_pattern, case=False, na=False)
    
    # Retorna apenas as linhas que atendem a AMBAS as condições
    return df[mask_status & mask_obs]