from kilnweb2 import app, kiln_command, model
from flask import request, render_template

@app.route('/')
def show_jobs():
  kc = kiln_command.KilnCommand()
  run_state, running_job_id = kc.status()
  running_job_info = None
  if running_job_id is not None:
    running_job_info = model.Job.query.filter_by(id=running_job_id).first()
  jobs = model.Job.query.all()
  return render_template('show_jobs.html', jobs=jobs, run_state=run_state, running_job_id=running_job_id, running_job=running_job_info)
