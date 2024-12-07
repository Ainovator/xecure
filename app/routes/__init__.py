#Импорты python
from flask import Flask, render_template
from flask_migrate import Migrate

#Глобальные импорты
from app.extensions import db, login_manager
from app.extensions import redis_client, init_redis
from app.models import User

#Локальные импорты
from .admin_routes import *
from .auth_routes import *
from .finance_routes import *
from .profile_routes import *
from .report_routes import *
from .routes import *




@login_manager.user_loader
def load_user(user_id):
    """
    Загрузка пользователя Flask-Login по его ID.
    """
    return User.query.get(int(user_id))  # Загружаем пользователя из базы данных по ID




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Загружаем пользователя из базы данных по ID