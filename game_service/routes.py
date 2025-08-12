# game_service/routes.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from .models import Resources, Buildings
from .utils import verify_jwt_token, process_user_created_message
from . import db
import logging
from flasgger import swag_from

game_bp = Blueprint('game_bp', __name__, template_folder='templates', static_folder='static')
logger = logging.getLogger(__name__)

@game_bp.route('/game', methods=['GET'])
@swag_from({
    'tags': ['Game'],
    'description': 'Основная игровая страница',
    'parameters': [
        {
            'name': 'token',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'JWT токен аутентификации'
        }
    ],
    'responses': {
        200: {
            'description': 'Игровая страница',
            'content': {
                'text/html': {}
            }
        },
        401: {'description': 'Невалидный или просроченный токен'},
        500: {'description': 'Ошибка сервера'}
    },
    'security': [{'JWT': []}]
})
def game_page():
    token = request.args.get('token')
    if not token:
        logger.warning("Access attempt to /game without token.")
        return render_template("error.html", message="Token is required", token=None), 401

    user_data = verify_jwt_token(token)
    if not user_data:
        logger.warning(f"Invalid or expired token provided for /game: {token[:10]}...")
        return render_template("error.html", message="Invalid or expired token", token=token), 401

    try:
        if 'sub' not in user_data or 'username' not in user_data:
            logger.error(f"Token payload is missing 'sub' or 'username': {user_data}")
            return render_template("error.html", message="Invalid token payload", token=token), 401
        
        user_id = int(user_data['sub'])
        username = user_data['username']
        logger.info(f"User {username} (ID: {user_id}) accessing game page.")
    except (ValueError, TypeError) as e:
        logger.error(f"Could not convert user ID from token ('sub': {user_data.get('sub')}) to int: {e}")
        return render_template("error.html", message="Invalid user ID format in token", token=token), 401

    user_resources = db.session.get(Resources, user_id)
    user_buildings = db.session.get(Buildings, user_id)

    if not user_resources or not user_buildings:
        logger.warning(f"Game data not found for user {username} (ID: {user_id}). Attempting to create on-the-fly.")
        try:
            needs_commit = False
            if not user_resources:
                new_resources = Resources(user_id=user_id)
                db.session.add(new_resources)
                needs_commit = True
            if not user_buildings:
                new_buildings = Buildings(user_id=user_id)
                db.session.add(new_buildings)
                needs_commit = True

            if needs_commit:
                db.session.commit()
                logger.info(f"Successfully created missing game data for user {username} (ID: {user_id}) on-the-fly.")
                user_resources = db.session.get(Resources, user_id)
                user_buildings = db.session.get(Buildings, user_id)

            if not user_resources or not user_buildings:
                logger.error(f"Failed to create or fetch game data for user {username} (ID: {user_id}) even after attempting creation.")
                return render_template("error.html", message="Failed to initialize user game data.", token=token), 500

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error creating game data on-the-fly for user {username} (ID: {user_id}): {e}", exc_info=True)
            return render_template("error.html", message="Error initializing user game data (DB).", token=token), 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error creating game data on-the-fly for user {username} (ID: {user_id}): {e}", exc_info=True)
            return render_template("error.html", message="Error initializing user game data (Server).", token=token), 500

    now = datetime.utcnow()
    can_collect = True
    if user_resources.last_collected:
        try:
            if isinstance(user_resources.last_collected, datetime):
                can_collect = (now - user_resources.last_collected) >= timedelta(hours=1)
            else:
                logger.warning(f"last_collected for user {user_id} is not a datetime object: {user_resources.last_collected}")
                user_resources.last_collected = now
                db.session.commit()
                can_collect = False
        except TypeError as e:
            logger.error(f"TypeError comparing datetimes for user {user_id}. Now: {now}, Last Collected: {user_resources.last_collected}. Error: {e}")
            can_collect = False

    return render_template(
        'game.html',
        username=username,
        resources={
            'wood': user_resources.wood,
            'stone': user_resources.stone,
            'gold': user_resources.gold
        },
        buildings={
            'sawmill_level': user_buildings.sawmill_level,
            'quarry_level': user_buildings.quarry_level,
            'mine_level': user_buildings.mine_level
        },
        token=token,
        can_collect=can_collect
    )

