# swagger_config.py

# shared/swagger_config.py
from flasgger import Swagger
import os # Импортируем os, если его еще нет

def init_swagger(app):
    """
    Инициализация Swagger для Flask-приложения.
    Автоматически определяет host на основе конфигурации приложения.
    """
    # Определяем хост и порт
    # Сначала пытаемся взять SERVER_NAME, если он задан (например, 'mydomain.com' или 'localhost:5000')
    host = app.config.get('SERVER_NAME')

    # Если SERVER_NAME не задан, собираем хост из SWAGGER_HOST и PORT
    if not host:
        config_host = app.config.get('SWAGGER_HOST', 'localhost') # Можно задать базовый хост в конфиге
        port = app.config.get('PORT') # Берем порт из конфига приложения
        if port and port != 80 and port != 443: # Добавляем порт, если он не стандартный
             host = f"{config_host}:{port}"
        else:
             host = config_host

    # Формируем конфигурацию Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static", # Путь к статике Swagger UI
        "swagger_ui": True, # Включить Swagger UI
        "specs_route": "/apidocs/", # URL для Swagger UI

        # Динамически устанавливаем хост
        "host": host, # Используем определенный выше хост
        "basePath": "/", # Базовый путь для API

        # Остальные метаданные можно тоже брать из app.config при желании
        "info": {
            "title": app.config.get('SWAGGER_TITLE', "Game API Documentation"),
            "version": app.config.get('SWAGGER_VERSION', "1.0.0"),
            "description": app.config.get('SWAGGER_DESCRIPTION', "API documentation for Auth and Game services"),
            "termsOfService": app.config.get('SWAGGER_TERMS_URL', ""),
        },
        "securityDefinitions": {
            "JWT": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT authorization header using the Bearer scheme. Example: \"Bearer {token}\""
            }
        },
        # Можно добавить uiversion, если хотите конкретную версию UI
        # "uiversion": 3
    }

    # Инициализация Swagger с подготовленной конфигурацией
    Swagger(app, config=swagger_config)