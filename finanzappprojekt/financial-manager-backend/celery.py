from flask import Flask
from celery import Celery
from celery.schedules import crontab
from celery import Celery
from app import create_app, db

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    return celery

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='deine_broker_url',  # z.B. 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND='dein_backend_url'  # z.B. 'redis://localhost:6379/0'
)
celery = make_celery(app)

app = create_app()
app.app_context().push()

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def some_task():
    # Task Logic
    pass


@celery.task
def check_notifications():   
    app.conf.beat_schedule = {
    'check-notifications-every-hour': {
        'task': 'check_notifications',
        'schedule': crontab(minute=0, hour='*')  # Jede Stunde zur vollen Stunde
    }
}