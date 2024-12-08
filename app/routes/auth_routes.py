from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from . import db
from app.extensions import redis_client
from uuid import uuid4
from app.utils import log_user_action

auth = Blueprint('auth', __name__)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Регистрация нового пользователя.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Пароли не совпадают!', category='error')
            return render_template('signup.html')

        # Проверка наличия пользователя с таким же именем
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Пользователь с таким именем уже существует!', category='error')
        else:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Аккаунт успешно создан!', category='success')
            return redirect(url_for('auth.login'))

    return render_template('signup.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Авторизация пользователя.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash('Неверное имя пользователя или пароль.', 'error')
            return render_template('login.html')

        # Успешный вход
        log_user_action(user.id, "Успешный вход в сессию")
        login_user(user)

        # Генерация токена
        token = str(uuid4())
        print(token)
        if user.role != 'admin':
            redis_client.setex(f"user_token:{token}", timedelta(seconds=60), user.id)  # TTL = 60 секунд
        else:
            redis_client.set(f"user_token:{token}", user.id)  # Без истечения для администратора

        # Установка токена в куки
        response = make_response(redirect(url_for('auth.profile')))
        response.set_cookie('auth_token', token, httponly=True, samesite='Lax')  # Убрано secure=True
        flash('Вы успешно вошли!', 'success')
        return response

    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    """
    Выход из системы.
    """
    # Логирование действия выхода
    log_user_action(current_user.id, "Успешный выход из сессии")

    # Разлогинивание пользователя
    logout_user()
    flash('Вы успешно вышли из системы.', 'success')

    # Перенаправление на главную страницу
    return redirect(url_for('home'))
