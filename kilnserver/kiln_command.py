import socket
from kilnserver.kiln_controller import SOCK_PATH

class KilnCommand:
  def __init__(self):
    self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) 
    self.sock.connect(SOCK_PATH)

  def __del__(self):
    self.sock.close()

  def start(self, job_id):
    self.sock.sendall("START " + str(job_id) + "\n")

  def stop(self):
    self.sock.sendall("STOP\n")

  def pause(self):
    self.sock.sendall("PAUSE\n")

  def resume(self):
    self.sock.sendall("RESUME\n")

  def status(self):
    state = None
    job_id = None
    self.sock.sendall("STATUS\n")
    data = self.sock.recv(128)
    if data:
      chunks = data.split(',')
      for chunk in chunks:
        key, value = chunk.split(' ')
        if key == 'STATE':
          state = value
        elif key == 'JOB_ID':
          job_id = value
    return [state,job_id]

