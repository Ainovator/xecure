from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

# Создаем приложение и контекст
app = create_app()
app.app_context().push()

# Данные пользователя
username = 'admin'
password = '12'
role = 'admin'

# Хешируем пароль
hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

# Создаем пользователя и добавляем в базу данных
admin_user = User(username=username, password=hashed_password, role=role)
db.session.add(admin_user)
db.session.commit()

print(f"Пользователь {username} с ролью {role} успешно создан.")
