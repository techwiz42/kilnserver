from kilnserver import celery
from kilnserver import app
import subprocess
from subprocess import PIPE

@celery.task()
def task_start_job(job_id):
  args = ['/bin/sleep', '15']
  p = subprocess.Popen(args, stdout=PIPE, stderr=PIPE)
  out, err = p.communicate()
  app.logger.debug("start_job: subprocess output: %s" % [out])

