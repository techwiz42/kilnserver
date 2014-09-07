import time
from kilnserver import app
from kilnserver.model import db, Job, JobStep
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import redis

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
    # TODO: Redis connection should be global
    # TODO: RedisState should probably handle all of this
    r = redis.Redis()
    r.lpush('jobs', job_id)
    flash("Job %s started." % job.comment)
    started = True
  return render_template('start_job.html', job=job, started=started)

@app.route('/job/status/all', methods=['GET', 'POST'])
def job_status_all():
  r = redis.Redis()
  running_job_keys = r.lrange('running_jobs', 0, -1)
  running_jobs = list()
  job_info = dict()
  for key in running_job_keys:
    rj = r.hgetall(key)
    rj['start_time'] = time.ctime(float(rj['start_time']))
    running_jobs.append(rj)
    if not rj['job_id'] in job_info:
      job_info[rj['job_id']] = Job.query.filter_by(id=rj['job_id']).first()
  return render_template('job_status_all.html', running_jobs=running_jobs, job_info=job_info)
