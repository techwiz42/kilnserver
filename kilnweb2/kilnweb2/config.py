import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
  SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'kilnweb.db')
  DEBUG = True,
  SECRET_KEY='099d77359a8c14d35c440b1589570f99'
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  EXPLAIN_TEMPLATE_LOADING = True