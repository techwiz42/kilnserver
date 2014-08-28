from kilnserver.model import db, Job, JobStep
from kilnserver.kiln_controller import KilnController
from kilnserver.redis_state import RedisState
from kilnserver.model import db, Job, JobStep
import redis
from time import sleep

def main():
  r = redis.Redis()
  while True:
    job_id = r.rpop('jobs')
    if job_id is not None:
      # Retrieve job data from database
      job = Job.query.filter_by(id=int(job_id)).first()
      # Create KilnController object
      kc = KilnController(job.steps)
      # Mark job as started
      start_time = time.time()
      unique_id = 'job_%s_%d' % (job_id, start_time)
      r.lpush('running_jobs', unique_id)
      r.hset(unique_id, 'job_id', job_id)
      r.hset(unique_id, 'start_time', start_time)
      # Call KilnController.run()
      kc.run()
    else:
      sleep(5)

if __name__ == '__main__':
  main()
