STACK:

python 3.12 + flask;
redis;
sqlite;

УСТАНОВКА И ЗАПУСК ВИРТУАЛЬНОЙ СРЕДЫ:

python3 -m venv .venv
source ./.venv/bin/activate

ЗАПУСК ПРОЕКТА:

python3 wsgi.py --host 0.0.0.0 --port 5000 (порт на выбор, можно 80, если открыт для доступа по http://localhost)

УСТАНОВКА ЗАВИСИМОСТЕЙ:

pip install flask
pip install flask_sqlalchemy
pip install flask_login
pip install flask_migrate
pip install flask_admin==1.6.1
pip install redis

ЗАПУСК МИГРАЦИЙ:

flask db update

ИНИЦИАЛИЗАЦИЯ DB

flask db init