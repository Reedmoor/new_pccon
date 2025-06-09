import json
import os
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_gigachat.embeddings import GigaChatEmbeddings
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from gigachat import GigaChat

# Отключаем предупреждения о незащищенном соединении
urllib3.disable_warnings(InsecureRequestWarning)

def main():
    # Список документов, по которым будет выполняться поиск
    documents = [
        Document(
            page_content="Собаки — отличные компаньоны, которые известны своей преданностью и дружелюбием.",
            metadata={"source": "mammal-pets-doc"},
        ),
        Document(
            page_content="Кошки — независимые животные, которым нужно собственное пространство.",
            metadata={"source": "mammal-pets-doc"},
        ),
        Document(
            page_content="Золотые рыбки — отличные домашние животные для начинающих. За ними достаточно просто ухаживать.",
            metadata={"source": "fish-pets-doc"},
        ),
        Document(
            page_content="Попугаи — умные птицы, которые способны имитировать человеческую речь.",
            metadata={"source": "bird-pets-doc"},
        ),
        Document(
            page_content="Кролики — социальные животные, которым нужно много места, чтобы прыгать.",
            metadata={"source": "mammal-pets-doc"},
        ),
    ]

    try:
        print("Инициализация GigaChat клиента...")
        
        # Настройка переменных окружения для GigaChat с новым ключом
        os.environ["GIGACHAT_CREDENTIALS"] = "MjZjYjAwNzUtZTllZS00YjkxLWJlOGEtYjk5N2FjMzA3ZjBmOjQ3ZTVmZmM4LTJiZGQtNDU1OC1iNDdkLTBiZmJmZDNmNWI4Ng=="
        os.environ["GIGACHAT_SCOPE"] = "GIGACHAT_API_PERS"
        
        # Создаем экземпляр модели эмбеддингов для LangChain
        embeddings_model = GigaChatEmbeddings(
            credentials=os.environ["GIGACHAT_CREDENTIALS"],
            scope=os.environ["GIGACHAT_SCOPE"],
            verify_ssl_certs=False
        )
        
        # Тестируем получение эмбеддингов
        print("Тестирование получения эмбеддингов...")
        test_embeddings = embeddings_model.embed_documents(["Тестовый запрос для проверки соединения"])
        print(f"Эмбеддинги получены успешно! Размер эмбеддинга: {len(test_embeddings[0])}")
        
        # Создаем векторное хранилище
        print("Создание векторного хранилища...")
        vectorstore = Chroma.from_documents(
            documents,
            embedding=embeddings_model,
        )
        
        # Выполняем поиск
        print("\nРезультаты поиска по запросу 'кошка':")
        results = vectorstore.similarity_search("кошка")
        for doc in results:
            print(f"- {doc.page_content} (источник: {doc.metadata['source']})")
            
    except Exception as e:
        print(f"Ошибка при работе с эмбеддингами: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
