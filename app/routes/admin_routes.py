from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Report, ReportAccessRequest
from . import db, login_manager  
from app.extensions import redis_client  
from flask import jsonify
from functools import wraps
from datetime import timedelta, datetime
from app.routes.auth_routes import auth


def admin_required(f):
    """
    Декоратор для ограничения доступа только для администраторов.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Вы должны войти в систему для доступа к этой странице.', 'error')
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            flash('У вас нет доступа к этой странице.', 'error')
            abort(403)  # Генерация ошибки 403
        return f(*args, **kwargs)
    return decorated_function


@auth.route('/admin_panel', methods=['GET', 'POST'])
@login_required
@admin_required  # Только администратор может получить доступ к этой панели
def admin_panel():
    users = User.query.all()  # Получаем всех пользователей
    reports = Report.query.all()  # Получаем все отчёты

    # Удаление отчёта, если это POST-запрос с report_id
    if request.method == 'POST':
        report_id = request.form.get('report_id')
        report_to_delete = Report.query.get(report_id)
        if report_to_delete:
            db.session.delete(report_to_delete)
            db.session.commit()
            flash('Отчёт успешно удалён.', 'success')
        else:
            flash('Отчёт не найден.', 'error')

        return redirect(url_for('auth.admin_panel'))

    return render_template('admin_panel.html', users=users, reports=reports)



@auth.route('/delete_user', methods=['POST'])
@login_required
@admin_required  # Проверка на роль администратора
def delete_user():
    user_id = request.form.get('user_id')
    user_to_delete = User.query.get(user_id)

    if user_to_delete:
        # Проверяем, что админ не удаляет себя
        if user_to_delete.username == current_user.username:
            flash('Вы не можете удалить свой собственный аккаунт.', 'error')
            return redirect(url_for('auth.admin_panel'))

        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Пользователь {user_to_delete.username} успешно удален.', 'success')
    else:
        flash('Пользователь не найден.', 'error')

    return redirect(url_for('auth.admin_panel'))

 