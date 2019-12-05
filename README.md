**Server for thermocouple/fuzzy-logic kiln control project.**

**The Architecture**
* Kilncontroller runs on the Raspberry Pi and talks to the thermocouple.
* Kilnweb is a Flask application that controls the web-based UI.

Kilncontroller must be running before kilnweb can be started.  Kilncontroller is listening
on a unix socket for commands from kilnweb.  Kilnweb makes RESTful API calls to the socket.

**The Project**
Best run under python3 in a virtual environment.

Kilncontroller must be running before kilnweb can be started.  Kilncontroller is listening
on a unix socket for commands from kilnweb.  Kilnweb makes RESTful API calls to the socket.

Roger's description of work to be done on the client:

I imagined that there would be two screens, which you could toggle between.  Screen 1 is a bunch of command buttons, and Screen 2 is the data table.

**Screen 1:   Commands**
* Wakeup/Reset  Establish connection to temperature programmer via WiFi & hand shake, reset.
* NewProgram:  Start new program and give it a name (bring up kb to allow user to type name)
* Store:  Store the program you are working on in RPi memory
* Recall:  Recall a program by name from RPi memory – bring up scroll table of all programs
* Delete:  Delete a program by name from Rpi memory
* Setup:  Go to screen 2 to set up temperature program
* Review:   Review program data
* Start:  Send start command to controller- start from beginning of program
* Delay:  Set later time for start to commence
* Stop:  Immediate stop & confirm
* Restart:  Start pro