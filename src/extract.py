from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import time
import shutil
from dotenv import load_dotenv

# --- 1. CONFIGURAÇÕES GLOBAIS E CONSTANTES ---

load_dotenv()
USUARIO_SIGA = os.getenv("USUARIO_SIGA")
SENHA_SIGA = os.getenv("SENHA_SIGA")

CAMINHO_SCRIPT = os.path.abspath(__file__)
DIRETORIO_SRC = os.path.dirname(CAMINHO_SCRIPT)
CAMINHO_RAIZ_PROJETO = os.path.dirname(DIRETORIO_SRC)
CAMINHO_DOWNLOAD = os.path.join(CAMINHO_RAIZ_PROJETO, "Data")

# --- DEFINIÇÃO DOS LOCATORS (ENDEREÇOS DOS ELEMENTOS) ---

# Locators para o fluxo COI
LOCATOR_BOTÃO_COI = (By.XPATH, '//*[@id="manage-content"]/div[1]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[1]/div[1]/button[1]')
LOCATOR_BOTÃO_SUL_COI = (By.XPATH, '//*[@id="manage-content"]/div[1]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]')

# Locators para o fluxo FISC
LOCATOR_BOTÃO_FISC = (By.XPATH, '//*[@id="manage-content"]/div[1]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[2]/div[1]/button[1]') 
LOCATOR_BOTÃO_SUL_FISC = (By.XPATH, '//*[@id="manage-content"]/div[1]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/div[3]/div[1]')


def configurar_driver(caminho_download):
    """Configura o WebDriver do Chrome com as opções de download e retorna a instância."""
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
    # chrome_options.add_argument("--headless")

    service = Service(log_path=os.devnull)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fazer_login(driver, usuario, senha):
    """Executa o processo de login na página."""
    url = "https://equatorialenergia.etadirect.com/"
    driver.get(url)
    print(f"Acessando a URL: {url}")
    
    print("Aguardando campo de usuário...")
    campo_usuario = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="username"]')))
    campo_usuario.send_keys(usuario)

    print("Aguardando campo de senha...")
    campo_senha = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))
    campo_senha.send_keys(senha)

    print("Clicando em 'Sign In'...")
    botao_login = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sign-in"]/div/span/span')))
    botao_login.click()
    print("Login bem-sucedido.")

def navegar_para_area(driver, locator_principal, locator_secundario, nome_da_area):
    """Função de navegação genérica que clica em dois botões em sequência."""
    print(f"Navegando para a área '{nome_da_area}'...")
    botao_principal = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(locator_principal)
    )
    botao_principal.click()
    print(f"Clicou no botão principal de '{nome_da_area}'.")
    time.sleep(3)
    
    botao_secundario = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable(locator_secundario)
    )
    botao_secundario.click()
    print(f"Navegou com sucesso para a sub-área de '{nome_da_area}'.")

def configurar_filtros_e_visualizacao(driver, alvo_atual):
    """Aplica os filtros e configurações de visualização, com lógica condicional para a checkbox."""
    print("Configurando filtros e visualização...")
    lista = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-ofsc-id='dc__top_panel__page_selector__list__btn']")))
    lista.click()
    time.sleep(3)
    print("Clicou em 'Visualização em Lista'.")
    
    exibir = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//button[@title='Exibir']")))
    exibir.click()
    time.sleep(2)
    
    # --- LÓGICA CONDICIONAL BASEADA NA SUA DICA ---
    if alvo_atual == "COI":
        print("Alvo é COI, aplicando o filtro hierárquico...")
        aplicar_hierarquica = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//label[.//oj-option[text()='Aplicar de forma hierárquica']]"))
        )
        aplicar_hierarquica.click()
        time.sleep(2)
    else:
        print("Alvo é FISC, pulando o clique no filtro hierárquico.")

    selecionar_hierarquica = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "(//button[@title='Aplicar'])[2]")))
    selecionar_hierarquica.click()
    print("Filtros e visualização aplicados.")

def exportar_e_renomear_arquivo(driver, caminho_download, novo_nome_base):
    """Clica em Ações, Exportar, aguarda o download e renomeia o arquivo."""
    time.sleep(2)
    print("Iniciando processo de exportação...")
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
        raise Exception("Nenhum arquivo encontrado na pasta de download.")
        
    arquivo_mais_recente = max(lista_de_arquivos, key=os.path.getctime)
    print(f"Arquivo mais recente encontrado: {os.path.basename(arquivo_mais_recente)}")
    
    _, extensao = os.path.splitext(arquivo_mais_recente)
    novo_nome = novo_nome_base + extensao
    novo_caminho = os.path.join(caminho_download, novo_nome)
    
    shutil.move(arquivo_mais_recente, novo_caminho)
    print(f"Arquivo renomeado/sobrescrito com sucesso para: {novo_nome}")


def main():
    """Função principal que orquestra a automação para MÚLTIPLOS ALVOS."""
    
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
                exportar_e_renomear_arquivo(driver, CAMINHO_DOWNLOAD, "prod_coi")

            elif alvo == "FISC":
                navegar_para_area(driver, LOCATOR_BOTÃO_FISC, LOCATOR_BOTÃO_SUL_FISC, "FISC SUL")
                configurar_filtros_e_visualizacao(driver, alvo)
                exportar_e_renomear_arquivo(driver, CAMINHO_DOWNLOAD, "prod_fisc")
            
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