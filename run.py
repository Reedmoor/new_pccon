from app import create_app, db

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Создание всех моделей базы данных."""
    db.create_all()
    print("База данных инициализирована.")

if __name__ == '__main__':
    app.run(debug=True) 