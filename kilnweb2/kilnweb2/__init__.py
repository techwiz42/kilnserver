#! /Users/bartelby/.virtualenvs/kilnsvr/bin/python
import os, logging
from flask import Flask
from flask_login import LoginManager
from flask_bootstrap import Bootstrap

from kilnweb2.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
app.db = SQLAlchemy(app)
migrate = Migrate(app, app.db)

bootstrap = Bootstrap(app)
login = LoginManager(app)

from internals import views, model

app.config.from_envvar('KILNSERVER_SETTINGS', silent=True)

def main():
  handler = logging.FileHandler('/tmp/kilnweb.log')
  formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
  handler.setFormatter(formatter)
  app.logger.addHandler(handler) 
  app.logger.setLevel(logging.DEBUG)
  app.run(debug=True, host='0.0.0.0')


if __name__ == '__main__':
    main()
