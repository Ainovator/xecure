from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from datetime import datetime
from app.models import User, ReportAccessRequest, UserActionLog
from . import db
from app.extensions import redis_client
from app.routes.auth_routes import auth


@auth.route('/profile')
@login_required
def profile():
    """
    Страница профиля пользователя. 
    Отображает информацию о запросах и последние действия пользователя.
    """
    # Проверка токена пользователя
    token = request.cookies.get('auth_token')  # Извлечение токена из куков
    if not token:
        flash('Отсутствует токен. Войдите снова.', 'error')
        return redirect(url_for('auth.login'))

    user_id = redis_client.get(f"user_token:{token}")
    if not user_id:
        flash('Токен истёк. Войдите снова.', 'error')
        return redirect(url_for('auth.login'))

    # Запросы, ожидающие одобрения
    active_requests = ReportAccessRequest.query.filter_by(
        user_id=current_user.id,
        approved=False
    ).all()

    # Одобренные запросы с действующим сроком действия
    approved_requests = ReportAccessRequest.query.filter_by(
        user_id=current_user.id,
        approved=True
    ).filter(ReportAccessRequest.access_expiration > datetime.utcnow()).all()

    # Логи действий пользователя (последние 5 записей)
    logs_user = (
        UserActionLog.query.filter_by(user_id=user_id)
        .order_by(UserActionLog.timestamp.desc())
        .limit(5)
        .all()
    )

    # Данные пользователя
    user = User.query.get(int(user_id))

    return render_template(
        'profile.html',
        user=user,
        active_requests=active_requests,
        approved_requests=approved_requests,
        logs_user=logs_user
    )

