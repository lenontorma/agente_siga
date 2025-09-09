from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import os
import time
import shutil
from dotenv import load_dotenv

# --- (Suas constantes e configurações de caminho continuam as mesmas) ---
load_dotenv()
USUARIO_SIGA = os.getenv("USUARIO_SIGA")
SENHA_SIGA = os.getenv("SENHA_SIGA")
CAMINHO_SCRIPT = os.path.abspath(__file__)
DIRETORIO_SRC = os.path.dirname(os.path.dirname(CAMINHO_SCRIPT))
CAMINHO_RAIZ_PROJETO = os.path.dirname(DIRETORIO_SRC)
CAMINHO_DOWNLOAD = os.path.join(CAMINHO_RAIZ_PROJETO, "Data")
LOCATOR_BOTÃO_COI = (By.XPATH, '//*[@id="manage-content"]/div[1]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[1]/div[1]/button[1]')
LOCATOR_BOTÃO_SUL_COI = (By.XPATH, '//*[@id="manage-content"]/div[1]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]')
LOCATOR_SUCESSO_LOGIN = (By.XPATH, '//*[@id="manage-content"]/div[1]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[1]/div[1]/button[1]')
LOCATOR_FLAG_LOGIN = (By.XPATH, "//label[@for='delsession']")
LOCATOR_BOTÃO_FISC = (By.XPATH, '//*[@id="manage-content"]/div[1]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[2]/div[1]/button[1]') 
LOCATOR_BOTÃO_SUL_FISC = (By.XPATH, '//*[@id="manage-content"]/div[1]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/div[3]/div[1]')

# --- (As funções de setup, login, navegação, etc. continuam as mesmas) ---
def configurar_driver(caminho_download):
    #...código existente...
    print(f"Configurando downloads para a pasta: {caminho_download}")
    if not os.path.exists(caminho_download):
        os.makedirs(caminho_download)
        print(f"Pasta de download criada em: {caminho_download}")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    prefs = {
        "download.default_directory": caminho_download,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    service = Service(log_path=os.devnull)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fazer_login(driver, usuario, senha):
    #...código existente...
    url = "https://equatorialenergia.etadirect.com/"
    driver.get(url)
    print(f"Acessando a URL: {url}")
    campo_usuario = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="username"]')))
    campo_usuario.send_keys(usuario)
    campo_senha = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))
    campo_senha.send_keys(senha)
    botao_login = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sign-in"]/div/span/span')))
    botao_login.click()
    print("Primeira tentativa de login realizada...")
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(LOCATOR_SUCESSO_LOGIN))
        print("✅ Login bem-sucedido na primeira tentativa.")
        return
    except TimeoutException:
        print("[AVISO] Login inicial falhou. Executando plano de recuperação...")
        campo_senha_recuperacao = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))
        campo_senha_recuperacao.clear()
        campo_senha_recuperacao.send_keys(senha)
        print(" -> Senha inserida novamente.")
        flag_login = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(LOCATOR_FLAG_LOGIN))
        flag_login.click()
        print(" -> Flag de login clicada.")
        botao_login_recuperacao = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sign-in"]/div/span/span')))
        botao_login_recuperacao.click()
        print(" -> Segunda tentativa de login realizada.")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(LOCATOR_SUCESSO_LOGIN))
        print("✅ Login bem-sucedido na segunda tentativa.")

def navegar_para_area(driver, locator_principal, locator_secundario, nome_da_area):
    #...código existente...
    print(f"Navegando para a área '{nome_da_area}'...")
    clicar_elemento_com_tentativas(driver, locator_principal)
    print(f"Clicou no botão principal de '{nome_da_area}'.")
    time.sleep(3)
    clicar_elemento_com_tentativas(driver, locator_secundario)
    print(f"Navegou com sucesso para a sub-área de '{nome_da_area}'.")

def clicar_elemento_com_tentativas(driver, locator, tentativas=3, timeout=15):
    #...código existente...
    for tentativa in range(tentativas):
        try:
            elemento = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
            elemento.click()
            return
        except StaleElementReferenceException:
            print(f"  [AVISO] Elemento 'vencido' encontrado na tentativa {tentativa + 1}/{tentativas}. Tentando novamente...")
            time.sleep(1)
    raise TimeoutException(f"Não foi possível clicar no elemento {locator} após {tentativas} tentativas.")
    
def configurar_filtros_e_visualizacao(driver, alvo_atual):
    #...código existente...
    print("Configurando filtros e visualização...")
    clicar_elemento_com_tentativas(driver, (By.CSS_SELECTOR, "button[data-ofsc-id='dc__top_panel__page_selector__list__btn']"))
    print("Clicou em 'Visualização em Lista'.")
    time.sleep(3)
    clicar_elemento_com_tentativas(driver, (By.XPATH, "//button[@title='Exibir']"))
    time.sleep(2)
    if alvo_atual == "COI":
        print("Alvo é COI, aplicando o filtro hierárquico...")
        clicar_elemento_com_tentativas(driver, (By.XPATH, "//label[.//oj-option[text()='Aplicar de forma hierárquica']]"))
        time.sleep(2)
    else:
        print("Alvo é FISC, pulando o clique no filtro hierárquico.")
    clicar_elemento_com_tentativas(driver, (By.XPATH, "(//button[@title='Aplicar'])[2]"))
    print("Filtros e visualização aplicados.")

