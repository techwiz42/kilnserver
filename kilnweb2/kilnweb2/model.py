''' Module defines Job, JobStep and User tables '''
from dataclasses import dataclass
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from kilnweb2 import app, login
import jwt

@login.user_loader
def load_user(id):
    '''Loads User corresponding to the given id'''
    return User.query.get(int(id))

@dataclass
class Job(app.db.Model):
    '''The job controls one annealing or cooling run'''
    __tablename__ = 'jobs'
    id = app.db.Column(app.db.Integer, primary_key=True)
    name = app.db.Column(app.db.Text)
    user_id = app.db.Column(app.db.Integer, app.db.ForeignKey('users.id'))
    comment = app.db.Column(app.db.Text)
    created = app.db.Column(app.db.DateTime)
    modified = app.db.Column(app.db.DateTime)
    steps = app.db.relationship('JobStep', backref='job')

    def __getitem__(self, key):
        ''' return the value corresponding to the given key '''
        if key in self.__dict__:
            return self.__dict__[key]

@dataclass
class Settings(app.db.Model):
    ''' class containing the user-definable settings '''
    __tablename__ = 'settings'
    id = app.db.Column(app.db.Integer, primary_key=True)
    erange = app.db.Column(app.db.Float)
    drange = app.db.Column(app.db.Float)
    interval = app.db.Column(app.db.Integer)
    units = app.db.Column(app.db.String(1))

    def __getitem__(self, key):
        ''' Returns the value from the row corresponding to the given key '''
        if key in self.__dict__:
            return self.__dict__[key]

@dataclass
class JobStep(app.db.Model):
    ''' class representing a single step in the annealing or cooling job '''
    __tablename__ = 'job_steps'
    id = app.db.Column(app.db.Integer, primary_key=True)
    job_id = app.db.Column(app.db.Integer, app.db.ForeignKey('jobs.id'))
    target = app.db.Column(app.db.Integer)
    rate = app.db.Column(app.db.Integer)
    dwell = app.db.Column(app.db.Integer)
    threshold = app.db.Column(app.db.Integer)

    def __getitem__(self, key):
        ''' Returns the value from the row corresponding to the given key '''
        if key in self.__dict__:
            return self.__dict__[key]

@dataclass
class JobRecord(app.db.Model):
    __tablename__ = 'job_record'
    id = app.db.Column(app.db.Integer, primary_key=True)
    job_id = app.db.Column(app.db.Integer, app.db.ForeignKey('jobs.id'))
    realtime = app.db.Column(app.db.Integer)
    tmeas = app.db.Column(app.db.Float)
    setpoint = app.db.Column(app.db.Float)
    run_number = app.db.Column(app.db.Integer)

    def __getitem__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]

class KeyStore(app.db.Model):
    __tablename__ = 'key_store'
    key = app.db.Column(app.db.String(16), primary_key=True, unique=True)
    value = app.db.Column(app.db.Integer)

    def __init__(self, key, value):
        self.key = key
        self.value = value
    
    def __repr__(self):
        return '<key=%r value=%r>' % (self.key, self.value)

    def __getitem__(self, key):
        return self.__dict__[key]

@dataclass
class User(UserMixin, app.db.Model):
    ''' Class representing a user '''
    __tablename__ = "users"
    id = app.db.Column(app.db.Integer, primary_key = True)
    username = app.db.Column(app.db.String(32), index=True, unique=True)
    is_admin = app.db.Column(app.db.Integer)
    is_auth = app.db.Column(app.db.Integer)
    full_name = app.db.Column(app.db.String(64))
    email_address = app.db.Column(app.db.String(128), index=True, unique=True)
    phone_number = app.db.Column(app.db.String(16))
    password_hash = app.db.Column(app.db.String(128))

    def __getitem__(self, key):
        ''' returns the value corresponding to the given key '''
        if key in self.__dict__:
            return self.__dict__[key]

    def set_password(self, password):
        ''' don\'t save password in clear text'''
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        ''' check password against saved hash '''
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self):
        return jwt.encode(payload={'username': self.username},
                key='it_is_a_secret',
                algorithm="HS256")

    @staticmethod
    def verify_reset_token(token):
        try:
            reset_dict = jwt.decode(jwt=token,
                    key='it_is_a_secret',
                    algorithms=['HS256'])
            username = reset_dict.get('username')
        except Exception as e:
            print(traceback.format_exc())
            return
        return User.query.filter_by(username=username).first()

    @staticmethod
    def verify_email(email_address):
        user = User.query.filter_by(email_address=email_address).first()
        return user

with app.app_context():
    app.db.create_all()

''' (c) 2023, 2024 Control Physics - all rights reserved '''
