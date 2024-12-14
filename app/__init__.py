from flask import Flask, render_template
from app.extensions import db, login_manager, redis_client, init_redis
from flask_migrate import Migrate
from app.routes.auth_routes import auth
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.models import *

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.xecure'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.from_pyfile('../config.py', silent=True)  # Загружаем конфигурацию из config.py, если он существует

    # Инициализация базы данных
    db.init_app(app)
    migrate = Migrate(app, db)
    admin = Admin(app, name='My Admin Panel', template_mode='bootstrap4')
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Report, db.session))


    # Включение поддержки внешних ключей в SQLite
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")  
            cursor.close()

    # Инициализация менеджера входа
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Перенаправлять неавторизованных пользователей на страницу входа
    login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к личному кабинету."
    login_manager.login_message_category = "info"

    # Инициализация Redis
    init_redis(app)

    # Глобальный маршрут для главной страницы
    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/signup')
    def signup():
        return render_template('signup.html')

    # Регистрация Blueprints
    app.register_blueprint(auth)

    # Создание таблиц в базе данных, если они не существуют
    with app.app_context():
        db.create_all()

    return app
