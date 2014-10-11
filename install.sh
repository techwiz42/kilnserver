#!/bin/bash
# Check if we're root
if [ `whoami` != "root" ]; then
  echo "Please run this script as root."
  exit 1
fi

# Check for Python
echo -n "Checking for Python version 2.7 or greater..."
PYTHON_VERSION=( $(python -V 2>&1 | tr '.' ' ') )
if [ ${PYTHON_VERSION[1]} == "2" -a ${PYTHON_VERSION[2]} -ge "7" ]; then
  echo "OK"
else
  echo "FAILED: Found ${PYTHON_VERSION[1]}.${PYTHON_VERSION[2]}"
fi
# Check for Pip
echo -n "Checking for Pip for Python 2.7..."
if dpkg -l python-pip 2>&1 > /dev/null && [ -x /usr/bin/pip-2.7 ]; then
  echo "OK"
else
  echo -n "installing..."
  apt-get install -y python-pip 2>&1 > /dev/null
  echo "OK"
fi
# Check for Flask
echo -n "Checking for Flask..."
if python -c 'from flask import Flask' 2>&1 > /dev/null; then
  echo "OK"
else
  echo -n "installing..."
  pip-2.7 install Flask 2>&1 > /dev/null
  echo "OK"
fi
# Check for Flask-SQLAlchemy
echo -n "Checking for Flask-SQLAlchemy..."
if python -c 'from flask.ext.sqlalchemy import SQLAlchemy' 2>&1 > /dev/null; then
  echo "OK"
else
  echo -n "installing..."
  pip-2.7 install Flask-SQLAlchemy 2>&1 > /dev/null
  echo "OK"
fi
# Check for redis-server
echo -n "Checking for Redis..."
if dpkg -l redis-server 2>&1 > /dev/null && [ -x /usr/bin/redis-server ]; then
  echo "OK"
else
  echo -n "installing..."
  apt-get install -y redis-server 2>&1 > /dev/null
  echo "OK"
fi

echo -n "Checking if redis-server is started on boot..."
if [ -s /etc/rc3.d/S??redis-server ]; then
  echo "OK"
else
  echo -n "configuring..."
  update-rc.d redis-server defaults 2>&1 > /dev/null
  echo "OK"
fi
