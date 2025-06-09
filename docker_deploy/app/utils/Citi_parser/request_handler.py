import requests
import time
import logging

def request(url, query, variables, name_request):
    while True:
        try:
            logging.info(f"Отправка запроса к {url}, для получения данных об {name_request}")
            response = requests.post(url=url, json={"query": query, "variables": variables})
            if response.status_code == 200:
                logging.info("Запрос успешно выполнен")
                return response.json()
            elif response.status_code == 429:
                logging.warning("Слишком много запросов. Ожидание перед повторной попыткой...")
                time.sleep(5)
            else:
                logging.error(f"Ошибка HTTP: {response.status_code}, Ответ: {response.text}")
        except Exception as e:
            logging.error(f"Произошла ошибка при выполнении запроса: {str(e)}")
            raise