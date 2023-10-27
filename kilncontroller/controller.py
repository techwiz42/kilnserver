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
GPIO_PIN = 31

class KilnController:
    '''This is the class that encapsulates the command structure for the kiln controller'''
    def __init__(self, segments, units, interval, erange, drange, conn):
        self.logger = logging.getLogger("Controller")
        handler = logging.FileHandler('/var/log/kilnweb/kilncontroller.log')
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
        #set the GPIO pin to LOW
        self.gpio_pin = GPIO_PIN   #this is the pin number, not the GPIO channel number
        GPIO.cleanup() # just in case
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)  #HIGH is on, LOW is off
        self.interval = interval
        self.erange = erange
        self.drange = drange
        self.kiln_off()

    def __del__(self):
        GPIO.cleanup()

    def run_state(self):
        return self.run_state

    def pause(self):
        self.logger.debug("Pausing job")
        self.run_state = PAUSE

    def resume(self):
        self.logger.debug("Resuming job")
        self.run_state = RUN

    def stop(self):
        self.logger.debug("Stopping Job")
        self.run_state = STOP

    def read_temp(self):
        thermocouple = mx.MAX31855(CS, CLK, DO, 'f', board=GPIO.BOARD)
        temp = thermocouple.get()
        self.logger.debug(f"temp: {temp}")
        return float(temp)

    # returns seconds
    def duration(self):
        '''Returns the duration of the job in seconds'''
        seconds = 0
        prev_target = self.to_F(self.read_temp())
        for segment in self.segments:
            #target is degrees, rate is degrees per hour so multiply 3600 to get seconds
            ramp = (abs(segment['target'] - prev_target) / segment['rate']) * 3600
            #dwell is minutes, multiply by 60 to get seconds
            seconds += (ramp + (segment['dwell'] * 60))
            prev_target = segment['target']
        self.logger.debug(f"JOB DURATION = {seconds}")
        return round(seconds)

    # NOTE that the internal units of the temp table are F.
    # Job Steps are stored in the database as either C or F and
    # Are converted to F here. the to_F() function does the conversion
    def build_temp_table(self, units):
        start_temp = self.to_F(self.read_temp())
        self.logger.debug(f"start_temp is {repr(start_temp)} degrees F")
        previous_target = start_temp
        self.temp_table = [start_temp]
        self.threshold_table = []
        for segment in self.segments:
            rate = int(self.to_F(segment['rate']))
            target = int(self.to_F(segment['target']))
            dwell = int(self.to_F(segment['dwell']))
            threshold = int(self.to_F(segment['threshold']))
            self.logger.debug(f"segment: rate: {rate} target: {target} dwell: {dwell})")
            rate_mins = self.to_F(segment['rate']) / 60.0
            ramp = int(round(abs((self.to_F(segment['target']) - previous_target) / rate_mins)))
            j = 1
            t = 0
            for _ in range(t, t + int(ramp)):
                self.temp_table.append(int(round(self.to_F(segment['target']) - previous_target) *
                        j / ramp + previous_target))
                j += 1
                self.threshold_table.append(threshold)
            for _ in range(t + int(ramp), t + int(ramp + segment['dwell'])):
                self.temp_table.append(int(round(self.to_F(segment['target']))))
                j += 1
                self.threshold_table.append(threshold)
            t = round(t + ramp + segment['dwell'])
            previous_target = self.to_F(segment['target'])

    def set_point(self):
        seconds = max(self.runtime - self.pausetime, 0)
        minute = int(math.floor(seconds / 60))
        try:
            if self.run_state != PAUSE:
                dT = self.temp_table[minute+1] - self.temp_table[minute]
                dt = seconds / 60 - minute
                retval = (self.temp_table[minute] + dT * dt, self.threshold_table[minute])
            else:
                retval = (self.temp_table[minute], self.temp_table[minute])
        except IndexError:
            #We've reached the target temp
            retval = (self.temp_table[-1], self.threshold_table[-1])
        return retval

    def kiln_on(self):
        try:
            GPIO.output(self.gpio_pin, GPIO.HIGH)
        except:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BOARD)
            GPIO.setwarnings(False)
            GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)
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

        #interval = 5  #interval between updates, seconds
        #erange = 5  # default error range +/- 5
        #drange = 5 #default delta range
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
        duration = self.duration()
        try:
            while (self.runtime - self.pausetime) < duration:
            # Check run_state:
                if self.run_state in [RUN, PAUSE]:

                    #self.pausetime += interval
                    #self.logger.debug(f"pause calculation: {self.runtime - self.pausetime} < {duration}")
                    #time.sleep(interval)
                    pass
                if self.run_state == STOP:
                    break
                # find error and delta-error
                self.logger.debug(f"Run state is {self.run_state}")
                tmeas = self.to_F(self.read_temp())   # degrees F
                setpoint, threshold = self.set_point()  # degrees F
                if self.run_state == PAUSE:
                    self.kiln_off()
                    self.logger.debug("Pausing job")
                elif tmeas > threshold:
                    self.kiln_off()
                    self.logger.debug("Threshold temperature exceeded. Kiln is OFF and run is TERMINATED")
                    break
                e = tmeas - setpoint # present error degrees F
                d = e - lasterr # positive for increasing error, neg for decreasing error - degrees F
                self.logger.debug("e = %.3f, d = %.3f"  % (e, d))
                self.logger.debug("measured temperature = %.3f,  setpoint =  %.3f"  % (tmeas, setpoint))
                pct_complete = (self.runtime - self.pausetime)/duration * 100
                pct_compliant = tmeas/setpoint * 100
                self.logger.debug("measured temp %.2f setpoint %.2f compliant %.2f pct complete %.2f" % (tmeas, setpoint, pct_compliant, pct_complete))
                lasterr = e

                tempdata.append(tmeas)   #record data for plotting later
                setdata.append(setpoint)
                timedata.append(self.runtime)

                # find degree of membership in the 5 membership functions for e and d
                # make sure universe of discourse is large enough by increasing its size if e
                # or d lie outside the default range.

                if e > self.erange:
                    self.erange = e  #adjust universe of discourse if error is outside present range
                if e < -self.erange:
                    self.erange = -e  
                if d > self.drange:
                    self.drange = d  #same for d
                if d < -self.drange:
                    self.drange = -d

                #print"erange = ", erange, "   drange = ", drange

                #generate 5 entry degree of membership lists for each of 4 regions, for e and d
                if (e >= -self.erange) & (e < -self.erange/2):
                    dome = [-2*e/self.erange -1,2*e/self.erange +2,0,0,0]
                if (e >= -self.erange/2) & (e < 0):
                    dome = [0,-2*e/self.erange,2*e/self.erange +1,0,0]
                if (e >= 0) & (e < self.erange/2):
                    dome = [0,0,-2*e/self.erange +1,2*e/self.erange ,0]
                if (e >= self.erange/2) & (e <= self.erange):
                    dome = [0,0,0,-2*e/self.erange +2,2*e/self.erange -1]

                if (d >= -self.drange) & (d < -self.drange/2):
                    domd = [-2*d/self.drange -1,2*d/self.drange +2,0,0,0]
                if (d >= -self.drange/2) & (d < 0):
                    domd = [0,-2*d/self.drange,2*d/self.drange +1,0,0]
                if (d >= 0) & (d < self.drange/2): 
                    domd = [0,0,-2*d/self.drange +1,2*d/self.drange ,0]
                if (d >= self.drange/2) & (d <= self.drange): 
                    domd = [0,0,0,-2*d/self.drange +2,2*d/self.drange -1]
      
                # FIXME - what is this about?
                #if (dome[0] <0) or (domd[-1] <0):
                #    self.logger.debug(f" dome={dome}, domd={domd}, erange={erange}, drange={drange}")

                #Apply all 25 rules using minimum criterion
                for i in range(0,5):     #range end condition is < end, not = end.
                    for j in range(0,5):
                        m[i,j] = min(dome[i],domd[j])  # should be zero except in  four cases
                #self.logger.debug(m)

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
                #self.logger.debug(" num = %.5f,den = %.5f, output = %.5f" %(num, den, result))
                if self.run_state != PAUSE:
                    self.kiln_on()
                    time.sleep(proportion*self.interval*result)   # wait for a number of seconds
                    self.kiln_off()
                    remainder = self.interval - proportion*self.interval*result  #should be positive, but...
                    if remainder > 0:
                        time.sleep(remainder) 
                        self.runtime = time.time() - self.start      #present time since start, seconds
                        self.logger.debug("runtime = %.3f minutes pausetime = %.3f minutes" % (self.runtime/60, self.pausetime/60))
                else:
                    time.sleep(self.interval)
                    self.pausetime += self.interval
            self.kiln_off()
            self.job_id = None
            self.logger.debug("Exiting RUN loop")
            #end of while loop
        finally:
            #self.stop()
            #self.job_id = None
            pass


