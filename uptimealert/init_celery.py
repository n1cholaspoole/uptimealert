from app import create_app
from app import db
from celery.signals import worker_process_init

flask = create_app()
celery = flask.extensions["celery"]


@worker_process_init.connect
def prep_db_pool(**kwargs):
    with flask.app_context():
        db.engine.dispose()
