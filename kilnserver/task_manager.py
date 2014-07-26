from kilnserver import app
from celery import Celery

def make_celery(app):
    app.logger.debug("app.import_name=%s" % app.import_name)
    celery = Celery('tasks', broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery_obj = make_celery(app)

