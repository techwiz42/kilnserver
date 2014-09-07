from kilnserver.model import db, Job, JobStep
import redis

RUN = 'run'
PAUSE = 'pause'
STOP = 'stop'
FINISH = 'finish'

VALID_STATE_TRANSITIONS = {
  None: [RUN],
  RUN: [PAUSE, STOP, FINISH],
  PAUSE: [RUN, STOP],
  STOP: [],
  FINISH: [],
}

class InvalidStateTransitionError(Exception):
  pass

class RedisState:
  # TODO: Build a dict of current states mapped to an array of valid target states.
  def __init__(self, tag, hostname='localhost', port=6379):
    self.redis = redis.Redis(hostname, port)
    self.tag = tag

  def valid_state_transition(self, current_state, target_state):
    if target_state in VALID_STATE_TRANSITIONS[current_state]:
      return True
    return False

  def get(self):
    return self.redis.hget(self.tag, 'state')

  def set(self, state):
    current_state = self.get()
    if self.valid_state_transition(current_state, state):
      self.redis.hset(self.tag, 'state', state)
    else:
      raise InvalidStateTransitionError("Invalid state transition: %s -> %s (%s)" % (current_state, state, self.tag))
    return True
