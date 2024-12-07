from flask import Flask, render_template
from app.extensions import db, login_manager
from app.routes import auth
from app.extensions import redis_client, init_redis
from flask_migrate import Migrate
from app.routes.auth_routes import auth


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.xecure'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.from_pyfile('../config.py')

    db.init_app(app)
    migrate = Migrate(app, db)

    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Перенаправлять неавторизованных пользователей на регистрацию
    login_manager.login_message = "Пожалуйста, зарегистрируйтесь, чтобы получить доступ к личному кабинету."
    login_manager.login_message_category = "info"

    # Инициализация Redis
    init_redis(app)

    # Глобальный маршрут для главной страницы
    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/signup')
    def signup():
        return render_template('signup.html')

    # Регистрация других Blueprints
    app.register_blueprint(auth)

    with app.app_context():
        db.create_all()

    return app
