# all the imports
import os
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from celery import Celery


app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
  DATABASE=os.path.join(app.root_path, 'kilnserver.db'),
  DEBUG=True,
  SECRET_KEY='099d77359a8c14d35c440b1589570f99',
  CELERY_BROKER_URL='redis://localhost:6379/0'
))
app.config.from_envvar('KILNSERVER_SETTINGS', silent=True)

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

celery = make_celery(app)

import kilnserver.db
import kilnserver.views
import kilnserver.tasks
