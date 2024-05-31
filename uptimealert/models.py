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
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_checked_at = db.Column(db.DateTime)
    failed_times = db.Column(db.Integer, default=0)
    status = db.Column(db.Boolean)
    disabled = db.Column(db.Boolean)

    user = db.relationship("User", foreign_keys="Monitor.user_id")
    incidents = db.relationship("Incident", cascade="all, delete", back_populates="monitor")
    dashboards = db.relationship('DashboardMonitor', cascade="all, delete", back_populates='monitor')
    shared_users = db.relationship('SharedMonitor', cascade="all, delete", back_populates='monitor')


class Incident(db.Model):
    __tablename__ = "incidents"
    id = db.Column(db.Integer, primary_key=True, index=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey(Monitor.id))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    resolved_at = db.Column(db.DateTime)

    monitor = db.relationship("Monitor", back_populates="incidents", foreign_keys='Incident.monitor_id')


class Dashboard(db.Model):
    __tablename__ = "dashboards"
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    name = db.Column(db.String(150))

    monitors = db.relationship('DashboardMonitor', cascade="all, delete", back_populates='dashboard')
    user = db.relationship("User", foreign_keys="Dashboard.user_id")


class DashboardMonitor(db.Model):
    __tablename__ = "dashboards_monitors"
    id = db.Column(db.Integer, primary_key=True, index=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('monitors.id'))
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboards.id'))

    dashboard = db.relationship('Dashboard', back_populates='monitors')
    monitor = db.relationship('Monitor', back_populates='dashboards')


class SharedMonitor(db.Model):
    __tablename__ = "shared_monitors"
    id = db.Column(db.Integer, primary_key=True, index=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey(Monitor.id))
    shared_user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    shared_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    monitor = db.relationship("Monitor", back_populates="shared_users")
    shared_user = db.relationship("User", foreign_keys="SharedMonitor.shared_user_id")