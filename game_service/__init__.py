# game_service/__init__.py


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
# import logging # Логгирование здесь не используется напрямую
from datetime import datetime
import jinja2

# Импортируем правильную конфигурацию и функцию инициализации Swagger
from shared.config import GameConfig
from shared.swagger_config import init_swagger

db = SQLAlchemy()

def create_app(config_class=GameConfig):
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    # Загружаем конфигурацию ИЗ GameConfig (включая PORT=5001, SWAGGER_DESCRIPTION и т.д.)
    app.config.from_object(config_class)

    # Настройка загрузчика шаблонов
    service_templates = os.path.join(app.root_path, app.template_folder)
    shared_templates = os.path.abspath(os.path.join(app.root_path, '..', 'shared', 'templates'))
    app.jinja_loader = jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(service_templates),
        jinja2.FileSystemLoader(shared_templates),
    ])

    # Инициализация расширений
    db.init_app(app)

    # Инициализация Swagger
    # init_swagger(app) прочитает app.config (включая PORT) и настроит все сама
    init_swagger(app)


    # Регистрация blueprint'ов
    from .routes import game_bp
    app.register_blueprint(game_bp)

    # Создание таблиц БД (лучше использовать Alembic/Flask-Migrate для управления)
    with app.app_context():
        # Убедитесь, что модели импортированы ДО db.create_all()
        from . import models # Пример импорта моделей, если они определены в models.py
        db.create_all()

    # Добавление глобальных переменных/функций в Jinja
    app.jinja_env.globals['now'] = datetime.utcnow

    return app