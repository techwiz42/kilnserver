import socket
from kilnserver.kiln_controller import SOCK_PATH

class KilnCommand:
  def __init__(self):
    self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) 
    self.sock.connect(SOCK_PATH)

  def __del__(self):
    self.sock.close()

  def start(self, job_id):
    sock.sendall("START " + job_id + "\n")

  def stop(self):
    sock.sendall("STOP\n")

  def pause(self):
    sock.sendall("PAUSE\n")

  def resume(self):
    sock.sendall("RESUME\n")

  def status(self):
    state = None
    job_id = None
    sock.sendall("STATUS\n")
    data = sock.recv(128)
    if data:
      chunks = data.split(',')
      for chunk in chunks:
        key, value = chunk.split(' ')
        if key == 'STATE':
          state = value
        elif key == 'JOB_ID':
          job_id = value

