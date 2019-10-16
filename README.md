***Server for thermocouple/fuzzy-logic kiln control project.***

Roger's description of work to be done:

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
* Restart:  Start program from wherever stop happened & confirm
* Sleep:  Put controller to sleep
* Units:  Farenheit or Celsius
* Status:  Get segment, temperature, time to complete from controller, and any error records

**Screen 2:**
* Scrollable table:  Columns:  
** Segment Number, 
** Target Temperature, 
** Ramp Rate, 
** Dwell Time, 
** Alarm Limit  (alarm limit is a temperature measurement limit, which, if too high, causes program to wait till temp goes down to acceptable level)  
** Special code for 'Done'.
* Rows:  added as needed, always have one blank row below ones already entered, so you can add another.

