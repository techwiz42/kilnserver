'''The views module defines the app\'s available URLs '''
import os
import traceback
import threading
import time as tm
from datetime import datetime, time
from flask import request, redirect, url_for, render_template, flash
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Mail, Message
from kilnweb2 import app
from kilnweb2 import kiln_command, model, email
from kilnweb2.model import User, Job, JobRecord
from kilnweb2.forms import RegistrationForm, LoginForm, NewJobForm, ShowUserForm, PasswordResetForm

@app.route('/', methods = ['GET', 'POST'])
def index():
    return render_template('index.html', title="Kilnweb Welcome")

@app.route('/login', methods=['GET', 'POST'])
def login():
    ''' Route for handling the login page logic '''
    if current_user.is_authenticated:
        return redirect(url_for('show_jobs'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            print("failed validation - redirecting to login")
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('show_jobs'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    ''' logout user '''
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    ''' register new user '''
    if current_user.is_authenticated:
        return redirect(url_for('show_jobs'))
    form = RegistrationForm()
    if form.validate_on_submit():
        #Default value for is_admin and is_auth are False 
        #Admin authorizes users access to kilns on page ******* TBD ********
        user = User(username=form.username.data, email_address=form.email.data,
                full_name=form.full_name.data, phone_number=form.phone_number.data)
        user.set_password(form.password.data)
        user.is_auth = 0
        user.is_admin = 0
        app.db.session.add(user)
        app.db.session.commit()
        flash('Congratulations. you are now a registered user!')
        flash("You must be authorized by an administrator to use the kiln.")
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'GET':
        return render_template('reset.html')
    if request.method == 'POST':
        email_address = request.form.get('email')
        user = User.verify_email(email_address)
        if user:
            try:
                email.send_password_reset_link(user)
                flash("An email has been sent to your inbox")
            except Exception as e:
                print(traceback.format_exc())
        else:
            flash("Email address not found", "error")
    return redirect(url_for('login'))

@app.route('/reset_verified/<token>', methods=['GET', 'POST'])
def reset_verified(token):
    form = PasswordResetForm()
    user = User.verify_reset_token(token)
    if not user:
        print('no user found')
        return redirect(url_for('login'))
    password = request.form.get('password')
    if password:
        user.set_password(password)
        app.db.session.commit()
        flash("Password has been reset")
        return redirect(url_for('login'))
    return render_template('reset_verified.html', form=form)

@app.route('/show_jobs', methods = ['GET', 'POST'])
@login_required
def show_jobs():
    ''' display list of all jobs '''
    form = NewJobForm()
    if not current_user.is_auth and not current_user.is_admin:
        flash('You must be authorized by an administrator to use the kiln')
        logout_user()
        return redirect(url_for('login'))
    if form.validate_on_submit():
        name = form.name.data
        comment = form.comment.data
        interval = form.interval.data
        erange = form.erange.data
        drange = form.drange.data
        job = Job(name=name, comment=comment, user_id=current_user.id, 
                    interval=interval, erange=erange, drange=drange,
                    created=datetime.now(), modified=datetime.now())
        app.db.session.add(job)
        app.db.session.commit()
        flash("added job %r" % (name))
    kiln_cmd = kiln_command.KilnCommand()
    running_job_info = None
    running_job_id = None
    running_job_user = None
    run_state, running_job_id, _, _ = kiln_cmd.status()
    if running_job_id is not None:
        running_job_info = model.Job.query.filter_by(id=running_job_id).first()
        if running_job_info is not None:
            running_job_user_id = running_job_info.user_id
            running_job_user = model.User.query.filter_by(id=running_job_user_id).first()
    jobs = model.Job.query.filter_by(user_id=current_user.id)
    form.name.data = ""
    form.comment.data = ""
    return render_template('show_jobs.html', jobs=jobs, run_state=run_state,
                            running_job_id=running_job_id, running_job=running_job_info,
                            running_job_user=running_job_user, form=form)

@app.route('/users', methods = ['GET', 'POST'])
@login_required
def show_users():
    '''display list of users, allow edits'''
    if not current_user.is_admin:
        flash(f"{current_user.username} is not authorized access this page")
        return redirect(url_for('show_jobs'))
    users = model.User.query.all()
    return render_template('show_users.html', users=users)


@app.route('/user', methods = ['GET', 'POST'])
@login_required
def show_user():
    '''display a user\'s info, allow updates'''
    if not current_user.is_auth:
        flash("Unable to update user")
    else:
        form = ShowUserForm()
        if form.validate_on_submit():
            user = model.User.query.filter_by(id=current_user.id).first()
            user.full_name = form.full_name.data
            user.phone_number = form.phone_number.data
            user.email_address = form.email_address.data
            app.db.session.commit()
            flash("User {user.username} updated successfully")
            return redirect(url_for('show_jobs'))
        return render_template('show_user.html', title="update user", form=form)

@app.route('/users/<int:user_id>/update_user', methods = ['GET', 'POST'])
@login_required
def update_user(user_id):
    ''' get form data, update user'''
    user = model.User.query.filter_by(id=user_id).first()
    if not user:
        flash("Unable to update user")
    elif current_user.is_admin or user.id == user_id:
        user.full_name = request.args.get('full_name[%r]' % user_id)
        user.email_address = request.args.get('email_address[%r]' % user_id)
        user.phone_number = request.args.get('phone_number[%r]' % user_id)
        user.is_admin = request.args.get('is_admin[%r]' % user_id) == 'on'
        user.is_auth = request.args.get('is_auth[%r]' %user_id) == 'on'
        app.db.session.commit()
        flash(f"User {user.username} updated successfully")
    else:
        flash(f"{current_user.username} is not authorized access this page")
        return redirect(url_for('show_jobs'))
    if current_user.is_admin:
        users = model.User.query.all()
        return redirect(url_for('show_users', users=users))
    return redirect(url_for('show_jobs'))


@app.route('/users/<int:user_id>/delete_user', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    ''' delete a user '''
    if not current_user.is_admin:
        flash(f"{current_user.username} is not authorized access this page")
        return redirect(url_for('show_jobs'))
    user = model.User.query.filter_by(id=user_id).first()
    app.db.session.delete(user)
    app.db.session.commit()
    users = model.User.query.all()
    return redirect(url_for('show_users', users=users))

def parse_job(job_data):
    ''' parse job data from file - may not be used '''
    steps = []
    for line in job_data.splitlines():
        if line[0] == '#':
            continue
        job_fields = line.split()
        steps.append({
        'target': int(job_fields[1]),
        'rate': int(job_fields[2]),
        'dwell': int(job_fields[3]),
        'threshold': int(job_fields[4]),
        })
    return steps

def add_job(name, interval, erange, drange, comment):
    ''' adds a job to the Job table in the db '''
    job = model.Job(name = name, comment=comment, user_id = current_user.id,
            interval=interval, erange=erange, drange=drange,
            created = datetime.now(), modified = datetime.now())
    flash("adding a job")
    app.db.session.add(job)
    app.db.session.commit()

@app.route('/job/<int:job_id>/steps')
@login_required
def show_job_steps(job_id):
    ''' display job steps '''
    kiln_cmd = kiln_command.KilnCommand()
    run_state, _, _, _ = kiln_cmd.status()
    job = model.Job.query.filter_by(id=job_id).first()
    if not job.user_id == current_user.id:
        flash("Accessing someone else's job is strictly not allowed.")
        flash("This infraction has been logged.")
        return  redirect(url_for('show_jobs'))
    job_steps = model.JobStep.query.filter_by(job_id=job_id).all()
    return render_template('show_job_steps.html', job=job, job_steps=job_steps, run_state=run_state)

@app.route('/job/<int:job_id>/remove_step')
@login_required
def remove_job_step(job_id):
    ''' remove a step from a job '''
    kiln_cmd = kiln_command.KilnCommand()
    run_state, _, _, _ = kiln_cmd.status()
    job = model.Job.query.filter_by(id=job_id).first()
    if not job.user_id == current_user.id:
        flash("Accessing someone else's job is strictly not allowed.")
        flash("This infraction has been logged.")
        return  redirect(url_for('show_jobs'))
    job_steps = model.JobStep.query.filter_by(job_id=job_id).all()
    return render_template('show_job_steps.html', job=job, job_steps=job_steps, run_state=run_state)

@app.route('/job/<int:job_id>/steps/update', methods=['POST'])
@login_required
def update_job_steps(job_id):
    ''' update changes to job steps '''
    job = model.Job.query.filter_by(id=job_id).first()
    if not job.user_id == current_user.id:
        flash("Accessing someone else's job is strictly not allowed.")
        flash("This infraction has been logged.")
        return  redirect(url_for('show_jobs'))
    __update_steps(job)
    flash("Job %s updated" % job.name)
    return redirect(url_for('show_job_steps', job_id=job.id))

def __update_steps(job):
    ''' the internals for update_job_steps '''
    for step_id in request.form.getlist('id'):
        #update existing steps
        target = int(request.form["target[%s]" % step_id])
        rate = int(request.form["rate[%s]" % step_id])
        dwell = int(request.form["dwell[%s]" % step_id])
        threshold = int(request.form["threshold[%s]" % step_id])
        step_record = model.JobStep.query.filter_by(job_id=job.id, id=int(step_id)).first()
        if step_record is None:
            step_record = model.JobStep(job=job, target=target,
                    rate=rate, dwell=dwell, threshold=threshold)
        else: 
            step_record.target = target
            step_record.rate = rate
            step_record.dwell = dwell
            step_record.threshold = threshold
        app.db.session.add(step_record)
        app.db.session.commit()
    #Add a new step
    try:
        target = int(request.form["target"])
        rate = int(request.form["rate"])
        dwell = int(request.form["dwell"])
        threshold = int(request.form["threshold"])
        step_record = model.JobStep(job=job, target=target, rate=rate, dwell=dwell, threshold=threshold)
        app.db.session.add(step_record)
        app.db.session.commit()
    except ValueError:
        flash("All input values must be integers")

@app.route('/job/<int:job_id>/steps/add', methods=['GET'])
@login_required
def add_job_step(job_id):
    ''' add a step to a job '''
    job = model.Job.query.filter_by(id=job_id).first()
    if not job.user_id == current_user.id:
        flash("Accessing someone else's job is strictly not allowed.")
        flash("This infraction has been logged.")
        return  redirect(url_for('show_jobs'))
    __update_steps(job)
    flash("Job step added.")
    return redirect(url_for('show_job_steps', job_id=job_id))

@app.route('/job/<int:job_id>/steps/delete/<int:step_id>', methods=['GET'])
@login_required
def delete_job_step(job_id, step_id):
    ''' delete a step from a job '''
    job = model.Job.query.filter_by(id=job_id).first()
    if not job.user_id == current_user.id:
        flash("Accessing someone else's job is strictly not allowed.")
        flash("This infraction has been logged.")
        return  redirect(url_for('show_jobs'))
    step = model.JobStep.query.filter_by(job_id=job_id, id=step_id).first()
    flash("Job step %d from job %s deleted." % (step_id, job.name))
    app.db.session.delete(step)
    app.db.session.commit()
    return redirect(url_for('remove_job_step', job_id=job_id))

@app.route('/job/<int:job_id>/change_units/<units>', methods=['POST'])
@login_required
def change_units(job_id, units):
    ''' change temperature units from F to C or vice versa '''
    job = model.Job.query.filter_by(id=job_id).first()
    if not job.user_id == current_user.id:
        flash("Accessing someone else's job is strictly not allowed.")
        flash("This infraction has been logged.")
        return redirect(url_for('show_jobs'))
    job.units = units
    app.db.session.commit()
    flash("Units successfully changed to %s" % units)
    return redirect(url_for('show_job_steps', job_id=job_id))

@app.route('/job/<int:job_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_job(job_id):
    ''' delete a job '''
    job = model.Job.query.filter_by(id=job_id).first()
    if not job.user_id == current_user.id:
        flash("Accessing someone else's job is strictly not allowed.")
        flash("This infraction has been logged.")
        return  redirect(url_for('show_jobs'))
    deleted = False
    if request.method == 'POST':
        flash("Job %s deleted." % job.name)
        steps = model.JobStep.query.filter_by(job=job)
        for step in steps:
            app.db.session.delete(step)
        app.db.session.delete(job)
        app.db.session.commit()
        deleted = True
    return render_template('delete_job.html', job=job, deleted=deleted)

@app.route('/job/<int:job_id>/start', methods=['GET', 'POST'])
@login_required
def start_job(job_id):
    ''' start a job '''
    job = model.Job.query.filter_by(id=job_id).first()
    if not job.user_id == current_user.id:
        flash("Accessing someone else's job is strictly not allowed.")
        flash("This infraction has been logged.")
        return  redirect(url_for('show_jobs'))
    started = False
    if request.method == 'POST':
        kiln_cmd = kiln_command.KilnCommand()
        kiln_cmd.start(job_id)
        job_record_thread = threading.Thread(target=_job_record_thread, args=(job, kiln_cmd))
        job_record_thread.start()
        flash(f"Job {job.name} started.")
        started = True
    return render_template('start_job.html', job=job, started=started)

def _job_record_thread(job, kiln_cmd):
    job_status, _, tmeas, setpoint = kiln_cmd.status()
    while job_status == "RUN":
        with app.app_context():
            job_record = JobRecord(job=job, realtime=tm.time(), tmeas=tmeas, setpoint=setpoint)
            app.db.session.add(job_record)
            app.db.session.commit()
            tm.sleep(5)
            job_status, _, tmeas, setpoint = kiln_cmd.status()

@app.route('/job/pause')
@login_required
def pause_job():
    ''' pause a running job '''
    kiln_cmd = kiln_command.KilnCommand()
    kiln_cmd.pause()
    flash("Job paused.")
    return redirect(url_for('show_jobs'))

@app.route('/job/resume')
@login_required
def resume_job():
    ''' resume a paused job '''
    kiln_cmd = kiln_command.KilnCommand()
    kiln_cmd.resume()
    flash("Job resumed.")
    return redirect(url_for('show_jobs'))

@app.route('/job/stop')
@login_required
def stop_job():
    ''' stop a running job '''
    kiln_cmd = kiln_command.KilnCommand()
    kiln_cmd.stop()
    flash("Job stopped.")
    return redirect(url_for('show_jobs'))

''' (c) 2023 Control Physics - all rights reserved '''