class KilnCommandProcessor:
    def __init__(self):
        self.logger = logging.getLogger("Command Processor")
        handler = logging.FileHandler('/var/log/kilnweb/kilncommandprocessor.log')
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
            job_id = command_data['job_id']
            self.kiln_controller = KilnController(command_data['steps'],
                                                  command_data['units'],
                                                  command_data['interval'],
                                                  command_data['erange'],
                                                  command_data['drange'],
                                                  conn)
            self.kiln_controller.job_id = job_id
            self.kiln_controller_thread = threading.Thread(target=self.kiln_controller.run)
            self.kiln_controller_thread.start()
        elif command_data['command'].upper() == 'STOP':
            if self.kiln_controller is not None:
                self.kiln_controller.stop()
                self.kiln_controller_thread.join(30) # 30 sec timeout
                self.kiln_controller.job_id = None
                self.kiln_controller.logger.handlers = []
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
            tmeas = "N/A"
            setpoint = "N/A"
            if self.kiln_controller is not None:
                job_id = self.kiln_controller.job_id
                if job_id is not None and job_id != '-1':
                    state = self.kiln_controller.run_state
                    tmeas = self.kiln_controller.read_temp()
                    setpoint = self.kiln_controller.set_point()[0]
                else:
                    self.kiln_controller.run_state = state
            response = json.dumps({'response': 'status', 
                                   'state': state, 'job_id': job_id,
                                   'tmeas': tmeas, 'setpoint': setpoint})
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
