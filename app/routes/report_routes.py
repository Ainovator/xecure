from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import timedelta, datetime
from app.models import *
from . import db
from app.routes.auth_routes import auth
from .admin_routes import admin_required
from app.utils import log_user_action
import json


# Вспомогательные функции
def remove_expired_requests():
    """
    Удаляет все просроченные запросы на доступ, срок действия которых истёк.
    """
    expired_requests = ReportAccessRequest.query.filter(
        ReportAccessRequest.access_expiration < datetime.utcnow(),
        ReportAccessRequest.approved == False
    ).all()
    for request in expired_requests:
        db.session.delete(request)
    db.session.commit()


def get_existing_access_request(user_id, report_id):
    """
    Возвращает существующий запрос доступа для пользователя и отчёта.
    """
    return ReportAccessRequest.query.filter_by(user_id=user_id, report_id=report_id).first()


# Маршруты
@auth.route('/create_report', methods=['GET', 'POST'])
@login_required
@admin_required
def create_report():
    """
    Создание нового отчёта. Только для администратора.
    """
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        type = request.form.get('type')
        lvl_report = request.form.get('lvl')
        new_report = Report(title=title, content=content, user_id=current_user.id, type_report = type, lvl = lvl_report)
        db.session.add(new_report)
        db.session.commit()

        log_user_action(current_user.id, f'Создан отчёт: {title}')
        flash('Отчёт успешно создан.', 'success')
        return redirect(url_for('auth.admin_panel'))

    return render_template('create_report.html')


@auth.route('/approve_report/<int:report_id>', methods=['POST'])
@login_required
@admin_required
def approve_report(report_id):
    """
    Одобрение запроса на доступ к отчёту.
    """
    report = Report.query.get(report_id)
    if not report:
        flash('Отчёт не найден.', 'error')
        return redirect(url_for('auth.admin_panel'))

    access_duration = request.form.get('access_duration', 86400)  # 1 день по умолчанию
    try:
        access_duration = int(access_duration)
        if access_duration <= 0:
            raise ValueError
    except ValueError:
        flash('Некорректное время доступа. Укажите положительное число.', 'error')
        return redirect(url_for('auth.admin_panel'))

    access_expiration = datetime.utcnow().replace(microsecond=0) + timedelta(seconds=access_duration)
    remove_expired_requests()

    access_request = ReportAccessRequest.query.filter_by(report_id=report.id, approved=False).first()
    if access_request:
        access_request.approved = True
        access_request.access_expiration = access_expiration
        db.session.commit()

        log_user_action(current_user.id, f'Одобрение доступа к отчёту "{report.title}"')
        log_user_action(access_request.user_id, f'Доступ к отчёту "{report.title}" предоставлен')
        flash(f'Доступ к отчёту предоставлен на {access_duration} секунд.', 'success')
    else:
        flash('Запрос на доступ не найден.', 'error')

    return redirect(url_for('auth.admin_panel'))


@auth.route('/request_access/<int:report_id>', methods=['POST'])
@login_required
def request_access(report_id):
    """
    Запрос доступа к отчёту. Пользователь может отправить запрос, если он не отклонён.
    """
    report = Report.query.get(report_id)
    if not report:
        flash('Отчёт не найден.', 'error')
        return redirect(url_for('auth.finance'))

    rejected_request = RejectedRequest.query.filter_by(user_id=current_user.id, report_id=report.id).first()
    if rejected_request:
        flash('Ваш запрос отклонён. Повторный запрос невозможен.', 'error')
        return redirect(url_for('auth.finance'))

    existing_request = get_existing_access_request(current_user.id, report.id)
    if existing_request:
        if existing_request.access_expiration < datetime.utcnow().replace(microsecond=0):
            db.session.delete(existing_request)
            db.session.commit()
        else:
            flash('Ваш запрос уже ожидает одобрения.', 'info')
            return redirect(url_for('auth.finance'))

    access_expiration = datetime.utcnow().replace(microsecond=0) + timedelta(hours=24)
    request_purpose = request.form.get('request_reason')
    new_request = ReportAccessRequest(
        user_id=current_user.id,
        report_id=report.id,
        access_expiration=access_expiration,
        request_purpose = request_purpose
    )
    db.session.add(new_request)
    db.session.commit()

    log_user_action(current_user.id, f'Отправлен запрос на доступ к отчёту: {report.title}')
    flash('Ваш запрос отправлен. Ожидайте одобрения.', 'success')
    return redirect(url_for('auth.finance'))