# --- FUNÇÃO DE EXPORTAÇÃO ATUALIZADA E ROBUSTA ---
def exportar_e_renomear_arquivo(driver, caminho_download, novo_nome_base, alvo_atual):
    """
    Clica em Ações, Exportar, aguarda o download de forma robusta e renomeia o arquivo.
    """
    print("Iniciando processo de exportação...")
    
    # Verifica se o botão "Ações" está disponível (crítico para FISC)
    if alvo_atual == "FISC":
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "(//button[@title='Ações'])")))
        except TimeoutException:
            print("[AVISO] Botão 'Ações' não disponível para FISC. Pulando download.")
            return

    # 1. Limpa a área: apaga qualquer arquivo de destino antigo
    # Encontra a extensão do primeiro arquivo na pasta para adivinhar a extensão final
    extensao_esperada = ".csv" # Padrão
    arquivos_existentes = os.listdir(caminho_download)
    if arquivos_existentes:
        _, ext = os.path.splitext(arquivos_existentes[0])
        if ext: extensao_esperada = ext
            
    caminho_arquivo_antigo = os.path.join(caminho_download, novo_nome_base + extensao_esperada)
    if os.path.exists(caminho_arquivo_antigo):
        os.remove(caminho_arquivo_antigo)
        print(f"  - Arquivo antigo '{os.path.basename(caminho_arquivo_antigo)}' removido.")

    # 2. Tira uma "foto" dos arquivos existentes antes do download
    arquivos_antes = set(os.listdir(caminho_download))
    
    # Clica para exportar
    clicar_elemento_com_tentativas(driver, (By.XPATH, "(//button[@title='Ações'])"))
    time.sleep(2)
    clicar_elemento_com_tentativas(driver, (By.CSS_SELECTOR, "body > div.app-menu-container-wrapper > div > div > button:nth-child(2)"))

    # 3. Aguarda de forma inteligente pelo novo arquivo
    print("Aguardando a conclusão do download de forma robusta...")
    tempo_limite = 300
    tempo_inicial = time.time()
    arquivo_baixado = None
    
    while time.time() - tempo_inicial < tempo_limite:
        arquivos_agora = set(os.listdir(caminho_download))
        novos_arquivos = arquivos_agora - arquivos_antes
        
        # Filtra para encontrar arquivos que não são temporários
        arquivos_finais = [f for f in novos_arquivos if not f.endswith('.crdownload') and not f.endswith('.tmp')]
        
        if len(arquivos_finais) == 1:
            nome_arquivo_novo = arquivos_finais[0]
            caminho_completo_novo = os.path.join(caminho_download, nome_arquivo_novo)
            # Confirma que o arquivo terminou de ser escrito (tamanho > 0)
            if os.path.getsize(caminho_completo_novo) > 0:
                arquivo_baixado = caminho_completo_novo
                print(f"  - Novo arquivo detectado: '{nome_arquivo_novo}'")
                break
        
        time.sleep(1)

    if not arquivo_baixado:
        raise TimeoutException("Download não foi concluído ou o novo arquivo não foi detectado no tempo limite.")

    # 4. Renomeia com precisão
    _, extensao = os.path.splitext(arquivo_baixado)
    novo_nome = novo_nome_base + extensao
    novo_caminho = os.path.join(caminho_download, novo_nome)
    
    shutil.move(arquivo_baixado, novo_caminho)
    print(f"Arquivo renomeado/sobrescrito com sucesso para: {novo_nome}")


def main():
    # ... (código existente)
    alvos = ["COI", "FISC"]
    driver = None
    try:
        driver = configurar_driver(CAMINHO_DOWNLOAD)
        fazer_login(driver, USUARIO_SIGA, SENHA_SIGA)
        for alvo in alvos:
            print(f"\n--- INICIANDO EXTRAÇÃO PARA {alvo} ---")
            if alvo == "COI":
                navegar_para_area(driver, LOCATOR_BOTÃO_COI, LOCATOR_BOTÃO_SUL_COI, "COI SUL")
                configurar_filtros_e_visualizacao(driver, alvo)
                exportar_e_renomear_arquivo(driver, CAMINHO_DOWNLOAD, "prod_coi", alvo)
            elif alvo == "FISC":
                navegar_para_area(driver, LOCATOR_BOTÃO_FISC, LOCATOR_BOTÃO_SUL_FISC, "FISC SUL")
                configurar_filtros_e_visualizacao(driver, alvo)
                exportar_e_renomear_arquivo(driver, CAMINHO_DOWNLOAD, "prod_fisc", alvo)
            print(f"--- EXTRAÇÃO PARA {alvo} CONCLUÍDA ---")
        print("\n✅ Todos os processos foram concluídos com sucesso!")
    except Exception as e:
        print(f"\n❌ Ocorreu um erro inesperado: {e}")
        if driver:
            screenshot_path = os.path.join(CAMINHO_RAIZ_PROJETO, "erro_debug.png")
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot salvo em: {screenshot_path}")
    finally:
        if driver:
            print("Fechando o navegador...")
            driver.quit()

if __name__ == "__main__":
    main()