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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), nullable=False)
    access_expiration = db.Column(db.DateTime, nullable=False)
    approved = db.Column(db.Boolean, default=False)


    def __repr__(self):
        return f'<ReportAccessRequest user_id={self.user_id}, report_id={self.report_id}>'

    






