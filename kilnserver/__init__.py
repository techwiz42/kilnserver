# all the imports
import os
import sqlite3
import time
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from celery import Celery
import subprocess
from subprocess import PIPE


app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
  DATABASE=os.path.join(app.root_path, 'kilnserver.db'),
  DEBUG=True,
  SECRET_KEY='099d77359a8c14d35c440b1589570f99',
  CELERY_BROKER_URL='redis://localhost:6379/0'
))
app.config.from_envvar('KILNSERVER_SETTINGS', silent=True)

def make_celery(app):
    app.logger.debug("app.import_name=%s" % app.import_name)
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

def connect_db():
  """Connects to the specific database."""
  rv = sqlite3.connect(app.config['DATABASE'])
  rv.row_factory = sqlite3.Row
  return rv

def init_db():
  with app.app_context():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
      db.cursor().executescript(f.read())
    db.commit()

def get_db():
  """Opens a new database connection if there is none yet for the
  current application context.
  """
  if not hasattr(g, 'sqlite_db'):
    g.sqlite_db = connect_db()
  return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
  """Closes the database again at the end of the request."""
  if hasattr(g, 'sqlite_db'):
      g.sqlite_db.close()

@app.route('/')
def show_jobs():
  db = get_db()
  cur = db.execute('''SELECT j.id, j.comment, count(js.id) AS step_count
                        FROM jobs j
                   LEFT JOIN job_steps js ON js.job_id = j.id
                    GROUP BY j.id, j.comment
                    ORDER BY j.id DESC''')
  jobs = cur.fetchall()
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
  db = get_db()
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
  db = get_db()
  cursor = db.cursor()
  cursor.execute('select id,comment from jobs where id=?', [job_id])
  job = cursor.fetchone()
  cursor.execute('''SELECT * FROM job_steps js WHERE js.job_id=?''', [job_id])
  job_steps = cursor.fetchall()
  return render_template('show_job_steps.html', job=job, job_steps=job_steps)

@app.route('/job/<int:job_id>/delete', methods=['GET', 'POST'])
def delete_job(job_id):
  db = get_db()
  cursor = db.cursor()
  cursor.execute('select id,comment from jobs where id=?', [job_id])
  job = cursor.fetchone()
  deleted = False
  if request.method == 'POST':
    # perform the delete
    cursor.execute('''DELETE FROM job_steps WHERE job_id=?''', [job_id])
    cursor.execute('''DELETE FROM jobs WHERE id=?''', [job_id])
    db.commit()
    flash("Job %s deleted." % job['comment'])
    deleted = True
  return render_template('delete_job.html', job=job, deleted=deleted)

@app.route('/job/<int:job_id>/start', methods=['GET', 'POST'])
def start_job(job_id):
  db = get_db()
  cursor = db.cursor()
  cursor.execute('select id,comment from jobs where id=?', [job_id])
  job = cursor.fetchone()
  started = False
  if request.method == 'POST':
    # start the job
    result = task_start_job.delay(job_id)
    flash("Job %s started." % job['comment'])
    started = True
  return render_template('start_job.html', job=job, started=started)

@celery.task()
def task_start_job(job_id):
  args = ['/bin/sleep', '120']
  p = subprocess.Popen(args, stdout=PIPE, stderr=PIPE)
  out, err = p.communicate()
  app.logger.debug("start_job: subprocess output: %s" % [out])

if __name__ == '__main__':
  app.run()
