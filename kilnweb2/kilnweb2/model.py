from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import enum
from sqlalchemy import Integer, Enum
from kilnweb2 import app
from kilnweb2 import login

@login.user_loader
def load_user(id):
  return User.query.get(int(id))

class Job(app.db.Model):
  __tablename__ = 'jobs'
  id = app.db.Column(app.db.Integer, primary_key=True)
  name = app.db.Column(app.db.Text)
  user_id = app.db.Column(app.db.Integer, app.db.ForeignKey('users.id'))
  comment = app.db.Column(app.db.Text)
  created = app.db.Column(app.db.DateTime)
  modified = app.db.Column(app.db.DateTime)
  units = app.db.Column(app.db.Text, default="F")
  steps = app.db.relationship('JobStep', backref='job')

  def __init__(self, user_id, name, comment, created, modified, units="F"):
    self.comment = comment
    self.user_id = user_id
    self.name = name
    self.created = created
    self.modified = modified
    self.units = units

  def __getitem__(self, key):
    if key in self.__dict__:
      return self.__dict__[key]

  def __repr__(self):
    return '<Job %r, name=%r, user_id=%r, comment=%r, created=%r, modified=%r, units=%r>' % (self.id, self.name, self.user_id, self.comment, self.created, self.modified, self.units)

class JobStep(app.db.Model):
  __tablename__ = 'job_steps'
  id = app.db.Column(app.db.Integer, primary_key=True)
  job_id = app.db.Column(app.db.Integer, app.db.ForeignKey('jobs.id'))
  target = app.db.Column(app.db.Integer)
  rate = app.db.Column(app.db.Integer)
  dwell = app.db.Column(app.db.Integer)
  threshold = app.db.Column(app.db.Integer)

  def __init__(self, job, target, rate, dwell, threshold):
    self.job = job
    self.target = target
    self.rate = rate
    self.dwell = dwell
    self.threshold = threshold

  def __repr__(self):
    return '<JobStep %r target=%r rate=%r dwell=%r threshold=%r>' % (self.id, self.target, self.rate, self.dwell, self.threshold)

  def __getitem__(self, key):
    if key in self.__dict__:
      return self.__dict__[key]

class User(UserMixin, app.db.Model):
  __tablename__ = "users"
  id = app.db.Column(app.db.Integer, primary_key = True)
  username = app.db.Column(app.db.String(32), index=True, unique=True)
  is_admin = app.db.Column(app.db.Integer)
  is_auth = app.db.Column(app.db.Integer)
  full_name = app.db.Column(app.db.String(64))
  email_address = app.db.Column(app.db.String(128), index=True, unique=True)
  phone_number = app.db.Column(app.db.String(16), index=True)
  password_hash = app.db.Column(app.db.String(128))

  def __repr__(self):
    return '<User %r, username=%r, is_admin=%r, is_auth=%r, full_name=%r, email_address=%r, phone_number=%r>' % (self.id, self.is_admin, self.is_auth, self.username, self.full_name, self.email_address, self.phone_number)

  def __getitem__(self, key):
    if key in self.__dict__:
      return self.__dict__[key]

  def __init__(self, username, full_name, email_address, phone_number, is_admin = 0, is_auth = 0):
    __tablename__ = 'kilns'
    self.username = username
    self.is_admin = is_admin
    self.is_auth = is_auth,
    self.full_name = full_name
    self.email_address = email_address
    self.phone_number = phone_number

  def set_password(self, password):
    self.password_hash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

app.db.create_all()
