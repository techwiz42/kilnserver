#!/usr/bin/python2.7
# all the imports
import os, logging
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

handler = logging.FileHandler('/tmp/kilnweb.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler) 
app.logger.setLevel(logging.DEBUG)

import kilnweb.views

