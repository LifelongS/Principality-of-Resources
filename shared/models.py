#models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Создание объекта базы данных
db = SQLAlchemy()

# Модель для хранения данных о пользователях (ресурсах)
class Resources(db.Model):
    __tablename__ = 'resources'

    user_id = db.Column(db.Integer, primary_key=True)
    wood = db.Column(db.Integer, default=0)
    stone = db.Column(db.Integer, default=0)
    gold = db.Column(db.Integer, default=0)
    last_collected = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, wood=0, stone=0, gold=0):
        self.user_id = user_id
        self.wood = wood
        self.stone = stone
        self.gold = gold

# Модель для хранения данных о зданиях
class Buildings(db.Model):
    __tablename__ = 'buildings'

    user_id = db.Column(db.Integer, primary_key=True)
    sawmill_level = db.Column(db.Integer, default=1)
    quarry_level = db.Column(db.Integer, default=1)
    mine_level = db.Column(db.Integer, default=1)

    def __init__(self, user_id, sawmill_level=1, quarry_level=1, mine_level=1):
        self.user_id = user_id
        self.sawmill_level = sawmill_level
        self.quarry_level = quarry_level
        self.mine_level = mine_level
