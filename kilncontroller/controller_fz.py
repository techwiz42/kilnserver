import os
import sys
import socket
import time
import math
import threading
import json
import logging
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

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
        #self.logger.debug(f"temp: {temp}")
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
        self.runtime = 0
        self.pausetime = 0
        duration = self.duration()
        # Create Antecedent/Consequent objects representing the error, its rate of change, and second derivative of error
        #FIXME - play with antiecedent range values - could be params from UI
        universe = np.linspace(-5,0,5)
        alternate_universe = np.linspace(-5,0,5)
        error = ctrl.Antecedent(universe, 'error')
        delta = ctrl.Antecedent(alternate_universe, 'delta')
        output = ctrl.Consequent(np.arange(0, 55, 1), 'output')
        
        names = ['nb', 'ns', 'ze', 'ps', 'pb']

        # Define the linguistic variables with membership functions
        error.automf(names = names)
        delta.automf(names = names)
        output.automf(names = names)

        # Create rules for the fuzzy logic controller
        rule_PB = ctrl.Rule(antecedent=((error['nb'] & delta['nb']) |
                              (error['ns'] & delta['nb']) |
                              (error['nb'] & delta['ns'])),
                  consequent=output['pb'], label='rule pb')

        rule_PS = ctrl.Rule(antecedent=((error['nb'] & delta['ze']) |
                              (error['nb'] & delta['ps']) |
                              (error['ns'] & delta['ns']) |
                              (error['ns'] & delta['ze']) |
                              (error['ze'] & delta['ns']) |
                              (error['ze'] & delta['nb']) |
                              (error['ps'] & delta['nb'])),
                  consequent=output['ps'], label='rule ps')

        rule_ZE = ctrl.Rule(antecedent=((error['nb'] & delta['pb']) |
                              (error['ns'] & delta['ps']) |
                              (error['ze'] & delta['ze']) |
                              (error['ps'] & delta['ns']) |
                              (error['pb'] & delta['nb'])),
                  consequent=output['ze'], label='rule ze')

        rule_NS = ctrl.Rule(antecedent=((error['ns'] & delta['pb']) |
                              (error['ze'] & delta['pb']) |
                              (error['ze'] & delta['ps']) |
                              (error['ps'] & delta['ps']) |
                              (error['ps'] & delta['ze']) |
                              (error['pb'] & delta['ze']) |
                              (error['pb'] & delta['ns'])),
                  consequent=output['ns'], label='rule ns')

        rule_NB = ctrl.Rule(antecedent=((error['ps'] & delta['pb']) |
                              (error['pb'] & delta['pb']) |
                              (error['pb'] & delta['ps'])),
                  consequent=output['nb'], label='rule nb')
        # Create the control system
        kiln_ctrl = ctrl.ControlSystem([rule_PB, rule_PS, rule_ZE, rule_NS, rule_NB])
        controller = ctrl.ControlSystemSimulation(kiln_ctrl)



        e1 = 0 # last error before current 
        try:
            while (self.runtime - self.pausetime) < duration:
            # Check run_state:
                if self.run_state in [RUN, PAUSE]:
                    pass
                if self.run_state == STOP:
                    break
                # find error and delta-error
                self.logger.debug(f"Run state is {self.run_state}")
                tmeas = self.to_F(self.read_temp())   # degrees F
                setpoint, threshold = self.set_point()  # degrees F
                setpoint = round(setpoint, 2)
                if self.run_state == PAUSE:
                    self.kiln_off()
                    self.logger.debug("Pausing job")
                elif tmeas > threshold:
                    self.kiln_off()
                    self.logger.debug("Threshold temperature exceeded. Kiln is OFF and run is TERMINATED")
                    break
                e = tmeas - setpoint # present error degrees F
                e1 = e - e1 # first derivative of error - positive for increasing error, neg for decreasing error - degrees F

                controller.input['error'] = e
                controller.input['delta'] = e1
                controller.compute()
                proportion = controller.output['output']/100
                self.logger.debug("proportion %.2f" % proportion)
                self.logger.debug("temp = %.3f, setpoint = %.3f, e = %.3f, d = %.3f" % (tmeas, setpoint, e, e1))
                e1 = e

                # find degree of membership in the 5 membership functions for e and d
                # make sure universe of discourse is large enough by increasing its size if e
                # or d lie outside the default range.

                if self.run_state != PAUSE:
                    print(f"self.interval = {self.interval}, proportion = {proportion}, time_on = {self.interval*proportion}")
                    self.kiln_on()
                    time.sleep(proportion*self.interval)   # wait for a number of seconds
                    self.kiln_off()
                    remainder = self.interval - proportion*self.interval  #should be positive, but...
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
                    setpoint = round(self.kiln_controller.set_point()[0], 2)
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
