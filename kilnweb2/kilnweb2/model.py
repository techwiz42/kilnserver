''' Module defines Job, JobStep and User tables '''
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from kilnweb2 import app, login
import jwt

@login.user_loader
def load_user(id):
    '''Loads User corresponding to the given id'''
    return User.query.get(int(id))

class Job(app.db.Model):
    '''The job controls one annealing or cooling run'''
    __tablename__ = 'jobs'
    id = app.db.Column(app.db.Integer, primary_key=True)
    name = app.db.Column(app.db.Text)
    user_id = app.db.Column(app.db.Integer, app.db.ForeignKey('users.id'))
    comment = app.db.Column(app.db.Text)
    created = app.db.Column(app.db.DateTime)
    modified = app.db.Column(app.db.DateTime)
    units = app.db.Column(app.db.Text, default="F")
    interval = app.db.Column(app.db.Integer)
    erange = app.db.Column(app.db.Integer)
    drange = app.db.Column(app.db.Integer)
    steps = app.db.relationship('JobStep', backref='job')

    def __init__(self, user_id, name, comment, interval, erange, drange, created, modified, units="F"):
        ''' class initializer '''
        self.comment = comment
        self.user_id = user_id
        self.name = name
        self.interval = interval
        self.erange = erange
        self.drange = drange
        self.created = created
        self.modified = modified
        self.units = units

    def __getitem__(self, key):
        ''' return the value corresponding to the given key '''
        if key in self.__dict__:
            return self.__dict__[key]

    def __repr__(self):
        ''' Returns the string representation of a row in the table '''
        return f"<Job {self.id}, name={self.name}, user_id={self.user_id}, comment={self.comment}, created={self.created}, modified={self.modified}, units={self.units}, interval={self.interval}, erange={self.erange}, drange={self.drange}>" 

class JobStep(app.db.Model):
    ''' class representing a single step in the annealing or cooling job '''
    __tablename__ = 'job_steps'
    id = app.db.Column(app.db.Integer, primary_key=True)
    job_id = app.db.Column(app.db.Integer, app.db.ForeignKey('jobs.id'))
    target = app.db.Column(app.db.Integer)
    rate = app.db.Column(app.db.Integer)
    dwell = app.db.Column(app.db.Integer)
    threshold = app.db.Column(app.db.Integer)

    def __init__(self, job, target, rate, dwell, threshold):
        ''' Class initializer '''
        self.job = job
        self.target = target
        self.rate = rate
        self.dwell = dwell
        self.threshold = threshold

    def __repr__(self):
        ''' String representation of a single row in the JobStep table '''
        return '<JobStep %r target=%r rate=%r dwell=%r threshold=%r>' % (self.id, self.target, self.rate, self.dwell, self.threshold)

    def __getitem__(self, key):
        ''' Returns the value from the row corresponding to the given key '''
        if key in self.__dict__:
            return self.__dict__[key]

class JobRecord(app.db.Model):
    __tablename__ = 'job_record'
    id = app.db.Column(app.db.Integer, primary_key=True)
    job_id = app.db.Column(app.db.Integer, app.db.ForeignKey('jobs.id'))
    realtime = app.db.Column(app.db.Integer)
    tmeas = app.db.Column(app.db.Float)
    setpoint = app.db.Column(app.db.Float)
    run_number = app.db.Column(app.db.Integer)

    def __init__(self, job_id, realtime, tmeas, setpoint, run_number):
        self.job_id = job_id
        self.realtime = realtime
        self.tmeas = tmeas
        self.setpoint = setpoint
        self.run_number = run_number

    def __repr__(self):
        return '<JobRecord=%r realtime=%r tmeas=%r setpoint=%r run_number=%r>' % (self.id, self.realtime, self.tmeas, self.setpoint, self.run_number)


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

    def __repr__(self):
        ''' returns string representation of a single row of the user table '''
        return '<User %r, username=%r, is_admin=%r, is_auth=%r, full_name=%r, email_address=%r, phone_number=%r>' %(self.id, self.is_admin, self.is_auth, self.username, self.full_name, self.email_address, self.phone_number)

    def __getitem__(self, key):
        ''' returns the value corresponding to the given key '''
        if key in self.__dict__:
            return self.__dict__[key]

    def __init__(self, username, full_name, email_address, phone_number, is_admin = 0, is_auth = 0):
        ''' class initializer'''
        self.username = username
        self.is_admin = is_admin
        self.is_auth = is_auth
        self.full_name = full_name
        self.email_address = email_address
        self.phone_number = phone_number

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

''' (c) 2023 Control Physics - all rights reserved '''
