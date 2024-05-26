from celery import Celery
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    return app

flask_app = create_app()
celery = Celery(flask_app.name, broker=flask_app.config['CELERY_BROKER_URL'])
celery.conf.update(flask_app.config)

# Beispiel für einen Task
@celery.task
def example_task():
    print("Task executed")
