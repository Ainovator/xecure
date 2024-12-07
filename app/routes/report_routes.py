from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import *
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

    # Проверяем, был ли запрос отклонён
    rejected_request = RejectedRequest.query.filter_by(
        user_id=current_user.id,
        report_id=report.id
    ).first()
    if rejected_request:
        flash('Ваш запрос был отклонён администратором. Вы не можете отправить повторный запрос.', 'error')
        return redirect(url_for('auth.finance'))

    # Удаляем истёкший запрос (если есть)
    existing_request = ReportAccessRequest.query.filter_by(
        user_id=current_user.id, report_id=report.id
    ).first()
    if existing_request and existing_request.access_expiration < datetime.utcnow():
        db.session.delete(existing_request)
        db.session.commit()

    # Проверяем, если запрос ещё активен
    if existing_request:
        flash('Ваш запрос уже ожидает одобрения.', 'info')
        return redirect(url_for('auth.finance'))

    # Создаём новый запрос
    access_expiration = datetime.utcnow() + timedelta(hours=24)
    new_request = ReportAccessRequest(
        user_id=current_user.id,
        report_id=report.id,
        access_expiration=access_expiration
    )
    db.session.add(new_request)
    db.session.commit()

    flash('Ваш запрос на доступ отправлен. Ожидайте одобрения.', 'success')
    return redirect(url_for('auth.finance'))



@auth.route('/reject_request/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def reject_request(request_id):
    # Находим запрос по ID
    access_request = ReportAccessRequest.query.get(request_id)
    if not access_request:
        flash('Запрос на доступ не найден.', 'error')
        return redirect(url_for('auth.admin_panel'))

    # Создаём запись об отклонении
    rejected_request = RejectedRequest(
        user_id=access_request.user_id,
        report_id=access_request.report_id
    )
    db.session.add(rejected_request)

    # Удаляем запрос из ReportAccessRequest
    db.session.delete(access_request)
    db.session.commit()

    flash('Запрос на доступ отклонён.', 'success')
    return redirect(url_for('auth.admin_panel'))

@auth.route('/rejected_requests', methods=['GET'])
@login_required
def rejected_requests():
    rejections = RejectedRequest.query.filter_by(user_id=current_user.id).all()
    return render_template('rejected_requests.html', rejections=rejections)




@auth.route('/view_report/<int:report_id>', methods=['GET'])
@login_required
def view_report(report_id):
    # Проверяем запрос доступа для текущего пользователя
    access_request = ReportAccessRequest.query.filter_by(user_id=current_user.id, report_id=report_id).first()

    if not access_request:
        flash('Вы не запрашивали доступ к этому отчету.', 'error')
        return redirect(url_for('auth.finance'))

    if access_request.access_expiration < datetime.utcnow():
        # Удаляем запрос, если срок действия истек
        db.session.delete(access_request)
        db.session.commit()
        flash('Срок действия доступа истек. Пожалуйста, запросите доступ снова.', 'error')
        return redirect(url_for('auth.finance'))

    # Если доступ активен, показываем отчет
    report = Report.query.get(report_id)
    return render_template('view_report.html', report=report)
