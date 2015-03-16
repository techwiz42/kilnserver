#!/usr/bin/python2.7
# all the imports
import os
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
  SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join('/tmp', 'kilnweb.db'),
  DEBUG=True,
  SECRET_KEY='099d77359a8c14d35c440b1589570f99'
))
app.config.from_envvar('KILNSERVER_SETTINGS', silent=True)

import kilnweb.views

def main():
  app.run(debug=True, host='0.0.0.0')
