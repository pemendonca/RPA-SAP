import requests
from datetime import datetime

SUPABASE_URL = "https://iuztasmoifbhgxxbcvra.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1enRhc21vaWZiaGd4eGJjdnJhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg5NzM1MzQsImV4cCI6MjA2NDU0OTUzNH0.GcIAY_SjbIW5a2yDKDpsplgGCfL2LSqLYsVtHNUQlS4"

def inserir_processo(nome, id_externo, url, versao, pais, hash_arquivo=None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "nome_processo": nome,
        "id_externo": id_externo,
        "url_download": url,
        "versao": versao,
        "pais": pais,
        "hash_arquivo": hash_arquivo,
        "ultima_atualizacao": datetime.now().isoformat()
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/processos_sap",
        headers=headers,
        json=payload
    )

    if response.status_code == 201:
        print(f"✔️ Sucesso ao inserir: {nome}")
    else:
        print(f"❌ Erro ao inserir: {response.status_code} - {response.text}")

# Exemplo de uso
if __name__ == "__main__":
    inserir_processo(
        nome="Business Event Handling",
        id_externo="1NN",
        url="https://exemplo.com/arquivo.pdf",
        versao="2023",
        pais="Brazil"
    )
