drop table if exists jobs;
create table jobs (
  id integer primary key autoincrement,
  comment text not null,
  created integer not null,
  modified integer
);

drop table if exists job_steps;
create table job_steps (
  id integer primary key autoincrement,
  job_id integer not null,
  target integer not null,
  rate integer not null,
  dwell integer not null,
  threshold integer not null
 ); 
