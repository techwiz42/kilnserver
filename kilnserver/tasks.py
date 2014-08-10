from kilnserver import celery
from kilnserver import app
from kilnserver.db import get_db
from kilnserver.kiln_controller import KilnController

import subprocess
from subprocess import PIPE

@celery.task()
def task_start_job(job_id):
  db = get_db()
  cursor = db.cursor() 
  cursor.execute('''SELECT target,rate,dwell,threshold FROM job_steps WHERE job_id=?''', [job_id])
  steps = cursor.fetchall()
  app.logger.debug("task_start_job: job_id=%s steps: %s" % (repr(job_id), repr(steps)))
  kc = KilnController(steps)
  kc.start()
  app.logger.debug("task_start_job: After KilnController.start()") 

@celery.task()
def task_sleep():
  args = ['/bin/sleep', '60']
  p = subprocess.Popen(args, stdout=PIPE, stderr=PIPE)
  out, err = p.communicate()
  app.logger.debug("start_job: subprocess output: %s" % [out])

