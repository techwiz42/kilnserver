""" (c) 2023, 2024 Control Physics. All rights reserved. """
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
    conn = self.sock.connect(SOCK_PATH)
    settings = model.Settings.query.filter_by(id=1).first()
    self.erange = settings.erange
    self.drange = settings.drange
    self.units = settings.units
    self.interval = settings.interval

  def __del__(self):
    self.sock.close()

  def start(self, job_id):
    job = model.Job.query.filter_by(id=int(job_id)).first()
    if job is not None:
        command = json.dumps({'command': 'start', 'job_id': int(job_id), 'steps': job.steps, 
            'units': self.units, 'interval': self.interval, 'erange': self.erange, 'drange': self.drange}, default=jdefault)
        self.sock.sendall(_to_bytes(command + "\n"))
    else:
        return f"Job {job_id} does not exist"

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
      tmeas = status_data['tmeas']
      setpoint = status_data['setpoint']
    return [state, job_id, tmeas, setpoint]

def _to_bytes(s):
  return bytes(s, encoding='utf-8')

