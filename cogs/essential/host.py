import os,requests
from dotenv import load_dotenv

load_dotenv()
square_token = os.getenv("square_token") #acessa e define o token da square cloud
discloud_token = os.getenv("discloud_token") #acessa e define o token da square cloud

appid = None
host = None

if square_token:
    host = "squarecloud"
if discloud_token:
    host = "discloud"

def obter_nome_bot():
    global host
    if host == "discloud":
        caminho = "discloud.config"
        return ler_arquivo(caminho, host)
    elif host == "squarecloud":
        caminho = "squarecloud.app"
        return ler_arquivo(caminho, host)
    else:
        raise ValueError("Host desconhecido.")

def ler_arquivo(caminho, host):
    if not os.path.exists(caminho):
        return None
    
    name_value = None
    id_value = None
    
    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            if host == "squarecloud" and linha.startswith("DISPLAY_NAME="):
                return linha.strip().split("=", 1)[1]
            if host == "discloud":
                if linha.startswith("ID="):
                    id_value = linha.strip().split("=", 1)[1]
                elif linha.startswith("NAME="):
                    name_value = linha.strip().split("=", 1)[1]
    
    if host == "discloud":
        return id_value if id_value else name_value
        
    return None

async def appname():
    global appid
    global host
    if appid is None:
        if host is None:
            print("🤖 - Nenhum token de Host encontrado. Verifique o .env")
            return None
        
        nome = obter_nome_bot()
        if not nome:
            print("🤖 - Nome ou ID do bot não encontrado nos arquivos de config.")
            return None

        print(f"🤖 - Usando a hospedagem da {host}")
        if host == "squarecloud":
            busca = requests.get("https://api.squarecloud.app/v2/users/me", headers={"Authorization": square_token})
            if busca.status_code == 200:
                aplicativos = busca.json().get("response", {}).get("applications", [])
                for app in aplicativos:
                    nome_app = app.get("name", "").lower()
                    if nome_app.startswith(nome.lower()):
                        appid = app["id"]
                        return app["id"]
        if host == "discloud":
            cleaned_nome = nome.replace(".discloud.app", "").strip()
            busca = requests.get("https://api.discloud.app/v2/user", headers={"api-token": discloud_token})
            if busca.status_code == 200:
                aplicativos = busca.json().get("user", {}).get("apps", [])
                
                # 1. Checa ID exato
                for aid in aplicativos:
                    if aid.lower() == cleaned_nome.lower():
                        appid = aid
                        return appid
                
                # 2. Busca por nome contido
                for aid in aplicativos:
                    app = requests.get(f"https://api.discloud.app/v2/app/{aid}", headers={"api-token": discloud_token})
                    if app.status_code == 200:
                        app_name = app.json().get("apps", {}).get("name", "").lower()
                        if cleaned_nome.lower() in app_name:
                            appid = aid
                            return appid
    else:
        return appid
    return None

async def informação():
    global host
    retorno = await appname()
    if not retorno: return None, host
    try:
        if host == "squarecloud":
            res_information = requests.get(f"https://api.squarecloud.app/v2/apps/{retorno}", headers={"Authorization": square_token})
            return res_information.json(), host
        if host == "discloud":
            res_information = requests.get(f"https://api.discloud.app/v2/app/{retorno}", headers={"api-token": discloud_token})
            return res_information.json(), host
    except:
        return None, None

async def status():
    global host
    retorno = await appname()
    if not retorno: return None, host
    try:
        if host == "squarecloud":
            res_status = requests.get(f"https://api.squarecloud.app/v2/apps/{retorno}/status", headers={"Authorization": square_token})
            return res_status.json(), host
        if host == "discloud":
            res_status = requests.get(f"https://api.discloud.app/v2/app/{retorno}/status", headers={"api-token": discloud_token})
            return res_status.json(), host
    except:
        return None, None

async def restart():
    global host
    retorno = await appname()
    if not retorno: return None, host
    try:
        if host == "squarecloud":
            res_status = requests.post(f"https://api.squarecloud.app/v2/apps/{retorno}/restart", headers={"Authorization": square_token})
            return res_status.json(), host
        if host == "discloud":
            res_status = requests.put(f"https://api.discloud.app/v2/app/{retorno}/restart", headers={"api-token": discloud_token})
            return res_status.json(), host
    except:
        return None, None