import pandas as pd
from pydantic import BaseModel, ValidationError, Field
from typing import Optional, Any
from datetime import datetime

class ContratoDadosBrutos(BaseModel):
    Recurso: Optional[Any] = None
    Data: Optional[Any] = None
    Status_da_Atividade: Optional[Any] = Field(alias='Status da Atividade', default=None)
    Cidade: Optional[Any] = None
    Início: Optional[Any] = None
    Fim: Optional[Any] = None
    Duração: Optional[Any] = None
    Tempo_de_Deslocamento: Optional[Any] = Field(alias='Tempo de Deslocamento', default=None)
    Tipo_de_Atividade: Optional[Any] = Field(alias='Tipo de Atividade', default=None) # Apenas uma definição é necessária
    Ordem_de_Serviço: Optional[Any] = Field(alias='Ordem de Serviço', default=None)
    Abrangência: Optional[Any] = None
    Tipo_de_Natureza_Text: Optional[Any] = Field(alias='Tipo de Natureza - Text', default=None)
    Tipo_de_Causa_Text: Optional[Any] = Field(alias='Tipo de Causa - Text', default=None)
    SubTipo_de_Causa_Text: Optional[Any] = Field(alias='SubTipo de Causa - Text', default=None)
    Tipo_de_Conclusão_Executada: Optional[Any] = Field(alias='Tipo de Conclusão Executada', default=None)
    Tipo_de_Conclusão: Optional[Any] = Field(alias='Tipo de Conclusão', default=None)
    Tipo_de_Conclusão_Não_Executada: Optional[Any] = Field(alias='Tipo de Conclusão Não Executada', default=None)
    Latitude: Optional[Any] = None
    Longitude: Optional[Any] = None
    Posição_na_Rota: Optional[Any] = Field(alias='Posição na Rota', default=None)
    Status_da_Coordenada: Optional[Any] = Field(alias='Status da Coordenada', default=None)
    Área_de_Deslocamento: Optional[Any] = Field(alias='Área de Deslocamento', default=None)
    Data_Limite: Optional[Any] = Field(alias='Data Limite', default=None)
    Data_Abertura: Optional[Any] = Field(alias='Data Abertura', default=None)
    Valor_Total_Contrato: Optional[Any] = Field(alias='Valor Total Contrato', default=None)
    Valor: Optional[Any] = None
    Code: Optional[Any] = None
    Número_Ocorrência: Optional[Any] = Field(alias='Número Ocorrência', default=None)
    Número_da_Nota: Optional[Any] = Field(alias='Número da Nota', default=None)
    Número_de_Clientes_Interrompidos: Optional[Any] = Field(alias='Número de Clientes Interrompidos', default=None)
    Medidor_Retirado: Optional[Any] = Field(alias='Medidor Retirado', default=None)
    Medidor_Instalado: Optional[Any] = Field(alias='Medidor Instalado', default=None)
    Observação: Optional[Any] = None
    Tipo_de_Indisponibilidade: Optional[Any] = Field(alias='Tipo de Indisponibilidade', default=None)
    Instalação: Optional[Any] = None

    class Config:
        extra = 'allow'
        populate_by_name = True

def validar_dados(df: pd.DataFrame, modelo_contrato: BaseModel, nome_arquivo: str):
    """Valida a estrutura de um DataFrame contra um contrato Pydantic."""
    print(f"Iniciando validação do contrato '{modelo_contrato.__name__}' para o arquivo: {nome_arquivo}")
    
    df_para_validar = df.astype(object).where(pd.notnull(df), None)
    
    erros = []
    for index, row in df_para_validar.iterrows():
        try:
            modelo_contrato.model_validate(row.to_dict())
        except ValidationError as e:
            erros.append(f"  - Erro na linha {index + 2}: {e}")

    if erros:
        print(f"\n❌ ERRO DE CONTRATO no arquivo {nome_arquivo}!")
        for erro in erros[:10]:
            print(erro)
        raise ValueError(f"Validação do contrato '{modelo_contrato.__name__}' falhou.")
    
    print(f"✅ Contrato '{modelo_contrato.__name__}' validado com sucesso para {nome_arquivo}.")
    return True