@game_bp.route('/collect_resources', methods=['POST'])
@swag_from({
    'tags': ['Game Actions'],
    'description': 'Сбор ресурсов',
    'parameters': [
        {
            'name': 'token',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'JWT токен аутентификации'
        }
    ],
    'responses': {
        302: {
            'description': 'Redirect to game page with flash message',
            'headers': {
                'Location': {
                    'description': 'URL of game page',
                    'type': 'string'
                }
            }
        },
        401: {'description': 'Невалидный или просроченный токен'},
        404: {'description': 'Данные пользователя не найдены'},
        500: {'description': 'Ошибка сервера'}
    },
    'security': [{'JWT': []}]
})
def collect_resources():
    token = request.form.get('token') or request.args.get('token')
    user_data = verify_jwt_token(token)
    if not user_data:
        return render_template("error.html", message="Invalid token", token=token), 401

    user_id = int(user_data['sub'])
    user_resources = db.session.get(Resources, user_id)
    user_buildings = db.session.get(Buildings, user_id)

    if not user_resources or not user_buildings:
        return render_template("error.html", message="User data not found", token=token), 404

    now = datetime.utcnow()
    if (now - user_resources.last_collected) < timedelta(hours=1):
        flash("Вы уже собирали ресурсы в течение последнего часа.", "warning")
        return redirect(url_for('game_bp.game_page', token=token))

    user_resources.wood += user_buildings.sawmill_level * 10
    user_resources.stone += user_buildings.quarry_level * 5
    user_resources.gold += user_buildings.mine_level * 2
    user_resources.last_collected = now

    db.session.commit()
    flash("Ресурсы успешно собраны!", "success")
    return redirect(url_for('game_bp.game_page', token=token))

@game_bp.route('/build/<building_type>', methods=['POST'])
@swag_from({
    'tags': ['Game Actions'],
    'description': 'Улучшение здания',
    'parameters': [
        {
            'name': 'token',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'JWT токен аутентификации'
        },
        {
            'name': 'building_type',
            'in': 'path',
            'type': 'string',
            'enum': ['sawmill', 'quarry', 'mine'],
            'required': True,
            'description': 'Тип здания для улучшения'
        }
    ],
    'responses': {
        302: {
            'description': 'Redirect to game page with flash message',
            'headers': {
                'Location': {
                    'description': 'URL of game page',
                    'type': 'string'
                }
            }
        },
        401: {'description': 'Невалидный или просроченный токен'},
        404: {'description': 'Данные пользователя не найдены'},
        400: {'description': 'Неверный тип здания'},
        500: {'description': 'Ошибка сервера'}
    },
    'security': [{'JWT': []}]
})
def build_building(building_type):
    token = request.form.get('token') or request.args.get('token')
    user_data = verify_jwt_token(token)
    if not user_data:
        flash("Invalid or expired token.", "error")
        return render_template("error.html", message="Invalid token", token=token), 401

    user_id = int(user_data['sub'])
    valid_buildings = ['sawmill', 'quarry', 'mine']
    if building_type not in valid_buildings:
        flash("Указан недопустимый тип здания", "error")
        return redirect(url_for('game_bp.game_page', token=token))

    user_buildings = db.session.get(Buildings, user_id)
    user_resources = db.session.get(Resources, user_id)
    if not user_buildings or not user_resources:
        flash("User data not found.", "error")
        return render_template("error.html", message="User data not found", token=token), 404

    current_level = getattr(user_buildings, f'{building_type}_level')
    setattr(user_buildings, f'{building_type}_level', current_level + 1)

    db.session.commit()
    flash(f"{building_type.capitalize()} level increased successfully!", "success")
    return redirect(url_for('game_bp.game_page', token=token))

@game_bp.route('/logout')
def logout():
    """Выход из игровой системы
    ---
    tags:
      - Game
    responses:
      302:
        description: Redirect to auth service login page
    """
    flash("Вы успешно вышли из системы.", "info")
    return redirect("http://localhost:5000/login")