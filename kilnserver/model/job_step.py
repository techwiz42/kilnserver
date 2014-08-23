from kilnserver.model import db
from kilnserver.model.db import Model, Column, Integer, ForeignKey

class JobStep(Model):
  __tablename__ = 'job_steps'
  id = Column(Integer, primary_key=True)
  job_id = Column(Integer, ForeignKey('jobs.id'))
  target = Column(Integer)
  rate = Column(Integer)
  dwell = Column(Integer)
  threshold = Column(Integer)

  def __init__(self):
    pass

  def __repr__(self):
    return '<JobStep %r>' % self.id
