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
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    name = db.Column(db.String(50))
    type = db.Column(db.String(4))
    schema = db.Column(db.String(8))
    hostname = db.Column(db.String(100))
    port = db.Column(db.Integer)
    interval = db.Column(db.Integer)
    threshold = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    last_checked_at = db.Column(db.DateTime)
    failed_times = db.Column(db.Integer, default=0)
    status = db.Column(db.Boolean)

    user = db.relationship('User', foreign_keys='Monitor.user_id')


class Incident(db.Model):
    __tablename__ = "incidents"
    id = db.Column(db.Integer, primary_key=True, index=True)
    type = db.Column(db.Integer)
    monitor_id = db.Column(db.Integer, db.ForeignKey(Monitor.id))
    created_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    caused_by = db.Column(db.String(150))
    monitor = db.relationship('Monitor', foreign_keys='Incident.monitor_id')
