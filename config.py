import os
import redis

# Настройки Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_DECODE_RESPONSES = True

SECRET_KEY = os.environ.get('SECRET_KEY', 'xecuresecretkey')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///db.xecure')
SQLALCHEMY_TRACK_MODIFICATIONS = False
