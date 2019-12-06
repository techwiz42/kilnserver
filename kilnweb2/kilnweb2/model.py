from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from kilnweb2 import app
from kilnweb2 import login

db = SQLAlchemy(app)

@login.user_loader
def load_user(id):
  return User.query.get(int(id))

class Job(db.Model):
  __tablename__ = 'jobs'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.Text)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
  comment = db.Column(db.Text)
  created = db.Column(db.DateTime)
  modified = db.Column(db.DateTime)
  steps = db.relationship('JobStep', backref='job')

  def __init__(self, comment, created, modified):
    self.comment = comment
    self.created = created
    self.modified = modified

  def __getitem__(self, key):
    if key in self.__dict__:
      return self.__dict__[key]

  def __repr__(self):
    return '<Job %r, name=%r, user_id=%r, comment=%r, created=%r, modified=%r>' % (self.id, self.name, self.user_id, self.comment, self.created, self.modified)

class JobStep(db.Model):
  __tablename__ = 'job_steps'
  id = db.Column(db.Integer, primary_key=True)
  job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))
  target = db.Column(db.Integer)
  rate = db.Column(db.Integer)
  dwell = db.Column(db.Integer)
  threshold = db.Column(db.Integer)

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

class User(UserMixin, db.Model):
  __tablename__ = "users"
  id = db.Column(db.Integer, primary_key = True)
  username = db.Column(db.String(32), index=True, unique=True)
  full_name = db.Column(db.String(64))
  email_address = db.Column(db.String(128), index=True, unique=True)
  phone_number = db.Column(db.String(16), index=True)
  password_hash = db.Column(db.String(128))

  def __repr__(self):
    return '<User %r id=%r, username=%r, full_name=%r, email_address=%r, phone_number=%r>' % (self.id, self.username, self.full_name, self.email_address, self.phone_number)

  def __getitem__(self, key):
    if key in self.__dict__:
      return self.__dict__[key]

  def __init__(self, username, full_name, email_address, phone_number):
    self.username = username
    self.full_name = full_name
    self.email_address = email_address
    self.phone_number = phone_number

  def set_password(self, password):
    self.password_hash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password_hash, password)


db.create_all()
