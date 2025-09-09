import pandas as pd
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import os

def gerar_resumo_produtividade(df: pd.DataFrame, 
                               seccional: Optional[str] = None, 
                               processo: Optional[str] = None) -> str:
    """Filtra e gera um resumo simples de produtividade por status."""
    # ... (Esta função continua a mesma de antes, para não quebrar outras funcionalidades)
    df_filtrado = df.copy()
    filtros_aplicados = []
    if seccional:
        df_filtrado = df_filtrado[df_filtrado['Seccional'].str.strip().str.upper() == seccional.strip().upper()]
        filtros_aplicados.append(f"Seccional = '{seccional}'")
    if processo:
        df_filtrado = df_filtrado[df_filtrado['Processo'].str.strip().str.upper() == processo.strip().upper()]
        filtros_aplicados.append(f"Processo = '{processo}'")
    if df_filtrado.empty:
        return f"Nenhuma atividade encontrada para os filtros: {', '.join(filtros_aplicados)}." if filtros_aplicados else "Nenhuma atividade encontrada."
    contagem_status = df_filtrado['Status da Atividade'].value_counts()
    total_atividades = len(df_filtrado)
    titulo_filtro = f"para filtros: {', '.join(filtros_aplicados)}" if filtros_aplicados else "geral"
    resposta = f"📊 *Resumo de Produtividade ({titulo_filtro})*\n\n"
    resposta += f"Total de Atividades: *{total_atividades}*\n-----------------------------------\n"
    for status, contagem in contagem_status.items():
        percentual = (contagem / total_atividades) * 100
        resposta += f"- *{status}:* {contagem} ({percentual:.2f}%)\n"
    return resposta


## --- FUNÇÃO DE ANÁLISE REFEITA COM AS NOVAS REGRAS --- ##
def gerar_relatorio_equipes_por_seccional(df: pd.DataFrame, seccional_filtro: str) -> str:
    """
    Filtra por seccional, considera apenas equipes (Recurso começando com 'RS-'),
    e gera um relatório de produtividade agrupado por Processo e Equipe.
    """
    print(f"\nGerando relatório de produtividade por equipe para a Seccional: '{seccional_filtro}'...")

    # 1. FILTRAGEM INICIAL
    # Filtra pela seccional desejada
    filtro_seccional = df['Seccional'].str.strip().str.upper() == seccional_filtro.strip().upper()
    df_seccional = df[filtro_seccional].copy()
    
    # Filtra para manter apenas equipes (Recurso que começa com 'RS-')
    df_seccional = df_seccional[df_seccional['Recurso'].str.startswith('RS-', na=False)]

    if df_seccional.empty:
        return f"Nenhuma equipe (Recurso começando com 'RS-') encontrada para a Seccional '{seccional_filtro}'."

    # Exclui atividades não produtivas
    atividades_para_excluir = ["Intervalo para almoço", "Indisponibilidade"]
    df_produtivo = df_seccional[~df_seccional['Tipo de Atividade'].isin(atividades_para_excluir)].copy()
    
    if df_produtivo.empty:
        return f"Nenhuma atividade produtiva encontrada para as equipes da Seccional '{seccional_filtro}'."
        
    # 2. CATEGORIZAR STATUS (COM MAIS DETALHES)
    status_concluido = ['concluído']
    status_nao_concluido = ['não concluído']
    status_pendentes = ['deslocamento', 'pendente', 'iniciado']
    
    # Usa .str.lower() para garantir a comparação correta
    df_lower_status = df_produtivo['Status da Atividade'].str.lower()
    
    df_produtivo['categoria_status'] = 'Outros' # Categoria padrão
    df_produtivo.loc[df_lower_status.isin(status_concluido), 'categoria_status'] = 'Concluído'
    df_produtivo.loc[df_lower_status.isin(status_nao_concluido), 'categoria_status'] = 'Não Concluído'
    df_produtivo.loc[df_lower_status.isin(status_pendentes), 'categoria_status'] = 'Pendentes'

    # 3. AGRUPAR POR PROCESSO E EQUIPE (RECURSO)
    contagem_final = df_produtivo.groupby(['Processo', 'Recurso'])['categoria_status'].value_counts().unstack(fill_value=0)
    
    # Garante que as colunas de status sempre existam
    for cat in ['Concluído', 'Não Concluído', 'Pendentes', 'Outros']:
        if cat not in contagem_final.columns:
            contagem_final[cat] = 0
            
    contagem_final['Total'] = contagem_final.sum(axis=1)
    
    # 4. FORMATAR A SAÍDA
    fuso_horario_brasil = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_horario_brasil)
    
    resposta = f"📈 *Relatório de Produtividade por Equipe*\n"
    resposta += f"*- Seccional:* {seccional_filtro.upper()}\n"
    resposta += f"*- Data:* {agora.strftime('%d/%m/%Y %H:%M')}\n"
    resposta += "_(Apenas Recursos 'RS-' | Exclui almoço/indisponibilidade)_\n\n"
    
    # Itera sobre os processos para criar os cabeçalhos
    processos_unicos = contagem_final.index.get_level_values('Processo').unique()
    
    for processo in sorted(processos_unicos):
        if not processo: # Pula processos vazios, se houver
            continue
            
        resposta += f"*{processo.upper()}*\n"
        
        # Filtra o dataframe para as equipes apenas deste processo
        equipes_no_processo = contagem_final[contagem_final.index.get_level_values('Processo') == processo]
        equipes_no_processo = equipes_no_processo.sort_values(by='Total', ascending=False)
        
        for (proc, recurso), dados in equipes_no_processo.iterrows():
            resposta += f"  👤 `{recurso}`\n"
            resposta += f"    - Concluídos: {dados['Concluído']}\n"
            resposta += f"    - Não Concluídos: {dados['Não Concluído']}\n"
            resposta += f"    - Pendentes: {dados['Pendentes']}\n"
            resposta += f"    - *Total:* {dados['Total']}\n"
        resposta += "\n"
        
    return resposta


# --- Bloco para Teste Independente ---
if __name__ == '__main__':
    print("--- Testando o módulo de análise de produtividade ---")
    try:
        caminho_script = os.path.abspath(__file__)
        caminho_analysis = os.path.dirname(caminho_script)
        caminho_src = os.path.dirname(caminho_analysis)
        caminho_raiz_projeto = os.path.dirname(caminho_src)
        caminho_dados = os.path.join(caminho_raiz_projeto, "Data", "prod_gstc.xlsx")

        if not os.path.exists(caminho_dados):
            raise FileNotFoundError(f"Arquivo de dados não encontrado em {caminho_dados}")

        df_completo = pd.read_excel(caminho_dados)
        
        for col in ['Data', 'Início', 'Fim', 'Data Limite', 'Data Abertura', 'Data_Extracao']:
            if col in df_completo.columns:
                df_completo[col] = pd.to_datetime(df_completo[col])
        
        print(f"Base de dados carregada com {len(df_completo)} linhas.")
        
        # --- TESTE DA NOVA FUNÇÃO DEDICADA ---
        seccional_para_teste = "CENTRO SUL"
        
        relatorio_filtrado = gerar_relatorio_equipes_por_seccional(df_completo, seccional_para_teste)
        print(relatorio_filtrado)
        
    except FileNotFoundError as e:
        print(f"\nERRO: {e}")
        print("Certifique-se de que o script de transformação foi executado primeiro.")
    except Exception as e:
        print(f"\nOcorreu um erro durante o teste: {e}")