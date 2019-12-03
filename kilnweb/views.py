import time
from kilnweb import app
from kilnweb import kiln_command
from kilnweb import model #import db, Job, JobStep
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from datetime import datetime

@app.route('/', methods=["POST","GET"])
def show_jobs():
  return "HELLOOOOOO"
  # kc = kiln_command.KilnCommand()
  # run_state, running_job_id = kc.status()
  # running_job_info = None
  # if running_job_id is not None:
  #   running_job_info = model.Job.query.filter_by(id=running_job_id).first()
  # jobs = model.Job.query.all()
  # return render_template('show_jobs.html', jobs=jobs, run_state=run_state, running_job_id=running_job_id, running_job=running_job_info)

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
def job_create():
  cursor = model.db.cursor()
  cursor.execute('''INSERT INTO jobs (comment,created) VALUES (?,?)''', [request.form['comment'],int(time.time())])
  model.db.commit()
  job_id = cursor.lastrowid
  for step in parse_job(request.form['job_data']):
    cursor.execute('insert into job_steps (job_id, target, rate, dwell, threshold) values (?, ?, ?, ?, ?)',
      [job_id, step['target'], step['rate'], step['dwell'], step['threshold']])
  model.db.commit()
  flash('Successfully created job "%s" (%d)' % (request.form['comment'], job_id))
  return redirect(url_for('show_jobs'))

@app.route('/job/add')
def add_job():
  job = model.Job('', datetime.now(), datetime.now())
  model.db.session.add(job)
  model.db.session.commit()
  return redirect(url_for('show_job_steps', job_id=job.id))

@app.route('/job/<int:job_id>/steps')
def show_job_steps(job_id):
  job = model.Job.query.filter_by(id=job_id).first()
  job_steps = model.JobStep.query.filter_by(job_id=job_id).all()
  return render_template('show_job_steps.html', job=job, job_steps=job_steps)

@app.route('/job/<int:job_id>/steps/update', methods=['POST'])
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
def add_job_step(job_id):
  job = model.Job.query.filter_by(id=job_id).first()
  step = model.JobStep(job=job, target=0, rate=0, dwell=0, threshold=0)
  model.db.session.add(step)
  model.db.session.commit()
  flash("Job step added.")
  return redirect(url_for('show_job_steps', job_id=job_id))

@app.route('/job/<int:job_id>/steps/delete/<int:step_id>', methods=['GET'])
def delete_job_step(job_id, step_id):
  job = model.Job.query.filter_by(id=job_id).first()
  step = model.JobStep.query.filter_by(job_id=job_id, id=step_id).first()
  flash("Job step %d from job %s deleted." % (step_id, job.comment))
  model.db.session.delete(step)
  model.db.session.commit()
  return redirect(url_for('show_job_steps', job_id=job_id))

@app.route('/job/<int:job_id>/delete', methods=['GET', 'POST'])
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
def pause_job():
  kc = kiln_command.KilnCommand()
  kc.pause()
  flash("Job paused.")
  return redirect(url_for('show_jobs'))

@app.route('/job/resume')
def resume_job():
  kc = kiln_command.KilnCommand()
  kc.resume()
  flash("Job resumed.")
  return redirect(url_for('show_jobs'))

@app.route('/job/stop')
def stop_job():
  kc = kiln_command.KilnCommand()
  kc.stop()
  flash("Job stopped.")
  return redirect(url_for('show_jobs'))
