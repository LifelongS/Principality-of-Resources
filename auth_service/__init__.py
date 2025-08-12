# auth_service/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import os
import logging
import jinja2
from datetime import datetime

from shared.config import AuthConfig
from shared.swagger_config import init_swagger # Убедимся, что импорт правильный

db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_class=AuthConfig):
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    app.config.from_object(config_class) # Загружаем конфиг, включая PORT

    # Настройка загрузчика шаблонов
    service_templates = os.path.join(app.root_path, app.template_folder)
    shared_templates = os.path.abspath(os.path.join(app.root_path, '..', 'shared', 'templates'))
    app.jinja_loader = jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(service_templates),
        jinja2.FileSystemLoader(shared_templates),
    ])

    # Инициализация расширений
    db.init_app(app)
    jwt.init_app(app)

    # Инициализация Swagger
    # init_swagger берет PORT из app.config для настройки host
    init_swagger(app)


    # Регистрация blueprint'ов
    from .routes import auth_bp
    app.register_blueprint(auth_bp)

    # Создание таблиц (лучше делать это отдельно, например, через flask db migrate/upgrade)
    # Но если оставляем здесь:
    with app.app_context():
        db.create_all()

    app.jinja_env.globals['now'] = datetime.utcnow

    return app