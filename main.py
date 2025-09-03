from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os

service = Service(log_path=os.devnull)
chrome_options = Options()
driver = webdriver.Chrome(service=service, options=chrome_options)

url = "https://equatorialenergia.etadirect.com/"
driver.get(url)
