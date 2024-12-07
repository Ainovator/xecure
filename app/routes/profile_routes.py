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
from app.routes.auth_routes import auth

@auth.route('/profile')
@login_required
def profile():
    token = request.args.get('token')
    print(f"Token received: {token}")  # Отладка

    if not token:
        print("No token provided")  # Отладка
        flash('Отсутствует токен. Войдите снова.', 'error')
        return redirect(url_for('auth.login'))

    user_id = redis_client.get(f"user_token:{token}")
    print(f"User ID from token: {user_id}")  # Отладка

    if not user_id:
        print("Token expired or invalid")  # Отладка
        flash('Токен истёк. Войдите снова.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.get(int(user_id))
    return render_template('profile.html', user=user)