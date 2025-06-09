import requests
import json
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Отключаем предупреждения о незащищенном соединении
urllib3.disable_warnings(InsecureRequestWarning)

# Первый запрос для получения токена
url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

payload = {
    'scope': 'GIGACHAT_API_PERS'
}
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json',
    'RqUID': 'af37cb18-f569-442c-8540-46165f646b24',
    'Authorization': 'Basic MjZjYjAwNzUtZTllZS00YjkxLWJlOGEtYjk5N2FjMzA3ZjBmOjQ3ZTVmZmM4LTJiZGQtNDU1OC1iNDdkLTBiZmJmZDNmNWI4Ng=='
}

response = requests.request("POST", url, headers=headers, data=payload, verify=False)
auth_data = json.loads(response.text)
access_token = auth_data['access_token']

# Получаем список моделей
models_url = "https://gigachat.devices.sberbank.ru/api/v1/models"
headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}'
}

response = requests.request("GET", models_url, headers=headers, verify=False)
models_data = json.loads(response.text)

# Выбираем нужную модель (например, GigaChat-2)
model_id = "GigaChat-2"

# Теперь можно сделать запрос к конкретной модели
chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
payload = {
    "model": model_id,
    "messages": [{"role": "user", "content": ""}]
}

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}'
}

response = requests.request("POST", chat_url, headers=headers, json=payload, verify=False)
print(response.text)