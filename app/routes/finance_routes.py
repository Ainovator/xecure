from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta, datetime

from app.models import *
from app.extensions import db, redis_client
from app.routes.auth_routes import auth


@auth.route('/finance', methods=['GET'])
@login_required
def finance():
    # Получаем параметры из строки запроса
    report_type = request.args.get('type')  # Тип отчёта (может быть пустым или "Все")
    user_lvl = current_user.lvl  # Уровень доступа текущего пользователя

    # Базовый запрос: фильтруем отчёты по уровню доступа
    query = Report.query.filter(Report.lvl <= user_lvl)

    if report_type and report_type != "Все":  # Если тип отчёта указан и он не "Все"
        query = query.filter(Report.type_report == report_type)

    reports = query.all()  # Выполняем запрос

    return render_template('finance.html', user=current_user, reports=reports)


