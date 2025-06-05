import subprocess
import sys
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
import time


# Função para pedir credenciais e criar o arquivo .env se necessário
def pedir_credenciais_custom():
    env_path = Path(".env")

    # Carrega variáveis (se existirem)
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    email_salvo = os.getenv("SAP_EMAIL", "")
    senha_salva = os.getenv("SAP_SENHA", "")

    # Se já existem e estão preenchidas, sai fora — nada de janela
    if email_salvo and senha_salva:
        return

    # Caso contrário, precisa preencher pela primeira vez
    root = tk.Tk()
    root.withdraw()

    login_win = tk.Toplevel()
    login_win.title("Login SAPBot")
    login_win.geometry("300x150")
    login_win.resizable(False, False)

    tk.Label(login_win, text="Email:").pack(pady=5)
    email_entry = tk.Entry(login_win, width=30)
    email_entry.pack()
    email_entry.insert(0, email_salvo)

    tk.Label(login_win, text="Senha:").pack(pady=5)
    senha_entry = tk.Entry(login_win, width=30, show='*')
    senha_entry.pack()
    senha_entry.insert(0, senha_salva)

    def salvar_e_sair():
        email = email_entry.get()
        senha = senha_entry.get()
        if not email or not senha:
            messagebox.showerror("Erro", "Preencha ambos os campos.", parent=login_win)
            return
        with open(".env", "w") as f:
            f.write(f"SAP_EMAIL={email}\nSAP_SENHA={senha}")
        login_win.destroy()
        root.destroy()

    tk.Button(login_win, text="Entrar", command=salvar_e_sair).pack(pady=10)

    # Se os campos já estão preenchidos (primeira vez), salva e fecha sozinho
    if email_salvo and senha_salva:
        login_win.after_idle(salvar_e_sair)

    login_win.mainloop()


# Carregamento inicial das credenciais
pedir_credenciais_custom()

# Recarrega .env para garantir que está atualizado
load_dotenv()
email = os.getenv("SAP_EMAIL")
senha = os.getenv("SAP_SENHA")

if not email or not senha:
    raise ValueError("Email ou senha não encontrados no arquivo .env")


# Configurações do WebDriver
options = webdriver.ChromeOptions()
# options.add_argument("--headless")
navegador = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def fazer_login():
    try:
        navegador.get("https://me.sap.com/processnavigator/SolS/EARL_SolS-013/2408?region=BR")
        navegador.maximize_window()

        # Preenche o email
        campo_email = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.ID, "j_username"))
        )
        campo_email.send_keys(email)

        # Espera o botão continuar aparecer no DOM
        botao_continuar = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                ".ids-button.fn-button.ids-button--primary.fn-button--emphasized.ids-button--login.js-button-login"))
        )

        # Scroll até o botão
        navegador.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            botao_continuar
        )

        # Espera o botão estar clicável depois do scroll
        WebDriverWait(navegador, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                ".ids-button.fn-button.ids-button--primary.fn-button--emphasized.ids-button--login.js-button-login"))
        )

        # Clica no botão continuar
        botao_continuar.click()

        # botao cookies
        botao_cookies = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.ID,
                "truste-consent-button"))
        )
        #Clica no botao cookies
        botao_cookies.click()

        # Preenche a senha
        input_senha = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        input_senha.send_keys(senha)

        # Clica no botão de login final
        botao_login_final = WebDriverWait(navegador, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign in')]"))
        )

        # Scroll até ele
        navegador.execute_script(
        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
        botao_login_final
        )

# Clica
        botao_login_final.click()

        time.sleep(60)

        print('✅ Logado com sucesso')

    except Exception as e:
        print(f"❌ Erro ao fazer login: {e}")
        navegador.quit()
        sys.exit(1)




def obter_driver_logado():
    try:
        fazer_login()
        return navegador
    except Exception as e:
        print(f"❌ Erro ao obter driver logado: {e}")
        navegador.quit()
        return None

