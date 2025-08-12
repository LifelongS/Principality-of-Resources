# shared/config.py

import os
from datetime import timedelta

class Config:
    # --- Общие настройки ---
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a-very-secret-key-needs-to-be-set')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True

    # --- Настройки JWT ---
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback-super-secret-key-please-change')

    # --- Настройки RabbitMQ ---
    RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')

    # --- URL других сервисов ---
    AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL', 'http://localhost:5000')
    GAME_SERVICE_URL = os.environ.get('GAME_SERVICE_URL', 'http://localhost:5001')

    # --- Настройки Swagger (Общие, если нужны) ---
    SWAGGER_HOST = 'localhost' # Базовый хост для Swagger
    SWAGGER_TITLE = "Game Project API"
    SWAGGER_VERSION = "1.0.0"
    # Можно добавить другие общие настройки SWAGGER_*

    # --- Порт по умолчанию (будет переопределен в дочерних классах) ---
    PORT = None

class AuthConfig(Config):
    """Конфигурация для AuthService."""
    _basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'auth_service'))
    _instance_path = os.path.join(_basedir, 'instance')
    os.makedirs(_instance_path, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(_instance_path, 'users.db')}"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    PORT = 5000 # Явно указываем порт для AuthService
    SWAGGER_DESCRIPTION = "Authentication Service API" # Описание для Auth

class GameConfig(Config):
    """Конфигурация для GameService."""
    _basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'game_service'))
    _instance_path = os.path.join(_basedir, 'instance')
    os.makedirs(_instance_path, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(_instance_path, 'game.db')}"
    PORT = 5001 # Явно указываем порт для GameService
    SWAGGER_DESCRIPTION = "Game Logic Service API" # Описание для Game