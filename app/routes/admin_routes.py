from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models import User, Report, ReportAccessRequest, UserActionLog
from . import db
from app.routes.auth_routes import auth
from functools import wraps


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
            abort(403)  # Генерация ошибки 403 (доступ запрещён)
        return f(*args, **kwargs)
    return decorated_function


@auth.route('/admin_panel', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_panel():
    """
    Панель администратора: управление пользователями, отчётами и запросами доступа.
    """
    users = User.query.all()  # Список всех пользователей
    reports = Report.query.all()  # Список всех отчётов
    access_requests = ReportAccessRequest.query.all()  # Список всех запросов доступа

    # Обработка удаления отчёта
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

    return render_template('admin_panel.html', users=users, reports=reports, requests=access_requests)


@auth.route('/delete_user', methods=['POST'])
@login_required
@admin_required
def delete_user():
    """
    Удаление пользователя из системы. Доступно только администраторам.
    """
    user_id = request.form.get('user_id')
    user_to_delete = User.query.get(user_id)

    if user_to_delete:
        # Проверка на удаление собственного аккаунта
        if user_to_delete.username == current_user.username:
            flash('Вы не можете удалить свой собственный аккаунт.', 'error')
            return redirect(url_for('auth.admin_panel'))

        # Удаление связанных логов перед удалением пользователя
        UserActionLog.query.filter_by(user_id=user_id).delete()

        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Пользователь {user_to_delete.username} успешно удалён.', 'success')
    else:
        flash('Пользователь не найден.', 'error')

    return redirect(url_for('auth.admin_panel'))
