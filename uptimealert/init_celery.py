from app import create_app

flask = create_app()
celery = flask.extensions["celery"]
