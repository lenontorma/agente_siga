from dotenv import load_dotenv
import os

try:
    caminho_script = os.path.abspath(__file__)
    caminho_etl = os.path.dirname(caminho_script)
    caminho_src = os.path.dirname(caminho_etl)
    caminho_raiz_projeto = os.path.dirname(caminho_src)
    load_dotenv(os.path.join(caminho_raiz_projeto, '.env'))
except Exception as e:
    print(f"Aviso: Não foi possível carregar o arquivo .env em mappings.py. Erro: {e}")


# 1. Lê a string do .env, com um valor padrão de string vazia se não encontrar
user_ids_str = os.getenv("TELEGRAM_USER_IDS", "")
# 2. Converte a string em uma lista de IDs, removendo espaços e itens vazios
LISTA_DE_IDS_PRINCIPAL = [uid.strip() for uid in user_ids_str.split(',') if uid.strip()]

# ==============================================================================
# MAPEAMENTOS DE DADOS (REGRAS DE NEGÓCIO)
# ==============================================================================


MAPEAMENTO_PROCESSO = {
    'C0': 'CORTE',
    'F0': 'FISCALIZACAO',
    'L0': 'LIGACAO NOVA',
    'E0': 'EMERGENCIAL',
    'H0': 'CORTE MOTO',
    'A0': 'FISCALIZACAO'
}


MAPEAMENTO_SECCIONAL = {
    "BAGE": "CAMPANHA",
    "DOM PEDRITO": "CAMPANHA",
    "HULHA NEGRA": "CAMPANHA",
    "CANDIOTA": "CAMPANHA",
    "LAVRAS DO SUL": "CAMPANHA",
    "PINHEIRO MACHADO": "CAMPANHA",
    "PEDRAS ALTAS": "CAMPANHA",
    "CAMAQUA": "CENTRO SUL",
    "CRISTAL": "CENTRO SUL",
    "CHUVISCA": "CENTRO SUL",
    "ARAMBARE": "CENTRO SUL",
    "TAPES": "CENTRO SUL",
    "AMARAL FERRADOR": "CENTRO SUL",
    "DOM FELICIANO": "CENTRO SUL",
    "ENCRUZILHADA DO SUL": "CENTRO SUL",
    "SAO LOURENCO DO SUL": "CENTRO SUL",
    "TURUCU": "CENTRO SUL",
    "SERTAO SANTANA": "CENTRO SUL",
    "SENTINELA DO SUL": "CENTRO SUL",
    "CERRO GRANDE DO SUL": "CENTRO SUL",
    "RIO GRANDE": "LITORAL SUL",
    "SAO JOSE DO NORTE": "LITORAL SUL",
    "SANTA VITORIA DO PALMAR": "LITORAL SUL",
    "CHUI": "LITORAL SUL",
    "ARROIO GRANDE": "SUL",
    "CANGUCU": "SUL",
    "CERRITO": "SUL",
    "PIRATINI": "SUL",
    "HERVAL": "SUL",
    "JAGUARAO": "SUL",
    "PELOTAS": "SUL",
    "ARROIO DO PADRE": "SUL",
    "CAPAO DO LEAO": "SUL",
    "MORRO REDONDO": "SUL",
    "PEDRO OSORIO": "SUL",
    "BARAO DO TRIUNFO": "CENTRO SUL",
    "BARRA DO RIBEIRO": "CENTRO SUL",
    "MARIANA PIMENTEL": "CENTRO SUL",
    "SAO JERONIMO": "CENTRO SUL",
}


ATIVIDADES_ANEXO_IV = {
    "RELIGABT - Religação de Baixa Tensão",
    "TROCPABT - Troca Padrão Baixa Tensão (BT)",
    "LIGANOVA - Ligação Nova",
    "DSBTPDCL - Desligamento De Unidade Consumidora"
}


MAPEAMENTO_ALERTAS_SECCIONAL = {
    'SUL': LISTA_DE_IDS_PRINCIPAL,
    'CENTRO SUL': LISTA_DE_IDS_PRINCIPAL,
    'LITORAL SUL': LISTA_DE_IDS_PRINCIPAL,
    'CAMPANHA': LISTA_DE_IDS_PRINCIPAL,
    'GERAL': LISTA_DE_IDS_PRINCIPAL 
}

