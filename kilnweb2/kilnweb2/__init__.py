#! /Users/bartelby/.virtualenvs/kilnsvr/bin/python
import os, logging
from flask import Flask
from flask_login import LoginManager

app = Flask(__name__)
login = LoginManager(app)

#IMPORTANT NOTE: kilnweb2.views not referenced in this file
# but import is required for code to function.  Strange...
import kilnweb2.views

# Load default config and override config from an environment variable
app.config.update(dict(
  SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join('/tmp', 'kilnweb.db'),
  DEBUG=True,
  SECRET_KEY='099d77359a8c14d35c440b1589570f99'
))
app.config.from_envvar('KILNSERVER_SETTINGS', silent=True)

def create_admin_user():
  admins = app.model.db()

def main():
  handler = logging.FileHandler('/tmp/kilnweb.log')
  formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
  handler.setFormatter(formatter)
  app.logger.addHandler(handler) 
  app.logger.setLevel(logging.DEBUG)
  create_admin_user()
  app.run(debug=True, host='0.0.0.0')


if __name__ == '__main__':
    main()
