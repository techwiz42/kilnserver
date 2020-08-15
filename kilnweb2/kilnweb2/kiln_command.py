import socket, json
#from kilncontroller import constants
from kilnweb2 import model
from collections import OrderedDict

SOCK_PATH = "/tmp/kiln_controller"

def jdefault(o):
  if isinstance(o, model.JobStep):
    d = OrderedDict()
    for key in o.__mapper__.c.keys():
      d[key] = o[key]
    return d
  return o.__dict__

class KilnCommand:
  def __init__(self):
    self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    self.sock.connect(SOCK_PATH)

  def __del__(self):
    self.sock.close()

  def start(self, job_id):
    # TODO: Handle job not found condition
    job = model.Job.query.filter_by(id=int(job_id)).first()
    command = json.dumps({'command': 'start', 'job_id': int(job_id), 'steps': job.steps, 'units': job.units}, default=jdefault)
    self.sock.sendall(_to_bytes(command + "\n"))

  def stop(self):
    command = json.dumps({'command': 'stop'})
    self.sock.sendall(_to_bytes(command + "\n"))

  def pause(self):
    command = json.dumps({'command': 'pause'})
    self.sock.sendall(_to_bytes(command + "\n"))

  def resume(self):
    command = json.dumps({'command': 'resume'})
    self.sock.sendall(_to_bytes(command + "\n"))

  def status(self):
    state = None
    job_id = None
    command = json.dumps({'command': 'status'})
    self.sock.sendall(_to_bytes(command + '\n'))
    data = self.sock.recv(1024)
    if data:
      status_data = json.loads(data)
      state = status_data['state']
      job_id = status_data['job_id']
    return [state,job_id]

  def halt(self):
    command = json.dumps({'command': 'halt_kilnserver'})
    self.sock.sendall(_to_bytes(command + '\n'))
    data = self.sock.recv(1024)
    if data:
      state = json.loads(data)
      return state
    else:
      return "UNKNOWN"

def _to_bytes(s):
  return bytes(s, encoding='utf-8')


