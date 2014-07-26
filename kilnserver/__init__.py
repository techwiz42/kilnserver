# all the imports
import os
import time
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash


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

import kilnserver.db
import kilnserver.views
import kilnserver.task_manager
import kilnserver.tasks
