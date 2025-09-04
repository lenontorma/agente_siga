from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import time
from dotenv import load_dotenv

# --- 1. CONFIGURAÇÃO INICIAL ---

# Carrega as variáveis do arquivo .env
load_dotenv()
USUARIO_SIGA = os.getenv("USUARIO_SIGA")
SENHA_SIGA = os.getenv("SENHA_SIGA")

# Configurações do Chrome para um driver mais "limpo" (sem logs no console)
service = Service(log_path=os.devnull)
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Descomente esta linha se não quiser ver o navegador abrir
driver = webdriver.Chrome(service=service, options=chrome_options)

url = "https://equatorialenergia.etadirect.com/"
driver.get(url)
print(f"Acessando a URL: {url}")


# --- 2. LÓGICA DE AUTOMAÇÃO COM TRATAMENTO DE ERROS ---

try:
    # --- Login ---
    campo_usuario = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="username"]'))
    )
    campo_usuario.send_keys(USUARIO_SIGA)
    campo_senha = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="password"]'))
    )
    campo_senha.send_keys(SENHA_SIGA)
    botao_login = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="sign-in"]/div/span/span'))
    )
    botao_login.click()

    # --- Cliques Pós-Login ---
    print("Login bem-sucedido. Aguardando o primeiro botão após o login...")
    botao_coi = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="manage-content"]/div[1]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[1]/div[1]/button[1]'))
    )
    botao_coi.click()
    print("Clicou no primeiro botão.")

    print("Aguardando o próximo elemento...")
    proximo_elemento = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="manage-content"]/div[1]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]'))
    )
    proximo_elemento.click()
    print("Clicou no segundo elemento.")

    print("\n✅ Automação concluída com sucesso!")


except TimeoutException:
    print("\n❌ ERRO: Tempo de espera excedido.")
    print("Um dos elementos não foi encontrado ou a página demorou muito para carregar.")
    # Você pode adicionar aqui uma captura de tela para depuração, se quiser:
    # driver.save_screenshot("erro_screenshot.png")

except Exception as e:
    print(f"\n❌ Ocorreu um erro inesperado: {e}")


finally:
    # --- 3. FINALIZAÇÃO ---
    print("Fechando o navegador em 5 segundos...")
    time.sleep(5)  # Pequena pausa para ver o resultado final
    driver.quit()