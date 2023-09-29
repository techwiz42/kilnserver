#! /Users/bartelby/.virtualenvs/kilnsvr/bin/python
import os, logging
from flask import Flask
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from kilnweb2.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
mail = Mail(app)
app.config.from_object(Config)
app.db = SQLAlchemy(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'thetechwizard42@gmail.com'
app.config['MAIL_PASSWORD'] = 'iszq rdrg ofju qxtt'
app.config['MAIL_DEBUG'] = False
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['TESTING'] = False

migrate = Migrate(app, app.db)
bootstrap = Bootstrap(app)
login = LoginManager(app)
mail = Mail(app)

app.config.from_envvar('KILNSERVER_SETTINGS', silent=True)

from kilnweb2 import views, model
from tests import test_kilnweb2

def main():
    handler = logging.FileHandler('/tmp/kilnweb.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler) 
    app.logger.setLevel(logging.DEBUG)
    app.run(debug=True, host='0.0.0.0')


if __name__ == '__main__':
    main()
