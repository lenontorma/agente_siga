import os
import pandas as pd
from pydantic import BaseModel, ValidationError, Field
from typing import Optional, Any
from datetime import datetime, date

# ==============================================================================
# CONTRATO 1: PARA OS DADOS BRUTOS (Lê 63 colunas, valida 35)
# ==============================================================================
class ContratoDadosBrutos(BaseModel):
    Recurso: Optional[str] = None
    Data: Optional[str] = None
    Status_da_Atividade: Optional[str] = Field(alias='Status da Atividade', default=None)
    Cidade: Optional[str] = None
    Início: Optional[str] = None
    Fim: Optional[str] = None
    Duração: Optional[str] = None
    Tempo_de_Deslocamento: Optional[str] = Field(alias='Tempo de Deslocamento', default=None)
    Tipo_de_Atividade: Optional[str] = Field(alias='Tipo de Atividade', default=None)
    Ordem_de_Serviço: Optional[str] = Field(alias='Ordem de Serviço', default=None)
    Abrangência: Optional[str] = None
    Tipo_de_Natureza_Text: Optional[str] = Field(alias='Tipo de Natureza - Text', default=None)
    Tipo_de_Causa_Text: Optional[str] = Field(alias='Tipo de Causa - Text', default=None)
    SubTipo_de_Causa_Text: Optional[str] = Field(alias='SubTipo de Causa - Text', default=None)
    Tipo_de_Conclusão_Executada: Optional[str] = Field(alias='Tipo de Conclusão Executada', default=None)
    Tipo_de_Conclusão: Optional[str] = Field(alias='Tipo de Conclusão', default=None)
    Tipo_de_Conclusão_Não_Executada: Optional[str] = Field(alias='Tipo de Conclusão Não Executada', default=None)
    Latitude: Optional[Any] = None
    Longitude: Optional[Any] = None
    Posição_na_Rota: Optional[Any] = Field(alias='Posição na Rota', default=None)
    Status_da_Coordenada: Optional[str] = Field(alias='Status da Coordenada', default=None)
    Área_de_Deslocamento: Optional[str] = Field(alias='Área de Deslocamento', default=None)
    Data_Limite: Optional[str] = Field(alias='Data Limite', default=None)
    Data_Abertura: Optional[str] = Field(alias='Data Abertura', default=None)
    Valor_Total_Contrato: Optional[Any] = Field(alias='Valor Total Contrato', default=None)
    Valor: Optional[Any] = None
    Code: Optional[str] = None
    Número_Ocorrência: Optional[Any] = Field(alias='Número Ocorrência', default=None)
    Número_da_Nota: Optional[Any] = Field(alias='Número da Nota', default=None)
    Número_de_Clientes_Interrompidos: Optional[Any] = Field(alias='Número de Clientes Interrompidos', default=None)
    Medidor_Retirado: Optional[Any] = Field(alias='Medidor Retirado', default=None)
    Medidor_Instalado: Optional[Any] = Field(alias='Medidor Instalado', default=None)
    Observação: Optional[str] = None
    Tipo_de_Indisponibilidade: Optional[str] = Field(alias='Tipo de Indisponibilidade', default=None)
    Instalação: Optional[Any] = None

    class Config:
        extra = 'allow'
        from_attributes = True
        populate_by_name = True

# ==============================================================================
# CONTRATO 2: PARA OS DADOS DE PRODUÇÃO (35 COLUNAS)
# ==============================================================================
class ContratoDadosProducao(BaseModel):
    # Este contrato é mais rígido e espera os tipos corretos
    Recurso: str
    Data: datetime
    Status_da_Atividade: str = Field(alias='Status da Atividade')
    # ... (o resto do contrato de produção, como estava antes) ...

# ==============================================================================
# FUNÇÃO DE VALIDAÇÃO (SIMPLIFICADA E CORRIGIDA)
# ==============================================================================
def validar_dados(df: pd.DataFrame, modelo_contrato: BaseModel, nome_arquivo: str):
    """Valida um DataFrame contra um contrato Pydantic."""
    print(f"Iniciando validação do contrato '{modelo_contrato.__name__}' para o arquivo: {nome_arquivo}")
    
    # Preenche todos os valores vazios (NaN) com None, que o Pydantic entende
    df_para_validar = df.astype(object).where(pd.notnull(df), None)

    erros = []
    for index, row in df_para_validar.iterrows():
        try:
            # Pydantic usa os 'alias' para mapear as colunas do DF para os campos do modelo
            modelo_contrato.model_validate(row.to_dict())
        except ValidationError as e:
            erros.append(f"  - Erro na linha {index + 2}: {e}")

    if erros:
        print(f"\n❌ ERRO DE CONTRATO no arquivo {nome_arquivo}!")
        for erro in erros[:10]: # Mostra os 10 primeiros erros
            print(erro)
        raise ValueError(f"Validação do contrato '{modelo_contrato.__name__}' falhou.")
    
    print(f"✅ Contrato '{modelo_contrato.__name__}' validado com sucesso para {nome_arquivo}.")
    return True