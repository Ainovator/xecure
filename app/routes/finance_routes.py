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
    # Получение параметра фильтрации из строки запроса
    report_type = request.args.get('type')
    
    # Если параметр фильтра указан, фильтруем отчёты по типу
    if report_type:
        reports = Report.query.filter_by(type_report=report_type).all()
    else:
        reports = Report.query.all()  # Если фильтра нет, возвращаем все отчёты
    
    return render_template('finance.html', user=current_user, reports=reports)

