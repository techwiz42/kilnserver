''' The main KilnController module '''
import os
import sys
import socket
import time
import math
import threading
import json
import logging
from numpy import empty
import max31855 as mx

try:
    import RPi.GPIO as GPIO
    print("Raspberry Pi GPIO found")
except ImportError:
    # Assume we're not running on Pi hardware, import stub instead
    # This is for development and testing only.
    import stubGPIO as GPIO
    print("Raspberry Pi GPIO NOT FOUND - running stub")

RUN = 'RUN'
PAUSE = 'PAUSE'
STOP = 'STOP'
SOCK_PATH = '/tmp/kiln_controller'
FARENHEIT = 'F'
CELCIUS = 'C'
# These are the pin numbers of the physical pins on the RPi header.
# Choose any three GPIO pins, but the values here must be consistent 
# with the leads on the MAX31855 thermocouple.
CLK = 40 
CS = 36
DO = 38

class KilnController:
    '''This is the class that encapsulates the command structure for the kiln controller'''
    def __init__(self, segments, units, conn):
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('/tmp/kilncontroller.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler) 
        self.logger.setLevel(logging.DEBUG)
        self.conn = conn
        self.segments = segments
        self.run_state = None
        self.job_id = None  # this is the ID of the running job, if any.
        self.units = units
        self.build_temp_table(self.units)
        #set the GPIO pin to LOW, cuz my driver chip is inverting, so net active HIGH
        self.gpio_pin = 26   #this is the pin number, not the GPIO channel number -
        GPIO.cleanup() # just in case
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)  #HIGH is on, LOW is off

    def __del__(self):
        GPIO.cleanup()

    def run_state(self):
        return self.run_state

    def pause(self):
        self.run_state = PAUSE

    def resume(self):
        self.run_state = RUN

    def stop(self):
        self.run_state = STOP

    def read_temp(self):
        thermocouple = mx.MAX31855(CLK,CS,DO, 'f', board=GPIO.BOARD)
        temp = thermocouple.get()
        self.logger.debug(f"temp: {temp}")
        return float(temp)

    # returns seconds
    def duration(self):
        seconds = 0
        prev_target = 0
        for segment in self.segments:
            ramp = abs(segment['target'] - prev_target) / segment['rate']
            seconds += ramp + segment['dwell']
            prev_target = segment['target']
        return round(seconds)

    # NOTE that the internal units of the temp table are F.
    # Job Steps are stored in the database as either C or F and
    # Are converted to F here. the to_F() function does the conversion
    def build_temp_table(self, units):
        start_temp = self.to_F(self.read_temp())
        self.logger.debug(f"start_temp is {repr(start_temp)} degrees F")
        previous_target = start_temp
        self.temp_table = [start_temp]
        for segment in self.segments:
            rate = repr(self.to_F(segment['rate']))
            target = repr(self.to_F(segment['target']))
            dwell = repr(self.to_F(segment['dwell']))
            self.logger.debug(f"segment: rate: {rate} target: {target} dwell: {dwell})")
            rate_mins = self.to_F(segment['rate']) / 60.0
            ramp = int(round(abs((self.to_F(segment['target']) - previous_target) / rate_mins)))
            j = 1
            t = 0
            for m in range(t, t + int(ramp)):
                self.temp_table.append((self.to_F(segment['target']) - previous_target) *
                        j / ramp + previous_target)
                j += 1
            for m in range(t + int(ramp), t + int(ramp + segment['dwell'])):
                self.temp_table.append(self.to_F(segment['target']))
                j += 1
            t = round(t + ramp + segment['dwell'])
            previous_target = self.to_F(segment['target'])

    def set_point(self):
        seconds = self.runtime - self.pausetime
        minute = int(math.floor(seconds / 60))
        dT = self.temp_table[minute+1] - self.temp_table[minute]
        dt = seconds / 60 - minute
        return self.temp_table[minute] + dT * dt

    def kiln_on(self):
        GPIO.output(self.gpio_pin, GPIO.HIGH)

    def kiln_off(self):
        GPIO.output(self.gpio_pin, GPIO.LOW)

    # Convert celsius temperatures to Farenheit. If units are already F, don't convert.
    def to_F(self, temperature):
        if self.units == 'F':
            return temperature
        return temperature * 9 / 5 + 32

    def run(self):
        self.run_state = RUN
        self.start = time.time()
        m = empty((5,5),dtype=float)*0    # degree of membership matrix

        interval = 5  #interval between updates, seconds
        erange = 5  # default error range +/- 5
        drange = 5 #default delta range
        lasterr = 0

        hhhh = 1.00   # these heating values will have to be adjusted, or not
        hhh = 0.75
        hh = 0.50
        h = 0.25
        proportion = 1 #proportion of time heat is on - overall rate limit

        # Data collection for graphing
        self.runtime = 0   # seconds
        self.pausetime = 0   # seconds
        tempdata = [self.read_temp()]
        setdata = [self.set_point()]
        timedata = [self.runtime]

        while (self.runtime - self.pausetime) < self.duration():
        # Check run_state:
            if self.run_state == PAUSE:
                time.sleep(interval)
                self.pausetime += interval
            elif self.run_state == STOP:
                return
            elif self.run_state == RUN:
                pass
            else:
                raise "Unknown run state '%s'" % (self.run_state)
      
            # find error and delta-error
            tmeas = self.read_temp()   # degrees F
            setpoint = self.set_point()  # degrees F
            e = tmeas - setpoint # present error degrees F
            d = e - lasterr # positive for increasing error, neg for decreasing error - degrees F
            self.logger.debug("e = %.3f, d = %.3f"  % (e, d))
            self.logger.debug("measured temperature = %.3f,  setpoint =  %.3f"  % (tmeas, setpoint))
            lasterr = e

            tempdata.append(tmeas)   #record data for plotting later
            setdata.append(setpoint)
            timedata.append(self.runtime)

            # find degree of membership in the 5 membership functions for e and d
            # make sure universe of discourse is large enough by increasing its size if e
            # or d lie outside the default range.

            if e > erange:
                erange = e  #adjust universe of discourse if error is outside present range
            if e < -erange:
                erange = -e  
            if d > drange:
                drange = d  #same for d
            if d < -drange:
                drange = -d

            #    print"erange = ", erange, "   drange = ", drange

            #generate 5 entry degree of membership lists for each of 4 regions, for e and d
            if (e >= -erange) & (e < -erange/2):
                dome = [-2*e/erange -1,2*e/erange +2,0,0,0]
            if (e >= -erange/2) & (e < 0):
                dome = [0,-2*e/erange,2*e/erange +1,0,0]
            if (e >= 0) & (e < erange/2):
                dome = [0,0,-2*e/erange +1,2*e/erange ,0]
            if (e >= erange/2) & (e <= erange):
                dome = [0,0,0,-2*e/erange +2,2*e/erange -1]

            if (d >= -drange) & (d < -drange/2):
                domd = [-2*d/drange -1,2*d/drange +2,0,0,0]
            if (d >= -drange/2) & (d < 0):
                domd = [0,-2*d/drange,2*d/drange +1,0,0]
            if (d >= 0) & (d < drange/2): 
                domd = [0,0,-2*d/drange +1,2*d/drange ,0]
            if (d >= drange/2) & (d <= drange): 
                domd = [0,0,0,-2*d/drange +2,2*d/drange -1]
      
            # FIXME - what is this about?
            #if (dome[0] <0) or (domd[-1] <0):
            #    self.logger.debug(f" dome={dome}, domd={domd}, erange={erange}, drange={drange}")

            #Apply all 25 rules using minimum criterion
            for i in range(0,5):     #range end condition is < end, not = end.
                for j in range(0,5):
                    m[i,j] = min(dome[i],domd[j])  # should be zero except in  four cases
            self.logger.debug(m)

            #defuzzify using an RMS calculation.  There are four values of heating,
            #hhhh,hhh, hh,h, and one value of cooling z = 0.  There are 10 rules
            #that have non-zero heating values, but all 25 must be evaluated in denominator.                                     
            num = hhhh*math.sqrt(m[0,0]**2) + hhh*math.sqrt(m[0,1]**2 +m[1,0]**2) +\
                hh*math.sqrt(m[0,2]**2 + m[2,0]**2 + m[1,1]**2) + \
                h*math.sqrt(m[0,3]**2 + m[3,0]**2 + m[1,2]**2 + m[2,1]**2)
      
            densq = 0
            for i in range(0,4):    #the sum of all squares, unweighted
                for j in range(0,4):
                    densq = densq + m[i,j]**2
            den = math.sqrt(densq)

            if den != 0:
                result = num/den   # should be between 0 and 1
            if den == 0:
                result = 0
            if den == 0:
                self.logger.debug("denominator = 0")
            self.logger.debug(" num = %.5f,den = %.5f, output = %.5f" %(num, den, result))

            self.kiln_on()
            time.sleep(proportion*interval*result)   # wait for a number of seconds
            self.kiln_off()
            remainder = interval - proportion*interval*result  #should be positive, but...
            if remainder > 0:
                time.sleep(interval - proportion*interval*result) 
            self.runtime = time.time() - self.start      #present time since start, seconds
            self.logger.debug("runtime = %.3f, minutes; pausetime = %.3f minutes" % (self.runtime/60, self.pausetime/60))

            #end of while loop


class KilnCommandProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('/tmp/kilncommandprocessor.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler) 
        self.logger.setLevel(logging.WARNING)
        self.sock_path = SOCK_PATH
        # delete stale socket, if it exists
        try:
            os.unlink(self.sock_path)
        except OSError:
            if os.path.exists(self.sock_path):
                raise
        # open a unix domain socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.sock_path)
        os.chmod(self.sock_path, 0o777)

        self.kiln_controller = None
        self.kiln_controller_thread = None
        self.RUN_SERVER = True

    def socket_loop(self):
        self.sock.listen(1)
        while self.RUN_SERVER:
            try:
                conn, client_addr = self.sock.accept()
                self.logger.debug("connection from " + str(client_addr))
                while self.RUN_SERVER:
                    data = conn.recv(1024)
                    if data:
                        self.process_command(data, conn)
                    else:
                        break
            finally:
                conn.close()
                self.logger.debug('connection closed')

    def process_command(self, data, conn):
        command_data = json.loads(data)
        if command_data['command'].upper() == 'PING':
            conn.sendall(_to_bytes("PONG\n"))
        elif command_data['command'].upper() == 'START':
            # Start a job
            self.kiln_controller = KilnController(command_data['steps'], command_data['units'], conn)
            self.kiln_controller.job_id = command_data['job_id']
            self.kiln_controller_thread = threading.Thread(target=self.kiln_controller.run)
            self.kiln_controller_thread.start()
        elif command_data['command'].upper() == 'STOP':
            if self.kiln_controller is not None:
                self.kiln_controller.stop()
                self.kiln_controller_thread.join(30) # 30 sec timeout
                self.kiln_controller.job_id = None
                self.kiln_controller = None
        elif command_data['command'].upper() == 'PAUSE':
            if self.kiln_controller is not None:
                self.kiln_controller.pause()
        elif command_data['command'].upper() == 'RESUME':
            if self.kiln_controller is not None:
                self.kiln_controller.resume()
        elif command_data['command'].upper() == 'STATUS':
            state = 'IDLE'
            job_id = str(-1)
            if self.kiln_controller is not None:
                job_id = self.kiln_controller.job_id
                if job_id is not None and job_id != '-1':
                    state = self.kiln_controller.run_state
                else:
                    self.kiln_controller.run_state = state
            response = json.dumps({'response': 'status', 'state': state, 'job_id': job_id })
            conn.sendall(_to_bytes(response + "\n"))

    def run(self):
        self.socket_thread = threading.Thread(target=self.socket_loop)
        self.socket_thread.start()
        self.socket_thread.join()

def main():
    if not os.geteuid() == 0:
        print('Error: Must run as root')
        sys.exit(1)
    kcp = KilnCommandProcessor()
    kcp.run()

def _to_bytes(s):
    return bytes(s, 'utf-8')

if __name__ == "__main__":
    main()

''' (c) 2023 Control Physics - all rights reserved '''
