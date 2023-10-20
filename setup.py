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
    version = "1.0.0",
    authors = "Robert Liesenfeld and Peter Sisk",
    author_email = "xunil@xunil.net, thetechwizard42@gmail.com",
    description = ("Daemon and web interface for controlling heat-treating and ceramics kilns."),
    license = "Proprietary - contact Roger Carr roger.carr1@gmail.com",
    keywords = "thermocouple fuzzy-logic heat-treat kiln",
    url = "http://xunil.net/",
    packages = ['kilncontroller', 'kilnweb2'],
    package_data = {
      'kilnweb2': ['static/*.css', 'templates/*.html'],
    },
    install_requires = [
        "alembic==1.12.0",
        "astroid==2.15.6",
        "blinker==1.6.2",
        "click==8.1.7",
        "Cython==3.0.2",
        "dill==0.3.7",
        "dnspython==2.4.2",
        "dominate==2.8.0",
        "email-validator==2.0.0.post2",
        "Flask==2.3.3",
        "Flask-Bootstrap==3.3.7.1",
        "Flask-Login==0.6.2",
        "Flask-Migrate==4.0.5",
        "Flask-SQLAlchemy==3.1.1",
        "Flask-WTF==1.1.1",
        "Flask-Login",
        "Flask-Bootstrap",
        "Flask-Mail==0.9.1",
        "flask-wtf==1.2.1",
        "greenlet==3.0.0rc3",
        "idna==3.4",
        "isort==5.12.0",
        "itsdangerous==2.1.2",
        "Jinja2==3.1.2",
        "kilnserver==1.0.0",
        "kilnweb2==1.0.0",
        "lazy-object-proxy==1.9.0",
        "Mako==1.2.4",
        "MarkupSafe==2.1.3",
        "mccabe==0.7.0",
        "numpy==1.26.0rc1",
        "platformdirs==3.10.0",
        "pylint==2.17.5",
        "pylint-flask==0.6",
        "pylint-plugin-utils==0.8.2",
        "PyJWT==2.8.0",
        "PyTest",
        "SQLAlchemy==2.0.20",
        "tomli==2.0.1",
        "tomlkit==0.12.1",
        "typing_extensions==4.8.0rc1",
        "visitor==0.1.3",
        "Werkzeug==2.3.7",
        "wrapt==1.15.0",
        "WTForms==3.0.1"
    ],
    entry_points = {
        'console_scripts': [
            'kilnweb2= kilnweb2:main',
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
"""(c) 2023 Roger Carr - all rights reserved"""

