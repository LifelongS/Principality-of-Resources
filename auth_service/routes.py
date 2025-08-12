# auth_service/routes.py

from flask import (
    Blueprint, render_template, request, jsonify, redirect, url_for, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
import logging
from flasgger import swag_from

from . import db
from .models import User
from shared.rabbitmq import send_message

auth_bp = Blueprint('auth', __name__, template_folder='../templates', static_folder='../static')
logger = logging.getLogger(__name__)

@auth_bp.route('/')
def index():
    """Перенаправление на страницу входа
    ---
    tags:
      - Pages
    responses:
      302:
        description: Redirect to login page
    """
    return redirect(url_for('auth.login'))

@auth_bp.route('/login')
def login():
    """Страница входа в систему
    ---
    tags:
      - Pages
    responses:
      200:
        description: Login page
    """
    return render_template('login.html')

@auth_bp.route('/register')
def register():
    """Страница регистрации
    ---
    tags:
      - Pages
    responses:
      200:
        description: Registration page
    """
    return render_template('register.html')

@auth_bp.route('/api/register', methods=['POST'])
@swag_from({
    'tags': ['Authentication'],
    'description': 'Регистрация нового пользователя',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'example': 'new_user'},
                    'password': {'type': 'string', 'example': 'secure_password123'}
                },
                'required': ['username', 'password']
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Успешная регистрация',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'redirect_url': {'type': 'string'}
                }
            }
        },
        400: {'description': 'Не указаны имя пользователя или пароль'},
        409: {'description': 'Пользователь уже существует'},
        500: {'description': 'Ошибка сервера'}
    }
})
def api_register():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    try:
        if User.query.filter_by(username=username).first():
            logger.warning(f"Registration attempt for existing user: {username}")
            return jsonify({'message': 'User already exists'}), 409

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User '{username}' (ID: {new_user.id}) registered successfully.")

        message_data = {
            'user_id': new_user.id,
            'username': new_user.username
        }
        send_message(queue_name='user_created', message_body=message_data)

        login_url = url_for('auth.login', _external=False)
        return jsonify({'message': 'User registered successfully', 'redirect_url': login_url}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during registration for user '{username}': {e}", exc_info=True)
        return jsonify({'message': 'Internal Server Error during registration'}), 500

@auth_bp.route('/api/login', methods=['POST'])
@swag_from({
    'tags': ['Authentication'],
    'description': 'Аутентификация пользователя',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'example': 'existing_user'},
                    'password': {'type': 'string', 'example': 'secure_password123'}
                },
                'required': ['username', 'password']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Успешный вход',
            'schema': {
                'type': 'object',
                'properties': {
                    'access_token': {'type': 'string'},
                    'redirect_url': {'type': 'string'}
                }
            }
        },
        400: {'description': 'Не указаны имя пользователя или пароль'},
        401: {'description': 'Неверные учетные данные'},
        500: {'description': 'Ошибка сервера'}
    }
})
def api_login():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    try:
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={'username': user.username}
            )
            logger.info(f"User '{username}' (ID: {user.id}) logged in. JWT issued.")

            game_service_base_url = current_app.config.get('GAME_SERVICE_URL', 'http://localhost:5001')
            game_url = f'{game_service_base_url}/game?token={access_token}'

            return jsonify({'access_token': access_token, 'redirect_url': game_url}), 200
        else:
            logger.warning(f"Failed login attempt for user: {username}")
            return jsonify({'message': 'Invalid username or password'}), 401

    except Exception as e:
        logger.error(f"Error during login for user '{username}': {e}", exc_info=True)
        return jsonify({'message': 'Internal Server Error during login'}), 500

@auth_bp.route('/logout')
def logout():
    """Выход из системы
    ---
    tags:
      - Authentication
    responses:
      302:
        description: Redirect to login page
    """
    login_url = url_for('auth.login', _external=False)
    return redirect(login_url)