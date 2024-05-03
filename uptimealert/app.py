from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from celery import Celery, Task
from celery.schedules import crontab
from dotenv import load_dotenv
import os

load_dotenv()
db = SQLAlchemy()
mail = Mail()


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery = Celery(app.name, task_cls=FlaskTask)
    celery.config_from_object(app.config["CELERY"])
    celery.set_default()
    app.extensions["celery"] = celery
    return celery


def create_app() -> Flask:
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
    app.config['MAIL_SERVER'] = os.environ['MAIL_SERVER']
    app.config['MAIL_PORT'] = os.environ['MAIL_PORT']
    app.config['MAIL_USE_TLS'] = os.environ['MAIL_USE_TLS']
    app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
    app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
    app.config['MAIL_DEFAULT_SENDER'] = os.environ['MAIL_DEFAULT_SENDER']
    app.config['CELERY_BROKER_URL'] = os.environ['REDIS_URI']
    app.config['CELERY_RESULT_BACKEND'] = os.environ['REDIS_URI']

    app.config.from_mapping(
        CELERY=dict(
            broker_url=app.config.get('CELERY_BROKER_URL'),
            result_backend=app.config.get('CELERY_RESULT_BACKEND'),
            include=['scheduler'],
            autodiscover_tasks=(['scheduler']),
            task_ignore_result=True,
            timezone='UTC',
            enable_utc=True,
            beat_schedule={
                'scheduler': {
                    'task': 'scheduler.ping_servers',
                    'schedule': crontab(minute="*"),
                }
            }
        ),
    )

    celery_init_app(app)

    db.init_app(app)

    mail.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    @app.cli.command('reset-db')
    def reset_db():
        with app.app_context():
            db.drop_all()
            db.create_all()

    with app.app_context():
        db.create_all()

    return app
