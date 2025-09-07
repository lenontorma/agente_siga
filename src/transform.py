
import pandas as pd


prod_coi = pd.read_csv(r"data/prod_coi.csv")
prod_coi_df = pd.DataFrame(prod_coi)

#Selecionando colunas
prod_coi_df = prod_coi_df[["Recurso",
"Data",
"Status da Atividade",
"Cidade",
"Início",
"Fim",
"Duração",
"Tempo de Deslocamento",
"Tipo de Atividade",
"Ordem de Serviço",
"Abrangência",
"Tipo de Natureza - Text",
"Tipo de Causa - Text",
"SubTipo de Causa - Text",
"Tipo de Conclusão Executada",
"Tipo de Conclusão",
"Tipo de Conclusão Não Executada",
"Latitude",
"Longitude",
"Posição na Rota",
"Status da Coordenada",
"Área de Deslocamento",
"Data Limite",
"Data Abertura",
"Valor Total Contrato",
"Valor",
"Code",
"Número Ocorrência",
"Número da Nota",
"Número de Clientes Interrompidos",
"Medidor Retirado",
"Medidor Instalado",
"Observação",
"Tipo de Indisponibilidade",
"Instalação",
]]

print(prod_coi_df)
