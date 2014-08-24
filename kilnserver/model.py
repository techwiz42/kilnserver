from flask.ext.sqlalchemy import SQLAlchemy
from kilnserver import app

db = SQLAlchemy(app)

class Job(db.Model):
  __tablename__ = 'jobs'
  id = db.Column(db.Integer, primary_key=True)
  comment = db.Column(db.Text)
  created = db.Column(db.DateTime)
  modified = db.Column(db.DateTime)
  steps = db.relationship('JobStep')

  def __init__(self, comment, created, modified):
    self.comment = comment
    self.created = created
    self.modified = modified
    pass

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

  def __init__(self, target, rate, dwell, threshold):
    self.target = db.Column(db.Integer)
    self.rate = db.Column(db.Integer)
    self.dwell = db.Column(db.Integer)
    self.threshold = db.Column(db.Integer)

  def __repr__(self):
    return '<JobStep %r target=%r rate=%r dwell=%r threshold=%r>' % (self.id, self.target, self.rate, self.dwell, self.threshold)
