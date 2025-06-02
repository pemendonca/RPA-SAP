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


# Função para pedir credenciais e criar o arquivo .env se necessário
def pedir_credenciais_custom():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    ico_path = os.path.join(base_path, "favicon.ico")

    root = tk.Tk()
    root.withdraw()

    login_win = tk.Toplevel()
    login_win.title("Login SAPBot")
    # login_win.iconbitmap(ico_path)
    login_win.geometry("300x150")
    login_win.resizable(False, False)

    tk.Label(login_win, text="Email:").pack(pady=5)
    email_entry = tk.Entry(login_win, width=30)
    email_entry.pack()

    tk.Label(login_win, text="Senha:").pack(pady=5)
    senha_entry = tk.Entry(login_win, width=30, show='*')
    senha_entry.pack()

    def salvar_e_sair():
        email = email_entry.get()
        senha = senha_entry.get()
        if not email or not senha:
            messagebox.showerror("Erro", "Preencha ambos os campos.", parent=login_win)
            return
        with open(".env", "w") as f:
            f.write(f"SAP_EMAIL={email}\nSAP_SENHA={senha}")
        messagebox.showinfo("Sucesso", "Credenciais salvas!", parent=login_win)
        login_win.destroy()
        root.destroy()

    tk.Button(login_win, text="Entrar", command=salvar_e_sair).pack(pady=10)

    login_win.mainloop()

# Verificar se o .env existe, caso contrário pedir credenciais
env_path = Path(".env")
if not env_path.exists() or not os.getenv("WISE_EMAIL") or not os.getenv("WISE_SENHA"):
    pedir_credenciais_custom()

# Carregar as credenciais do .env
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
        navegador.get("https://accounts.sap.com/saml2/idp/sso")
        navegador.maximize_window()

        # Preenche o email
        campo_email = WebDriverWait(navegador, 10).until(EC.presence_of_element_located((By.ID, "username")))
        campo_email.send_keys(email)

        # Continua para a senha
        campo_continuar = WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.ID, "kc-login")))
        campo_continuar.click()

        # Preenche a senha
        input_senha = WebDriverWait(navegador, 10).until(EC.presence_of_element_located((By.ID, "password")))
        input_senha.send_keys(senha)

        # Finaliza o login
        campo_continuar_dois = WebDriverWait(navegador, 10).until(EC.element_to_be_clickable((By.NAME, "login")))
        campo_continuar_dois.click()

        # Verifica se o login foi bem-sucedido
        WebDriverWait(navegador, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "styles__ComplementsSelectBox-sc-1qitxh9-1"))
        )
        print('✅ Logado com sucesso')

        # Captura dos cookies após o login bem-sucedido
                # Captura dos cookies após o login bem-sucedido
        cookies = navegador.get_cookies()

        # Filtra apenas os cookies desejados
        cookies_desejados = [c for c in cookies if c["name"] in ["DeimosSID", "DeimosSub", "DeimosCSRF"]]

        with open("cookies.json", "w") as f:
            json.dump(cookies_desejados, f)
        print("✅ Cookies filtrados salvos em cookies.json")

    except Exception as e:
        print(f"❌ Erro ao fazer login: {e}")
        navegador.quit()
        sys.exit(1)

def carregar_cookies():
    try:
        with open("cookies.json", "r") as f:
            cookies = json.load(f)
        # Converte para o formato esperado pelo requests
        return {cookie["name"]: cookie["value"] for cookie in cookies}
    except FileNotFoundError:
        print("❌ Arquivo cookies.json não encontrado. Faça login primeiro.")
        return None

def enviar_reserva(cadeira_id, data_inicio, horario_inicio, data_fim, horario_fim):
    url = f"https://accounts.sap.com/saml2/idp/sso{cadeira_id}"
    
    # Montando o payload
    payload = {
        "idsUsuariosConvidados": [37859],
        "visitantes": [],
        "dataInicio": f"{data_inicio} {horario_inicio}",
        "dataFim": f"{data_fim} {horario_fim}",
        "descricao": None,
        "idUsuarioRepresentado": None,
        "tituloReuniao": None,
        "agora": False
    }

    # Carregando os cookies
    cookies = carregar_cookies()
    if not cookies:
        print("❌ Não foi possível carregar os cookies.")
        return
    
    # Headers para a request
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://app.wiseoffices.com.br",
        "Referer": "https://app.wiseoffices.com.br/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }

    # Enviando a request
    response = requests.post(url, json=payload, headers=headers, cookies=cookies)

    if response.status_code == 201:
        print("✅ Reserva criada com sucesso!")
        messagebox.showinfo("Reserva Confirmada", "Reserva criada com sucesso!")
    else:
        print(f"❌ Falha ao criar reserva: {response.status_code}")
        print(response.text)
        messagebox.showerror("Erro", f"Falha ao criar reserva: {response.status_code}")

def abrir_interface():
    # Mapeamento de nomes amigáveis para IDs
    CADEIRAS_IDS = {
        "Cabine 2": "7638",
        "Sala de entrevista": "7623",
        "Sala 2": "7632",
        "Sala 1": "7630",
        "Cabine 1": "7637"
    }

    def on_confirmar():
        try:
            # Corrigindo o formato de data e hora
            data_inicio = datetime.strptime(data_inicio_var.get(), "%d/%m/%Y").strftime("%Y-%m-%d")
            horario_inicio = datetime.strptime(horario_inicio_var.get(), "%H:%M").strftime("%H:%M")
            horario_fim = datetime.strptime(horario_fim_var.get(), "%H:%M").strftime("%H:%M")
        except ValueError:
            messagebox.showerror("Erro", "Formato de data ou hora inválido.")
            return

        cadeira_nome = cadeira_var.get()
        cadeira_id = CADEIRAS_IDS[cadeira_nome]
        
        enviar_reserva(cadeira_id, data_inicio, horario_inicio, data_inicio, horario_fim)

    # Configurações da janela principal
    root = tk.Tk()
    root.title("Login SAP")
    root.geometry("350x350")
    root.resizable(False, False)

    # Campos do Tkinter
    tk.Label(root, text="Cadeira:").pack(pady=5)
    cadeira_var = tk.StringVar(value=list(CADEIRAS_IDS.keys())[0])
    cadeira_menu = ttk.Combobox(root, textvariable=cadeira_var, values=list(CADEIRAS_IDS.keys()), state="readonly", width=30)
    cadeira_menu.pack()

    tk.Label(root, text="Data de Início (DD/MM/AAAA):").pack(pady=5)
    data_inicio_var = tk.Entry(root, width=30)
    data_inicio_var.pack()

    tk.Label(root, text="Horário de Início (HH:MM):").pack(pady=5)
    horario_inicio_var = tk.Entry(root, width=30)
    horario_inicio_var.pack()

    tk.Label(root, text="Horário de Fim (HH:MM):").pack(pady=5)
    horario_fim_var = tk.Entry(root, width=30)
    horario_fim_var.pack()

    tk.Button(root, text="Confirmar Reserva", command=on_confirmar).pack(pady=20)

    root.mainloop()


def main():
    try:
        fazer_login()
      
    except Exception as e:
        print(f"❌ Erro no fluxo principal: {e}")
    finally:
        navegador.quit()

if __name__ == "__main__":
    main()
