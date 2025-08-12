# game_service/utils.py

import jwt
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

# Импортируем db и модели.
# utils.py импортируется только из run_game.py
# и routes.py, ПОСЛЕ того как __init__.py уже создал 'db'.
from . import db
from .models import Resources, Buildings

logger = logging.getLogger(__name__)

# --- Функция проверки JWT ---
def verify_jwt_token(token):
    try:
        secret_key = current_app.config['JWT_SECRET_KEY']
        decoded = jwt.decode(token, secret_key, algorithms=['HS256'])
        return decoded
    except jwt.ExpiredSignatureError:
        logger.warning("JWT verification failed: Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT verification failed: Invalid token - {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during JWT verification: {e}", exc_info=True)
        return None

# --- Функция-обработчик для сообщений 'user_created' ---
def process_user_created_message(message_data: dict):
    """
    Обрабатывает сообщение о создании пользователя.
    Вызывается из консьюмера RabbitMQ внутри app_context.

    Args:
        message_data: Словарь с данными из сообщения ('user_id', 'username').
    """
    try:
        user_id = message_data['user_id']
        username = message_data['username']

        # Проверяем, существуют ли уже данные для этого пользователя
        existing_resources = db.session.get(Resources, user_id)
        if not existing_resources:
            existing_buildings = db.session.get(Buildings, user_id)
            if not existing_buildings:
                logger.info(f"Creating initial game data for user {username} ({user_id}).")
                new_resources = Resources(user_id=user_id)
                new_buildings = Buildings(user_id=user_id)
                db.session.add(new_resources)
                db.session.add(new_buildings)
                db.session.commit()
                logger.info(f"Successfully created game data for user {username} ({user_id}).")
            else:
                logger.warning(f"User {username} ({user_id}) has buildings but no resources. Data might be inconsistent.")
        else:
            logger.info(f"User {username} ({user_id}) already exists in game DB. No action needed.")

    except KeyError as e:
        logger.error(f"Missing key {e} in user_created message: {message_data}")
        raise # Передаем ошибку выше для nack в RabbitMQ wrapper
    except SQLAlchemyError as e:
        logger.error(f"Database error processing user_created for user_id {message_data.get('user_id', 'N/A')}: {e}", exc_info=True)
        # Откат сессии будет сделан в callback_wrapper в shared/rabbitmq.py
        raise # Передаем ошибку выше для nack
    except Exception as e:
         logger.error(f"Unexpected error processing user_created_message: {e}", exc_info=True)
         # Откат сессии будет сделан в callback_wrapper
         raise # Передаем ошибку выше для nack
