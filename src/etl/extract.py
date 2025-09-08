from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException # Importa a nova exceção
import os
import time
import shutil
from dotenv import load_dotenv

# --- (Suas constantes e configurações de caminho continuam as mesmas) ---
load_dotenv()
USUARIO_SIGA = os.getenv("USUARIO_SIGA")
SENHA_SIGA = os.getenv("SENHA_SIGA")
# ... resto das constantes ...
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

# --- NOVA FUNÇÃO AJUDANTE ---
def clicar_elemento_com_tentativas(driver, locator, tentativas=3, timeout=15):
    """
    Tenta encontrar e clicar em um elemento. Se encontrar StaleElementReferenceException,
    tenta novamente até o limite de tentativas.
    """
    for tentativa in range(tentativas):
        try:
            # A cada tentativa, ele REENCONTRA o elemento, garantindo que não está "vencido"
            elemento = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            elemento.click()
            return # Se o clique for bem-sucedido, sai da função
        except StaleElementReferenceException:
            print(f"  [AVISO] Elemento 'vencido' encontrado na tentativa {tentativa + 1}/{tentativas}. Tentando novamente...")
            time.sleep(1) # Pequena pausa antes de tentar de novo
    # Se todas as tentativas falharem, lança uma exceção
    raise TimeoutException(f"Não foi possível clicar no elemento {locator} após {tentativas} tentativas devido a StaleElementReferenceException.")


# --- (As funções configurar_driver e fazer_login continuam as mesmas) ---
def configurar_driver(caminho_download):
    # ... (código existente)
    print(f"Configurando downloads para a pasta: {caminho_download}")
    if not os.path.exists(caminho_download):
        os.makedirs(caminho_download)
        print(f"Pasta de download criada em: {caminho_download}")

    chrome_options = Options()
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
    # ... (código existente)
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
    # ... (código existente)
    print(f"Navegando para a área '{nome_da_area}'...")
    botao_principal = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(locator_principal))
    botao_principal.click()
    print(f"Clicou no botão principal de '{nome_da_area}'.")
    time.sleep(3)
    botao_secundario = WebDriverWait(driver, 15).until(EC.element_to_be_clickable(locator_secundario))
    botao_secundario.click()
    print(f"Navegou com sucesso para a sub-área de '{nome_da_area}'.")


# --- FUNÇÃO ATUALIZADA PARA USAR O NOVO MÉTODO DE CLIQUE ---
def configurar_filtros_e_visualizacao(driver, alvo_atual):
    """Aplica os filtros e configurações de visualização, com lógica condicional para a checkbox."""
    print("Configurando filtros e visualização...")

    # Usando a nova função para o primeiro clique, que é o ponto do erro
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


# --- (As funções exportar_e_renomear_arquivo e main continuam as mesmas) ---
def exportar_e_renomear_arquivo(driver, caminho_download, novo_nome_base, alvo_atual):
    # ... (código existente)
    print("Iniciando processo de exportação...")
    if alvo_atual == "FISC":
        try:
            print("Alvo é FISC. Verificando se o botão 'Ações' está visível e clicável...")
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "(//button[@title='Ações'])")))
            print("Botão 'Ações' encontrado e clicável para FISC.")
        except TimeoutException:
            print("[AVISO] Botão 'Ações' não está disponível para FISC. Provavelmente não há dados para exportar.")
            print("Pulando etapa de download para FISC.")
            return
            
    botao_acoes = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "(//button[@title='Ações'])")))
    botao_acoes.click()
    time.sleep(2)
    exportar = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "body > div.app-menu-container-wrapper > div > div > button:nth-child(2)")))
    exportar.click()
    print("Aguardando a conclusão do download...")
    tempo_limite = 300
    tempo_inicial = time.time()
    while True:
        if time.time() - tempo_inicial > tempo_limite:
            raise Exception("Tempo de espera para o download excedido!")
        arquivos_temp = [f for f in os.listdir(caminho_download) if f.endswith('.crdownload')]
        if not arquivos_temp:
            print("Download concluído!")
            break
        time.sleep(1)
    time.sleep(2) 
    lista_de_arquivos = [os.path.join(caminho_download, f) for f in os.listdir(caminho_download) if os.path.isfile(os.path.join(caminho_download, f))]
    if not lista_de_arquivos:
        if alvo_atual == "FISC":
            print("[AVISO] Nenhum arquivo foi baixado após clicar em exportar.")
            return
        else:
            raise Exception("Nenhum arquivo encontrado na pasta de download.")
    arquivo_mais_recente = max(lista_de_arquivos, key=os.path.getctime)
    print(f"Arquivo mais recente encontrado: {os.path.basename(arquivo_mais_recente)}")
    _, extensao = os.path.splitext(arquivo_mais_recente)
    novo_nome = novo_nome_base + extensao
    novo_caminho = os.path.join(caminho_download, novo_nome)
    shutil.move(arquivo_mais_recente, novo_caminho)
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
    except TimeoutException:
        print("\n❌ ERRO: Tempo de espera excedido. Um elemento não foi encontrado a tempo.")
        if driver:
            screenshot_path = os.path.join(CAMINHO_RAIZ_PROJETO, "erro_debug.png")
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot salvo em: {screenshot_path}")
    except Exception as e:
        print(f"\n❌ Ocorreu um erro inesperado: {e}")
    finally:
        if driver:
            print("Fechando o navegador...")
            driver.quit()

if __name__ == "__main__":
    main()