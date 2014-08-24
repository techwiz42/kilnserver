import time
from kilnserver import app
from kilnserver.model import db, Job, JobStep
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

@app.route('/')
def show_jobs():
  jobs = Job.query.all()
  return render_template('show_jobs.html', jobs=jobs)

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
    
@app.route('/job/create', methods=['POST'])
def job_create():
  cursor = db.cursor()
  cursor.execute('''INSERT INTO jobs (comment,created) VALUES (?,?)''', [request.form['comment'],int(time.time())])
  db.commit()
  job_id = cursor.lastrowid
  for step in parse_job(request.form['job_data']):
    cursor.execute('insert into job_steps (job_id, target, rate, dwell, threshold) values (?, ?, ?, ?, ?)',
      [job_id, step['target'], step['rate'], step['dwell'], step['threshold']])
  db.commit()
  flash('Successfully created job "%s" (%d)' % (request.form['comment'], job_id))
  return redirect(url_for('show_jobs'))

@app.route('/job/<int:job_id>/steps')
def show_job_steps(job_id):
  job = Job.query.filter_by(id=job_id).first()
  job_steps = JobStep.query.filter_by(job_id=job_id).all()
  return render_template('show_job_steps.html', job=job, job_steps=job_steps)

@app.route('/job/<int:job_id>/delete', methods=['GET', 'POST'])
def delete_job(job_id):
  job = Job.query.filter_by(id=job_id).first()
  deleted = False
  if request.method == 'POST':
    flash("Job %s deleted." % job.comment)
    db.session.delete(job)
    db.session.commit()
    deleted = True
  return render_template('delete_job.html', job=job, deleted=deleted)

@app.route('/job/<int:job_id>/start', methods=['GET', 'POST'])
def start_job(job_id):
  job = Job.query.filter_by(id=job_id).first()
  started = False
  if request.method == 'POST':
    # TODO: implement starting the job
    flash("Job %s started." % job.comment)
    started = True
  return render_template('start_job.html', job=job, started=started)

