''' (c) 2023, 2024 Control Physics - all rights reserved '''
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
  SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'kilnweb.db')
  DEBUG = True,
  SECRET_KEY='099d77359a8c14d35c440b1589570f99'
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  EXPLAIN_TEMPLATE_LOADING = False

  INTERVAL = 5 # Read and adjust temp every this many seconds.
  UNITS="F" # "F" or "C"
  ERANGE = 5 # Initall maximum error in degrees
  DRANGE = 5 # Initial first derivative of error in degrees
  TEMP_LIMIT = 1000 # Kiln will shut down if it reaches this temp.

