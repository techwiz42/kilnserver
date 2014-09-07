from kilnserver import app
from kilnserver.model import db, Job, JobStep
from datetime import datetime
def add_demo_job():
  j = Job('Another', datetime.now(), datetime.now()) 
  db.session.add(j)
  js = JobStep(j, 500, 15, 30, 505)
  db.session.add(js)
  js = JobStep(j, 750, 5, 10, 760)
  db.session.add(js)
  js = JobStep(j, 1200, 20, 120, 1350)
  db.session.add(js)
  js = JobStep(j, 900, 10, 10, 905)
  db.session.add(js)
  js = JobStep(j, 350, 60, 60, 355)
  db.session.add(js)
  db.session.commit()

if __name__ == '__main__':
  add_demo_job()
