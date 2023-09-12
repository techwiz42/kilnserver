import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "kilnserver",
    version = "0.0.20",
    authors = "Robert Liesenfeld and Peter Sisk",
    author_email = "xunil@xunil.net, bartelby@gmail.com",
    description = ("Daemon and web interface for controlling heat-treating and ceramics kilns."),
    license = "Proprietary",
    keywords = "thermocouple fuzzy-logic heat-treat kiln",
    url = "http://xunil.net/",
    packages = ['kilncontroller', 'kilnweb2', 'stub', 'stub.RPi'],
    package_data = {
      'kilnweb': ['static/*.css', 'templates/*.html'],
    },
    install_requires = [
      'cython',  
      'Flask >= 1.1.1',
      'flask-sqlalchemy',
      'numpy >= 1.7.1',
      'flask-login',
      'flask-wtf',
      'werkzeug >= 1.0',
      'flask_bootstrap',
      'flask-migrate',
      'email_validator'  
    ],
    entry_points = {
        'console_scripts': [
            'kilnweb = kilnweb:main',
            'kilncontroller = kilncontroller:main',
        ],
    },
    long_description = read('README.md'),
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Topic :: Utilities",
        "License :: Other/Proprietary License",
    ],
)
