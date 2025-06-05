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
from logger import registrar_log  # logger.py está na raiz

# Configuração da pasta de downloads
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Configuração do Selenium: configura os prefs para download
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
    registrar_log("⏳ Aguardando download...")
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

def expandir_setor_por_nome(nome_setor):
    try:
        # Busca o elemento pelo texto exato do setor
        xpath_setor = f'//span[text()="{nome_setor}"]'
        elemento = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_setor)))
        elemento.click()
        registrar_log(f"✅ Setor expandido: {nome_setor}")
        time.sleep(1)  # tempo para o setor expandir
    except Exception as e:
        registrar_log(f"❌ Erro ao expandir setor '{nome_setor}': {str(e)}")

def acessar_processo_e_baixar(link_processo, nome_processo, id_externo, versao, pais):
    driver.get(link_processo)
    registrar_log(f"Iniciando processamento do processo: {nome_processo}")

    try:
        # Clica na aba "Aceleradores"
        aba_aceleradores = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="Aceleradores"]')))
        aba_aceleradores.click()
        registrar_log("✅ Aba 'Aceleradores' clicada")
        
        time.sleep(2)  # Aguarda a renderização da aba
        
        # Clica no botão seletor de idioma (que abre o dropdown)
        botao_idioma = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[contains(@id,"internalBtn-inner")]')))
        botao_idioma.click()
        registrar_log("✅ Botão de idioma clicado")
        
        # Seleciona a opção "Portuguese"
        item_portugues = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(text(),"Portuguese")]')))
        item_portugues.click()
        registrar_log("✅ Idioma 'Portuguese' selecionado")
        
        # Aguarda o download ocorrer
        caminho_pdf = aguardar_download()
        hash_pdf = hash_arquivo(caminho_pdf)
        registrar_log(f"✅ Arquivo baixado e hash calculado: {hash_pdf}")
        
        # Envia dados para o Supabase
        inserir_processo(nome_processo, id_externo, link_processo, versao, pais, hash_pdf)
        registrar_log(f"✔️ Download e inserção concluídos: {nome_processo}")

    except Exception as e:
        registrar_log(f"⚠️ Erro ao processar {nome_processo}: {str(e)}")

def iniciar():
    # Abre a URL diretamente, como você já configurou essa tela no seu login
    driver.get("https://me.sap.com/processnavigator/SolS/EARL_SolS-013/2408?region=BR")
    input("🔐 Faça login no SAP se ainda não estiver logado e pressione ENTER para continuar...")

    # Lista de setores desejados (pode ser ajustada conforme necessário)
    setores_desejados = [
        "Application Platform and Infrastructure",
        "Asset Management"  # Adicione outros setores conforme sua necessidade
    ]

    for setor in setores_desejados:
        expandir_setor_por_nome(setor)
        time.sleep(1)  # tempo para os processos aparecerem

        # Seleciona todos os processos que estão visíveis com base na classe identificadora
        processos = driver.find_elements(By.XPATH, '//a[contains(@class,"sapMLnkEmphasized")]')
        registrar_log(f"Encontrados {len(processos)} processos no setor: {setor}")
        for processo in processos:
            nome_completo = processo.text
            link_processo = processo.get_attribute("href")
            # Extrai o ID com base no formato esperado, exemplo: "Processo Nome (2QU)"
            try:
                id_externo = nome_completo.split("(")[-1].replace(")", "").strip()
                nome_processo = nome_completo.replace(f"({id_externo})", "").strip()
            except Exception as e:
                registrar_log(f"⚠️ Erro ao extrair ID de: {nome_completo} - {str(e)}")
                continue

            # Chama a função que acessa o processo e baixa o PDF
            acessar_processo_e_baixar(link_processo, nome_processo, id_externo, "2408", "Brazil")

    registrar_log("🎯 Processo concluído. Encerrando navegador.")
    driver.quit()

if __name__ == "__main__":
    iniciar()
