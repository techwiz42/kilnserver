from flask_sqlalchemy import SQLAlchemy
from kilnweb2 import app

db = SQLAlchemy(app)

class Job(db.Model):
  __tablename__ = 'jobs'
  id = db.Column(db.Integer, primary_key=True)
  comment = db.Column(db.Text)
  created = db.Column(db.DateTime)
  modified = db.Column(db.DateTime)
  steps = db.relationship('JobStep', backref='job')

  def __init__(self, comment, created, modified):
    self.comment = comment
    self.created = created
    self.modified = modified

  def __repr__(self):
    return '<Job %r, comment=%r, created=%r, modified=%r>' % (self.id, self.comment, self.created, self.modified)

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

db.create_all()
