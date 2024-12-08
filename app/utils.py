from . import db 
from app.models import UserActionLog

def log_user_action(user_id, action):
    log_entry = UserActionLog(user_id=user_id, action=action)
    db.session.add(log_entry)
    db.session.commit()