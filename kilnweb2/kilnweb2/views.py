#FIXME: flask seems to understand the imports from kilnweb2 but python does not
#FIXME: python wants "from kilnweb2.kilnweb2 import ... " but this doesn't work in flask.
#FIXME: the configuration is out of whack somehow.
from kilnweb2 import app, kiln_command, model
from flask import request, render_template
from flask import request, g, redirect, url_for, render_template, flash
from datetime import datetime, time
from flask_login import current_user, login_user, logout_user, login_required
from kilnweb2.model import db, User
from kilnweb2.forms import RegistrationForm

# Route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    if current_user.is_authenticated:
      return redirect(url_for('show_jobs'))
    form = request.form
    #FIXME: create admin account in db - not hard-coded like so
    if form['username'] != 'admin' or form['password'] != 'admin':
      if True:
        user = User.query.filter_by(username=form['username']).first()
        if user is None or not user.check_password(form['password']):
          flash('Invalid Credentials. Please try again.')
          return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('show_jobs'))
    else:
      return redirect(url_for('show_jobs'))
  return render_template('login.html')

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
    user = User(username=form.username.data, email_address=form.email.data, full_name=form.full_name.data, phone_number=form.phone_number.data)
    user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()
    flash('Congratulations, you are now a registered user!')
    return redirect(url_for('login'))
  else:
    return render_template('register.html', title='Register', form=form)

@app.route('/')
@login_required
def show_jobs():
  kc = kiln_command.KilnCommand()
  run_state, running_job_id = kc.status()
  running_job_info = None
  if running_job_id is not None:
    running_job_info = model.Job.query.filter_by(id=running_job_id).first()
  jobs = model.Job.query.all()
  return render_template('show_jobs.html', jobs=jobs, run_state=run_state, running_job_id=running_job_id, running_job=running_job_info)


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

@app.route('/job/create', methods=['POST', 'GET'])
@login_required
def job_create():
  cursor = model.db.cursor()
  cursor.execute('''INSERT INTO jobs (comment,created) VALUES (?,?)''', [request.form['comment'], int(time.time())])
  model.db.commit()
  job_id = cursor.lastrowid
  for step in parse_job(request.form['job_data']):
    cursor.execute('insert into job_steps (job_id, target, rate, dwell, threshold) values (?, ?, ?, ?, ?)',
                   [job_id, step['target'], step['rate'], step['dwell'], step['threshold']])
  model.db.commit()
  flash('Successfully created job "%s" (%d)' % (request.form['comment'], job_id))
  return redirect(url_for('show_jobs'))


@app.route('/job/add')
@login_required
def add_job():
  job = model.Job('', datetime.now(), datetime.now())
  model.db.session.add(job)
  model.db.session.commit()
  return redirect(url_for('show_job_steps', job_id=job.id))


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
  job.comment = request.form['comment']
  model.db.session.add(job)
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
  flash("Job %s updated" % job.comment)
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
  flash("Job step %d from job %s deleted." % (step_id, job.comment))
  model.db.session.delete(step)
  model.db.session.commit()
  return redirect(url_for('show_job_steps', job_id=job_id))

@app.route('/job/<int:job_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_job(job_id):
  job = model.Job.query.filter_by(id=job_id).first()
  deleted = False
  if request.method == 'POST':
    flash("Job %s deleted." % job.comment)
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
    flash("Job %s started." % job.comment)
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


