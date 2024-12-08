from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Report, ReportAccessRequest
from . import db, login_manager  
from app.extensions import redis_client  
from uuid import uuid4
from flask import jsonify
from functools import wraps
from datetime import timedelta, datetime
from app.utils import log_user_action

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Пароли не совпадают!', category='error')
            return render_template('signup.html')

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
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Неверное имя пользователя или пароль.', 'error')
            return render_template('login.html')

        if not check_password_hash(user.password, password):
            flash('Неверное имя пользователя или пароль.', 'error')
            return render_template('login.html')

    
        user_id = user.id
        log_user_action(user.id, "Успешный вход в сессию")

        
        login_user(user)

        # Генерация токена
        token = str(uuid4())
        
        if user.role != 'admin':
            redis_client.setex(f"user_token:{token}", 60, user.id)  # TTL = 20 секунд
        else:
            redis_client.set(f"user_token:{token}", user.id)  

        flash('Вы успешно вошли!', 'success')
        return redirect(url_for('auth.profile', token=token))

    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    # Получаем user.id из current_user
    user_id = current_user.id

    # Логируем действие до разлогинивания
    log_user_action(user_id, "Успешный выход из сессии")

    # Разлогиниваем пользователя
    logout_user()

    # Перенаправляем на главную страницу
    return redirect(url_for('home'))
