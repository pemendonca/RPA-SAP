import os
import time
import hashlib
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from inserir_processos import inserir_processo

# Configuração de pasta de downloads
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Configurar Selenium
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})
chrome_options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(), options=chrome_options)
wait = WebDriverWait(driver, 20)

def hash_arquivo(caminho):
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def aguardar_download():
    print("⏳ Aguardando download...")
    tempo_limite = time.time() + 30
    while time.time() < tempo_limite:
        arquivos = os.listdir(DOWNLOAD_DIR)
        arquivos = [f for f in arquivos if f.endswith(".pdf")]
        if arquivos:
            caminho = os.path.join(DOWNLOAD_DIR, arquivos[0])
            if not caminho.endswith(".crdownload"):
                return caminho
        time.sleep(1)
    raise Exception("❌ Timeout ao aguardar download")

def acessar_processo_e_baixar(link_processo, nome_processo, id_externo, versao, pais):
    driver.get(link_processo)

    try:
        aba = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Aceleradores"]')))
        aba.click()

        time.sleep(2)  # pequena espera para carregar a aba

        botao_idioma = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[contains(@id,"internalBtn-inner")]')))
        botao_idioma.click()

        item_portugues = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(text(),"Portuguese")]')))
        item_portugues.click()

        caminho_pdf = aguardar_download()
        hash_pdf = hash_arquivo(caminho_pdf)

        inserir_processo(nome_processo, id_externo, link_processo, versao, pais, hash_pdf)
        print(f"✔️ Download e inserção concluídos: {nome_processo}")

    except Exception as e:
        print(f"⚠️ Erro ao processar {nome_processo}: {str(e)}")

def iniciar():
    driver.get("https://me.sap.com/processnavigator")  # Ou a URL completa da tela inicial logada

    input("🔐 Faça login manualmente e pressione ENTER para continuar...")

    setores = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//li[@role="treeitem"]')))

    for setor in setores:
        try:
            expander = setor.find_element(By.CLASS_NAME, "sapMTreeItemBaseExpander")
            expander.click()
            time.sleep(1)

            processos = driver.find_elements(By.XPATH, '//a[contains(@class,"sapMLnkEmphasized")]')
            for processo in processos:
                nome_completo = processo.text
                link_processo = processo.get_attribute("href")
                id_externo = nome_completo.split("(")[-1].replace(")", "").strip()
                nome_processo = nome_completo.replace(f"({id_externo})", "").strip()

                acessar_processo_e_baixar(link_processo, nome_processo, id_externo, "2023", "Brazil")

        except Exception as e:
            print(f"Erro ao processar setor: {e}")
            continue

    print("🎯 Concluído.")
    driver.quit()

if __name__ == "__main__":
    iniciar()
