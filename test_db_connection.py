import psycopg2
try:
    conn = psycopg2.connect(
        host="localhost",
        database="uipc",
        user="postgres",
        password="123456"  # пароль указан как 123456
    )
    print("Подключение к базе данных успешно!")
    # Пробуем выполнить простой запрос
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    print(f"Результат запроса: {result}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Ошибка при подключении к базе данных: {e}") 