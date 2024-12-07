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
from app.extensions import login_manager






@auth.route('/check-session', methods=['GET'])
@login_required
def check_session():
    user_id = current_user.get_id()
    token = redis_client.get(f"user_session:{user_id}")

    if not token:
        logout_user()
        return jsonify({'message': 'Session expired'}), 401

    return jsonify({'message': 'Session active'}), 200





