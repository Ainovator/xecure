from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta, datetime

from app.models import *
from app.extensions import db, redis_client
from app.routes.auth_routes import auth


@auth.route('/finance')
@login_required
def finance():
    reports = Report.query.all()  # Можно добавить кэширование с использованием Redis
    return render_template('finance.html', user=current_user, reports=reports)
