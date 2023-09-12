**Server for thermocouple/fuzzy-logic kiln control project.**

**The Architecture**
* Kilncontroller runs on the Raspberry Pi and talks to the thermocouple.
* Kilnweb is a Flask application that controls the web-based UI.

I've put the kinlweb component into kilnweb2, which is structured somewhat differently from the way that 
Rob originally structured the project.
See this page: https://flask.palletsprojects.com/en/1.1.x/patterns/packages/ for instructions on how to 
set up, initialize and run kilnweb2.  Note that the kilnweb2 directory structure looks like this:

Install virtualenvwrapper on your device if it is not already installed and create a virtual environment for the project.
then run setup.py:

~~~
python setup.py install
~~~

If you have not yet cloned the project onto your device, get it from github by:

~~~
git clone https://github.com/techwiz42/kilnserver.git
~~~

The directory structure of kilnweb2, the web server part of the project should look like this:

~~~
/kilnweb2
  /internals
    /static
    /templates
    __init__.py
    kiln_command.py
    model.py
    views.py
~~~    

The database has been moved from /tmp/kilnweb.db to the kilnweb2/kilnweb2/kilnweb.db.  
It is initialized from the command line by invoking 
~~~
flask db init
flask db migrate
flask db upgrade
~~~

For the image supplied with the project, invoke the virtual environment in a command window. The virtual environment can be invoked from any directory. Invoke it like so:

~~~
>workon kilnsvr
~~~ 

The kilncontroller must be run with root privileges. Change directory to the top level directory, be sure to activate the virtual environment and start the kilncontroller:

~~~
>sudo python ./main.py
~~~

Initialize kilnweb2 by changing to the kilnweb2 directory and running 
~~~
python setup.py install
~~~
Note that this needs only to be run once.

The flask app lives in kilncontroller/kilnweb2/kilnweb2/\__init__.py and is invoked from a command window.  cd to the upper-level
kilnweb2 directory and invoke. Be sure to run in the appropriate virtual environment.

~~~
>flask run
~~~
Note that the environment variables and setup specified in the web page referenced above must exist in order for the project to run.

Kilncontroller must be running before kilnweb requests can be processed.  Kilncontroller is listening
on a unix socket for commands from kilnweb.  Kilnweb invokes commands on the kilncontroller by sending
requests to to the socket. It also listens on the socket for responses from the kilncontroller.

See also this tutorial for comprehensive Flask how-to:
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins

**The Project**

Run under python3 in a virtual environment.

Kilncontroller must be running before kilnweb can be started. If kilncontroller is not running,
all kilnweb calls will result in a *connection refused* error

Kilncontroller is listening on a unix socket for commands from kilnweb.  Kilnweb makes RESTful API calls to the socket.

**The API inherited from Rob's project:**
* **server:5000/** - shows Kiln Server Status
* **server:5000/job/create**
* **server:5000/job/add** 
* **server:5000/job/<job_id>/steps** shows job's steps
* **server:5000/job/<job_id>/steps/update** update job's steps
* **server:5000/job/<job_id>/steps/add** add a step to a job
* **server:5000/job/<job_id>/steps/delete/<step_id>** delete a step from a job
* **server:5000/job/<job_id>/delete** delete a job
* **server:5000/job/<job_id>/start** starts a job
* **server:5000/job/pause** pauses current job (what does this mean, 'pause'?)
* **server:5000/job/resume** resumes the paused job
* **server:5000/job/stop** stops the current job

**Roger's requested enhancements to the client:**

>I imagined that there would be two screens, which you could toggle between.  Screen 1 is a bunch of command buttons, and Screen 2 is the data table.
>
>**Screen 1:   Commands**
>* Wakeup/Reset  Establish connection to temperature programmer via WiFi & hand shake, reset. ## DONT UNDERSTAND THIS - DO YOU MEAN THE RPI SHOULD BE A WIFI ACCESS POINT? ##
>* NewProgram:  ~~Start new program and give it a name (bring up kb to allow user to type name)~~
>* Store:  ~~Store the program you are working on in RPi memory~~
>* Recall:  ~~Recall a program by name from RPi memory – bring up scroll table of all programs~~
>* Delete:  ~~Delete a program by name from Rpi memory~~
>* Setup:  Go to screen 2 to set up temperature program
>* Review:   Review program data
>* Start:  Send start command to controller- start from beginning of program
>* Delay:  Set later time for start to commence
>* Stop:  Immediate stop & confirm
>* Restart:  Start program from wherever stop happened & confirm
>* Sleep:  Put controller to sleep
>* Units:  Farenheit or Celsius
>* Status:  Get segment, temperature, time to complete from controller, and any error records
>
>Screen 2:
>* Scrollable table:  Columns:  Segment Number, Target Temperature, Ramp Rate, Dwell Time, Alarm Limit  (alarm limit is a temperature measurement limit, which, if too high, causes program to wait till temp goes down to acceptable level)  Special code for 'Done'.
>* Rows:  added as needed, always have one blank row below ones already entered, so you can add another.
>* Numerical Keypad to allow user to enter values into table entry that is touch highlighted.
>* ”+” button to allow user to add new table entry, possible “–“  button to allow user to delete segment
>* Back to Screen 1 button

**In addition to Roger's requested changes, add the following features:**
* ~~basic auth and the concept of _'user'_ so multiple users can securely save programs to a single 
kilncontroller.~~ 
* Since multiple users can access the kiln controller and there is only a single kiln to control, 
there needs to be some mechanism for a user to 'own' a kiln while it's running. 
* **Question for Roger**: should users be able to queue kiln jobs?  Reserve time on kiln? ## NO ## 
* **Question for Roger**: should the kilncontroller be able to talk with multiple kilns? ## NO ##
* Unit tests are required for kilnweb2 and kilncontrolller modules
* Run pylint or similar to ensure code uniformity and adherence to proper python programming standards and conventions
