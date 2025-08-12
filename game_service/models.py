# game_service/models.py
from . import db
from datetime import datetime

class Resources(db.Model):
    __tablename__ = 'resources'
    user_id = db.Column(db.Integer, primary_key=True)
    wood = db.Column(db.Integer, default=0)
    stone = db.Column(db.Integer, default=0)
    gold = db.Column(db.Integer, default=0)
    last_collected = db.Column(db.DateTime, default=datetime.utcnow)

class Buildings(db.Model):
    __tablename__ = 'buildings'
    user_id = db.Column(db.Integer, primary_key=True)
    sawmill_level = db.Column(db.Integer, default=1)
    quarry_level = db.Column(db.Integer, default=1)
    mine_level = db.Column(db.Integer, default=1)