@auth.route('/reject_request/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def reject_request(request_id):
    """
    Отклонение запроса на доступ к отчёту. Только для администратора.
    """
    access_request = ReportAccessRequest.query.get(request_id)
    if not access_request:
        flash('Запрос на доступ не найден.', 'error')
        return redirect(url_for('auth.admin_panel'))

    rejected_request = RejectedRequest(
        user_id=access_request.user_id,
        report_id=access_request.report_id
    )
    db.session.add(rejected_request)
    db.session.delete(access_request)
    db.session.commit()

    report = Report.query.get(rejected_request.report_id)
    log_user_action(current_user.id, f'Запрос на доступ к отчёту "{report.title}" отклонён')
    flash('Запрос отклонён.', 'success')
    return redirect(url_for('auth.admin_panel'))


@auth.route('/rejected_requests', methods=['GET'])
@login_required
def rejected_requests():
    """
    Просмотр отклонённых запросов для текущего пользователя.
    """
    rejections = RejectedRequest.query.filter_by(user_id=current_user.id).all()
    return render_template('rejected_requests.html', rejections=rejections)


@auth.route('/view_report/<int:report_id>', methods=['GET'])
@login_required
def view_report(report_id):
    """
    Просмотр отчёта, если доступ к нему был одобрен.
    """
    access_request = get_existing_access_request(current_user.id, report_id)
    if not access_request:
        flash('Вы не запрашивали доступ к этому отчёту.', 'error')
        return redirect(url_for('auth.finance'))

    if access_request.access_expiration < datetime.utcnow().replace(microsecond=0):
        db.session.delete(access_request)
        db.session.commit()
        flash('Срок действия доступа истёк. Запросите доступ снова.', 'error')
        return redirect(url_for('auth.finance'))

    report = Report.query.get(report_id)
    return render_template('view_report.html', report=report)



# Эндпоинт для изменения отчёта
@auth.route('/report/<int:report_id>', methods=['POST'])
def update_report(report_id):
    # Получение данных из формы
    title = request.form.get('title')
    content = request.form.get('content')

    # Проверяем существование отчёта
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404

    # Сохраняем старые данные для логирования
    old_data = {"title": report.title, "content": report.content}

    # Обновляем данные отчёта
    report.title = title
    report.content = content

    # Логируем изменения
    change_summary = {
        "old_data": old_data,
        "new_data": {"title": title, "content": content}
    }


    # Создание записи в логах изменений
    change_log = ReportChangeLog(
        report_id=report.id,
        user_id=current_user.id,  # Используем текущего пользователя
        changed_at=datetime.utcnow().replace(microsecond=0),
        change_summary=json.dumps(change_summary)  # Преобразование в JSON
    )

    # Добавляем лог изменений в базу данных
    db.session.add(change_log)
    db.session.commit()

    return redirect(url_for('auth.view_report', report_id=report_id))


@auth.route('/report/<int:report_id>/history', methods=['GET'])
@login_required
@admin_required
def report_history(report_id):
    """
    Просмотр истории изменений отчёта.
    """
    report = Report.query.get(report_id)
    if not report:
        flash('Отчёт не найден.', 'error')
        return redirect(url_for('auth.admin_panel'))

    history = ReportChangeLog.query.filter_by(report_id=report_id).all()

    for log in history:
        try:
            log.change_summary_parsed = json.loads(log.change_summary)  # Парсим JSON
        except json.JSONDecodeError:
            log.change_summary_parsed = {"error": "Некорректный формат изменений"}

    return render_template('report_history.html', report=report, history=history)


@auth.route('/reports', methods=['GET'])
@login_required
def reports():
    """
    Отображение списка отчетов с фильтрацией по типу.
    """
    report_type = request.args.get('type', '')  # Получаем тип отчета из параметров запроса
    if report_type:
        reports = Report.query.filter_by(type_report=report_type).all()
    else:
        reports = Report.query.all()

    return render_template('reports.html', reports=reports)
