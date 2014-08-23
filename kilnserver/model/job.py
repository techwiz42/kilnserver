from kilnserver.model import db
from kilnserver.model.db import Model, Column, Integer, Text, DateTime, ForeignKey

class Job(Model):
  __tablename__ = 'jobs'
  id = Column(Integer, primary_key=True)
  comment = Column(Text)
  created = Column(DateTime)
  modified = Column(DateTime)
  steps = relationship('JobStep', backref='jobs')

  def __init__(self, comment, created, modified):
    self.comment = comment
    self.created = created
    self.modified = modified
    pass

  def __repr__(self):
    return '<Job %r, comment=%r, created=%r, modified=%r>' % (self.id, self.comment, self.created, self.modified)
