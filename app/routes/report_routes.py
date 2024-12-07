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
from .admin_routes import admin_required


@auth.route('/create_report', methods=['GET', 'POST'])
@login_required
@admin_required  # Только администратор может создавать отчеты
def create_report():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        # Создаем новый отчет
        new_report = Report(title=title, content=content, user_id=current_user.id)
        db.session.add(new_report)
        db.session.commit()

        flash('Отчет успешно создан.', 'success')
        return redirect(url_for('auth.admin_panel'))  # Перенаправляем на страницу админ-панели

    return render_template('create_report.html') 


@auth.route('/approve_report/<int:report_id>', methods=['POST'])
@login_required
@admin_required  # Только администратор может одобрить доступ
def approve_report(report_id):
    report = Report.query.get(report_id)
    if not report:
        flash('Отчет не найден.', 'error')
        return redirect(url_for('auth.admin_panel'))

    # Получаем время доступа в секундах из формы
    access_duration = request.form.get('access_duration', 60)  # Время в секундах (по умолчанию 60 секунд)
    access_expiration = datetime.utcnow() + timedelta(seconds=int(access_duration))  # Рассчитываем дату окончания доступа

    # Находим запрос на доступ
    access_request = ReportAccessRequest.query.filter_by(report_id=report.id, approved=False).first()
    if access_request:
        access_request.approved = True
        access_request.access_expiration = access_expiration  # Обновляем время окончания доступа
        db.session.commit()
        flash(f'Отчет был одобрен и доступ предоставлен на {access_duration} секунд.', 'success')
    else:
        flash('Запрос на доступ не найден.', 'error')

    return redirect(url_for('auth.admin_panel'))  # Перенаправляем на админ-панель

@auth.route('/request_access/<int:report_id>', methods=['POST'])
@login_required
def request_access(report_id):
    report = Report.query.get(report_id)
    if not report:
        flash('Отчет не найден.', 'error')
        return redirect(url_for('auth.finance'))

    # Проверяем, есть ли уже запрос на этот отчет от этого пользователя
    existing_request = ReportAccessRequest.query.filter_by(user_id=current_user.id, report_id=report.id).first()
    if existing_request:
        flash('Вы уже запросили доступ к этому отчету.', 'info')
        return redirect(url_for('auth.finance'))

    # Устанавливаем время доступа (например, 24 часа)
    access_expiration = datetime.utcnow() + timedelta(hours=24)

    # Создаем запрос на доступ
    new_request = ReportAccessRequest(
        user_id=current_user.id,
        report_id=report.id,
        access_expiration=access_expiration
    )
    db.session.add(new_request)
    db.session.commit()

    flash('Ваш запрос на доступ к отчету отправлен. Ожидайте одобрения.', 'success')
    return redirect(url_for('auth.finance'))


@auth.route('/view_report/<int:report_id>', methods=['GET'])
@login_required
def view_report(report_id):
    # Проверяем, есть ли у пользователя запрос на доступ к этому отчету
    access_request = ReportAccessRequest.query.filter_by(user_id=current_user.id, report_id=report_id).first()

    if not access_request or not access_request.approved:
        flash('Вы не можете просматривать этот отчет. Ваш запрос еще не одобрен или срок действия доступа истек.', 'error')
        return redirect(url_for('auth.finance'))

    # Проверяем, не истек ли срок действия доступа
    if access_request.access_expiration < datetime.utcnow():
        flash('Время доступа к отчету истекло. Пожалуйста, запросите доступ снова.', 'error')
        
        # Удаляем или деактивируем доступ, так как время истекло
        access_request.approved = False
        db.session.commit()
        
        return redirect(url_for('auth.finance'))

    # Если доступ еще актуален, отображаем отчет
    report = Report.query.get(report_id)
    return render_template('view_report.html', report=report)
