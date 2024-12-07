from app import create_app

app = create_app()

if __name__ == "__main__":
    print(app.url_map)  # Вывод карты маршрутов
    app.debug = True  # Включает отладочный режим
    app.run(host="0.0.0.0", port=5000)
