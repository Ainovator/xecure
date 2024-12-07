from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import redis
from flask import current_app
import redis

redis_client = redis.StrictRedis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

db = SQLAlchemy()
login_manager = LoginManager()


def init_redis(app):
    global redis_client
    redis_client = redis.StrictRedis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB'],
        decode_responses=app.config['REDIS_DECODE_RESPONSES']
    )