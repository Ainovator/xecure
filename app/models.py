from flask_login import UserMixin
from . import db
from datetime import datetime, timedelta

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default="user")

    def has_requested_access(self, report_id):
        request = ReportAccessRequest.query.filter_by(user_id=self.id, report_id=report_id).first()
        return request is not None

    def has_access_to_report(self, report_id):
        request = ReportAccessRequest.query.filter_by(user_id=self.id, report_id=report_id).first()
        return request and request.approved and request.access_expiration > datetime.utcnow()

    def has_rejected_access(self, report_id):
        from .models import RejectedRequest  # Избегаем циклического импорта
        rejected_request = RejectedRequest.query.filter_by(user_id=self.id, report_id=report_id).first()
        return rejected_request is not None

    def __repr__(self):
        return f'<User {self.username}>'


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('reports', lazy=True))

    access_requests = db.relationship(
        'ReportAccessRequest',
        backref='parent_report', 
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Report {self.title}>'


class ReportAccessRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),  # Удаление пользователя удаляет запросы доступа
        nullable=False
    )
    report_id = db.Column(
        db.Integer,
        db.ForeignKey('report.id', ondelete='CASCADE'),  # Удаление отчёта удаляет запросы доступа
        nullable=False
    )
    access_expiration = db.Column(db.DateTime, nullable=False)
    approved = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='access_requests', lazy=True)

    def __repr__(self):
        return f'<ReportAccessRequest user_id={self.user_id}, report_id={self.report_id}>'



class RejectedRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(
        db.Integer,
        db.ForeignKey('report.id', ondelete='CASCADE', name='fk_rejected_request_report_id'),
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE', name='fk_rejected_request_user_id'),
        nullable=False
    )
    rejected_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='rejected_requests', lazy=True)
    report = db.relationship('Report', backref='rejected_requests', lazy=True)

    def __repr__(self):
        return f'<RejectedRequest user_id={self.user_id}, report_id={self.report_id}>'







