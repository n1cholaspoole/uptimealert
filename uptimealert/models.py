from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, index=True)
    email = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(102))


class Monitor(db.Model):
    __tablename__ = "monitors"
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(50))
    type = db.Column(db.String(4))
    hostname = db.Column(db.String(100))
    port = db.Column(db.Integer)
    interval = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    status = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)
    last_checked_at = db.Column(db.DateTime)

    user = db.relationship('User', foreign_keys='Monitor.user_id')


class Incident(db.Model):
    __tablename__ = "incidents"
    id = db.Column(db.Integer, primary_key=True, index=True)
    type = db.Column(db.Integer)
    monitor_id = db.Column(db.Integer, db.ForeignKey(Monitor.id))
    created_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)

    monitor = db.relationship('Monitor', foreign_keys='Incident.monitor_id')
