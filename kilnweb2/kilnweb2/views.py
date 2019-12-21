#FIXME: flask seems to understand the imports from kilnweb2 but python does not
#FIXME: python wants "from kilnweb2.kilnweb2 import ... " but this doesn't work in flask.
#FIXME: the configuration is out of whack somehow.
from kilnweb2 import app, kiln_command, model
from flask import request, render_template
from flask import request, g, redirect, url_for, render_template, flash
from datetime import datetime, time
from flask_login import current_user, login_user, logout_user, login_required
from kilnweb2.model import db, User, Job
from kilnweb2.forms import RegistrationForm, LoginForm, NewJobForm

# Route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('show_jobs'))
  form = LoginForm()
  if form.validate_on_submit():
    user = User.query.filter_by(username=form.username.data).first()
    if user is None or not user.check_password(form.password.data):
      flash('Invalid username or password')
      return redirect(url_for('login'))
    login_user(user)
    return redirect(url_for('show_jobs'))
  return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
  if current_user.is_authenticated:
    return redirect(url_for('show_jobs'))
  form = RegistrationForm()
  if form.validate_on_submit():
    #Default value for is_admin and is_auth are False. Admin authorizes users access to kilns on page ******* TBD ********
    user = User(username=form.username.data, email_address=form.email.data, full_name=form.full_name.data, phone_number=form.phone_number.data)
    user.set_password(form.password.data)
    #FIXME: should be able to to set default values for is_admin & is_auth in model.
    user.is_auth = 0
    user.is_admin = 0
    db.session.add(user)
    db.session.commit()
    flash('Congratulations. you are now a registered user!')
    return redirect(url_for('login'))
  else:
    return render_template('register.html', title='Register', form=form)

@app.route('/', methods = ['GET', 'POST'])
@login_required
def show_jobs():
  form = NewJobForm()
  if form.validate_on_submit():
    name = form.name.data
    comment = form.comment.data
    job = Job(name=name, comment=comment, user_id=current_user.id, created=datetime.now(),
                    modified=datetime.now())
    db.session.add(job)
    db.session.commit()
    flash("added job %r" % (name))
    return redirect(url_for('show_jobs'))
  kc = kiln_command.KilnCommand()
  run_state, running_job_id = kc.status()
  running_job_info = None
  if running_job_id is not None:
    running_job_info = model.Job.query.filter_by(id=running_job_id).first()
  jobs = model.Job.query.all()
  return render_template('show_jobs.html', jobs=jobs, run_state=run_state, running_job_id=running_job_id, running_job=running_job_info, form=form)

@app.route('/users', methods = ['GET', 'POST'])
@login_required
def show_users():
  if not current_user.is_admin:
    flash("%s is not authorized access this page") % current_user.name
    return redirect(url_for('show_jobs'))
  users = model.User.query.all()
  return render_template('show_users.html', users=users)

@app.route('/update_user', methods = ['GET', 'POST'])
@login_required
def update_user():
  if not current_user.is_admin:
    flash("%s is not authorized access this page") % current_user.name
    return redirect(url_for('show_jobs'))
  flash("update_user was invoked")
  users = model.User.query.all()
  return render_template('show_users.html', users=users)


@app.route('/users/<int:user_id>/delete_user', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
  if not current_user.is_admin:
    flash("%s is not authorized access this page") % current_user.name
    return redirect(url_for('show_jobs'))
  flash("EAT MY SHORTS")
  user = model.User.query.filter_by(id=user_id).first()
  model.db.session.delete(user)
  model.db.session.commit()
  users = model.User.query.all()
  return render_template('show_users.html', users=users)

def parse_job(job_data):
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

def add_job(name, comment):
  job = model.Job(name = name, comment=comment, user_id = current_user.id, created = datetime.now(), modified = datetime.now())
  flash("adding a job")
  model.db.session.add(job)
  model.db.session.commit()


@app.route('/job/<int:job_id>/steps')
@login_required
def show_job_steps(job_id):
  job = model.Job.query.filter_by(id=job_id).first()
  job_steps = model.JobStep.query.filter_by(job_id=job_id).all()
  return render_template('show_job_steps.html', job=job, job_steps=job_steps)

@app.route('/job/<int:job_id>/steps/update', methods=['POST'])
@login_required
def update_job_steps(job_id):
  job = model.Job.query.filter_by(id=job_id).first()
  for step_id in request.form.getlist('id'):
    target = int(request.form["target[%s]" % step_id])
    rate = int(request.form["rate[%s]" % step_id])
    dwell = int(request.form["dwell[%s]" % step_id])
    threshold = int(request.form["threshold[%s]" % step_id])
    step_record = model.JobStep.query.filter_by(job_id=job_id, id=int(step_id)).first()
    if step_record is None:
      step_record = model.JobStep(job=job, target=target, rate=rate, dwell=dwell, threshold=threshold)
    else:
      step_record.target = target
      step_record.rate = rate
      step_record.dwell = dwell
      step_record.threshold = threshold
    model.db.session.add(step_record)
  model.db.session.commit()
  flash("Job %s updated" % job.name)
  return redirect(url_for('show_job_steps', job_id=job.id))


@app.route('/job/<int:job_id>/steps/add', methods=['GET'])
@login_required
def add_job_step(job_id):
  job = model.Job.query.filter_by(id=job_id).first()
  step = model.JobStep(job=job, target=0, rate=0, dwell=0, threshold=0)
  model.db.session.add(step)
  model.db.session.commit()
  flash("Job step added.")
  return redirect(url_for('show_job_steps', job_id=job_id))

@app.route('/job/<int:job_id>/steps/delete/<int:step_id>', methods=['GET'])
@login_required
def delete_job_step(job_id, step_id):
  job = model.Job.query.filter_by(id=job_id).first()
  step = model.JobStep.query.filter_by(job_id=job_id, id=step_id).first()
  flash("Job step %d from job %s deleted." % (step_id, job.name))
  model.db.session.delete(step)
  model.db.session.commit()
  return redirect(url_for('show_job_steps', job_id=job_id))

@app.route('/job/<int:job_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_job(job_id):
  job = model.Job.query.filter_by(id=job_id).first()
  deleted = False
  if request.method == 'POST':
    flash("Job %s deleted." % job.name)
    steps = model.JobStep.query.filter_by(job=job)
    for step in steps:
      model.db.session.delete(step)
    model.db.session.delete(job)
    model.db.session.commit()
    deleted = True
  return render_template('delete_job.html', job=job, deleted=deleted)

@app.route('/job/<int:job_id>/start', methods=['GET', 'POST'])
@login_required
def start_job(job_id):
  job = model.Job.query.filter_by(id=job_id).first()
  started = False
  if request.method == 'POST':
    kc = kiln_command.KilnCommand()
    kc.start(job_id)
    flash("Job %s started." % job.name)
    started = True
  return render_template('start_job.html', job=job, started=started)

@app.route('/job/pause')
@login_required
def pause_job():
  kc = kiln_command.KilnCommand()
  kc.pause()
  flash("Job paused.")
  return redirect(url_for('show_jobs'))

@app.route('/job/resume')
@login_required
def resume_job():
  kc = kiln_command.KilnCommand()
  kc.resume()
  flash("Job resumed.")
  return redirect(url_for('show_jobs'))

@app.route('/job/stop')
@login_required
def stop_job():
  kc = kiln_command.KilnCommand()
  kc.stop()
  flash("Job stopped.")
  return redirect(url_for('show_jobs'))


