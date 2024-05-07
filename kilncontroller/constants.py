START = 'START' 
RUN = 'RUN'
PAUSE = 'PAUSE'
RESUME = 'RESUME'
STOP = 'STOP'
STATUS = 'STATUS'
SOCK_PATH = '/tmp/kiln_controller'
FARENHEIT = 'F'
CELCIUS = 'C'

FUDGE_FACTOR = 1.0

HEAT4 = 1.0 * FUDGE_FACTOR
HEAT3 = 0.75 * FUDGE_FACTOR
HEAT2 = 0.5 * FUDGE_FACTOR
HEAT1 = 0.25 * FUDGE_FACTOR

# These are the pin numbers of the physical pins on the RPi header.
# You may choose any three GPIO pins, but the pins chosen must be
# wired to the correct lead on the MAX3185 thermocouple.
CLK = 40
CS = 36
DO = 38
GPIO_PIN = 31

# (c) 2023 Roger carr - all rights reserved
