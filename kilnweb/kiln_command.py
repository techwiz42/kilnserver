import socket, json
from kilncontroller.constants import SOCK_PATH
from kilnweb.model import db, Job, JobStep

class KilnCommand:
  def __init__(self):
    self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) 
    self.sock.connect(SOCK_PATH)

  def __del__(self):
    self.sock.close()

  def start(self, job_id):
    # TODO: Handle job not found condition
    job = Job.query.filter_by(id=int(job_id)).first()
    json.dump({'command': 'start', 'job_id': int(job_id), 'steps': job.steps}, self.sock)

  def stop(self):
    json.dump({'command': 'stop'}, self.sock)

  def pause(self):
    json.dump({'command': 'pause'}, self.sock)

  def resume(self):
    json.dump({'command': 'resume'}, self.sock)

  def status(self):
    state = None
    job_id = None
    json.dump({'command': 'status'}, self.sock)
    data = self.sock.recv(1024)
    if data:
      status_data = json.loads(data)
      state = status_data['state']
      job_id = status_data['job_id']
    return [state,job_id]

