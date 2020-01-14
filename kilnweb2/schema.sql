drop table if exists jobs;
create table jobs (
  id integer primary key autoincrement,
  user_id integer not null,
  name text not null,
  comment text not null,
  created integer not null,
  modified integer,
  units integer default 1 not null
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

drop table if exists users;
create table users(
  id integer primary key autoincrement,
  username text not null,
  is_admin integer,
  is_auth integer,
  full_name text,
  email_address text not null,
  phone_number text,
  password_hash  text
);

insert into users(username) values=('admin');

