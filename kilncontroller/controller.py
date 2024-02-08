''' 
    The main KilnController module 
    (c) 2023 Control Physics - all rights reserved
'''
import os
import socket
import time
import math
import threading
import json
import logging
from numpy import empty
import constants
import max31855 as mx

HEAT4 = 1.0
HEAT3 = 0.75
HEAT2 = 0.5
HEAT1 = 0.25

try:
    from  RPi import GPIO
    print("Raspberry Pi GPIO found")
except ImportError:
    # Assume we're not running on Pi hardware, import stub instead
    # This is for development and testing only.
    import stubGPIO as GPIO
    print("Raspberry Pi GPIO NOT FOUND - running stub")

class KilnController:
    """
        This is the class that encapsulates the
        command structure for the kiln controller
    """
    def __init__(self, segments, units, interval, erange, drange, conn):
        self.segments = segments
        self.units = units
        self.interval = interval
        self.erange = erange
        self.drange = drange
        self.logger = logging.getLogger("Controller")
        handler = logging.FileHandler('/var/log/kilnweb/kilncontroller.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self.conn = conn
        self.run_state = None
        self.start = None
        self.runtime = 0
        self.pausetime = 0
        self.job_id = None  # this is the ID of the running job, if any.
        self.build_temp_table()
        #set the GPIO pin to LOW
        self.gpio_pin = constants.GPIO_PIN # pin number, not channel number
        GPIO.cleanup() # just in case
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW) #HIGH=on, LOW=off
        self.m_deg = None
        self.kiln_off()

    def __del__(self):
        GPIO.cleanup()

    def get_state(self):
        """ Returns the state of the kiln """
        return self.run_state

    def pause(self):
        """ Pauses job """
        self.logger.debug("Pausing job")
        self.run_state = constants.PAUSE

    def resume(self):
        """ Resumes job """
        self.logger.debug("Resuming job")
        self.run_state = constants.RUN

    def stop(self):
        """ Stops Job """
        self.logger.debug("Stopping Job")
        self.run_state = constants.STOP

    def read_temp(self):
        """ Reads the temperature from the MAX31855 thermocouple """
        thermocouple = mx.MAX31855(
                constants.CS,
                constants.CLK,
                constants.DO,
                'f',
                board=GPIO.BOARD
            )
        temp = thermocouple.get()
        self.logger.debug("temp: %2f", temp)
        return float(temp)

    # returns seconds
    def duration(self):
        '''Returns the duration of the job in seconds'''
        seconds = 0
        prev_target = self.to_f(self.read_temp())
        for segment in self.segments:
            #target is degrees, rate is degrees per hour so multiply 3600 to get seconds
            ramp = (abs(segment['target'] - prev_target) / segment['rate']) * 3600
            #dwell is minutes, multiply by 60 to get seconds
            seconds += (ramp + (segment['dwell'] * 60))
            prev_target = segment['target']
        self.logger.debug("JOB DURATION = %s", seconds)
        return round(seconds)

    # NOTE that the internal units of the temp table are F.
    # Job Steps are stored in the database as either C or F and
    # Are converted to F here. the to_f() function does the conversion
    def build_temp_table(self):
        """ Builds the table of setpoint tempertures """
        start_temp = self.to_f(self.read_temp())
        self.logger.debug("start_temp is %s degrees F", repr(start_temp))
        previous_target = start_temp
        self.temp_table = [start_temp]
        self.threshold_table = []
        for segment in self.segments:
            rate = int(self.to_f(segment['rate']))
            target = int(self.to_f(segment['target']))
            dwell = int(self.to_f(segment['dwell']))
            threshold = int(self.to_f(segment['threshold']))
            log_msg = f"segment: rate: {rate} target: {target} dwell: {dwell})"
            self.logger.debug(log_msg)
            rate_mins = self.to_f(segment['rate']) / 60.0
            ramp = int(round(abs((
                self.to_f(segment['target']) - previous_target) / rate_mins))
            )
            j_val = 1
            t_val = 0
            for _ in range(t_val, t_val + int(ramp)):
                self.temp_table.append(
                    int(round(self.to_f(segment['target']) - previous_target) *\
                        j_val / ramp + previous_target)
                    )
                j_val += 1
                self.threshold_table.append(threshold)
            for _ in range(t_val + int(ramp), t_val + int(ramp + segment['dwell'])):
                self.temp_table.append(int(round(self.to_f(segment['target']))))
                j_val += 1
                self.threshold_table.append(threshold)
            t_val = round(t_val + ramp + segment['dwell'])
            previous_target = self.to_f(segment['target'])

    def set_point(self):
        """ Calculates the setpoint given the target temp and the runtime """
        seconds = max(self.runtime - self.pausetime, 0)
        minute = int(math.floor(seconds / 60))
        try:
            if self.run_state != constants.PAUSE:
                interval = self.temp_table[minute+1] - self.temp_table[minute]
                rate = seconds / 60 - minute
                retval = (
                        self.temp_table[minute] + interval * rate,
                        self.threshold_table[minute]
                    )
            else:
                retval = (self.temp_table[minute], self.temp_table[minute])
        except IndexError:
            #We've reached the target temp
            retval = (self.temp_table[-1], self.threshold_table[-1])
        return retval

    def kiln_on(self):
        """ Turns kiln on """
        try:
            GPIO.output(self.gpio_pin, GPIO.HIGH)
        except RuntimeError:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BOARD)
            GPIO.setwarnings(False)
            GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)
            GPIO.output(self.gpio_pin, GPIO.HIGH)

    def kiln_off(self):
        """ Turns kiln off """
        GPIO.output(self.gpio_pin, GPIO.LOW)

    # Convert celsius temperatures to Farenheit. If units are already F, don't convert.
    def to_f(self, temperature):
        """
           Convert celsius temperatures to Farenheit.
           If units are already F, don't convert 
        """
        if self.units == 'F':
            return temperature
        return temperature * 9 / 5 + 32

    def run(self):
        """ Start the run """
        self.run_state = constants.RUN
        self.start = time.time()
        self.logger.debug("denominator = 0")
        # initialize degree of membership matrix
        self.m_deg = empty((5,5),dtype=float)*0

        # Data collection for graphing
        duration = self.duration()
        lasterr = 0
        try:
            while (self.runtime - self.pausetime) < duration:
            # Check run_state:
                if self.run_state in [constants.RUN, constants.PAUSE]:
                    pass
                if self.run_state == constants.STOP:
                    break
                # find error and delta-error
                self.logger.debug("Run state is %s", self.run_state)
                tmeas = self.to_f(self.read_temp())   # degrees F
                setpoint, threshold = self.set_point()  # degrees F
                setpoint = round(setpoint, 2)
                if self.run_state == constants.PAUSE:
                    self.kiln_off()
                    self.logger.debug("Pausing job")
                elif tmeas > threshold:
                    self.kiln_off()
                    log_msg = "Threshold temperature exceeded. Kiln is OFF and run is TERMINATED"
                    self.logger.debug(log_msg)
                    break
                error = tmeas - setpoint # present error degrees F
                delta = error - lasterr
                log_msg = f"e = {error}, d = {delta}"
                self.logger.debug(log_msg)
                log_msg = f"meas temp = {tmeas}, set pt = {setpoint}"
                self.logger.debug(log_msg)
                lasterr = error

                # find degree of membership in the 5 membership functions
                # for e and d
                # make sure universe of discourse is large enough by increasing
                # its size if e or d lie outside the default range.

                self.adjust_universe(error, delta)
                self.generate_degree_of_membership(error, delta)
                result = self.defuzify()
                self.toggle_kiln(result)

            self.kiln_off()
            self.job_id = None
            self.logger.debug("Exiting RUN loop")
            #end of while loop
        finally:
            pass

    def adjust_universe(self, error, delta):
        """
            adust universe of discourse if error is outside of range
            also adjust universe of discourse if delta is outside of range
        """
        if error > self.erange:
            self.erange = error  # adjust universe of discourse if error > range
        elif error < -self.erange:
            self.erange = -error
        if delta > self.drange:
            self.drange = delta  #same for d
        elif delta < -self.drange:
            self.drange = -delta

    def generate_degree_of_membership(self, error, delta):
        """
            generate 5 entry degree of membership lists for each of 4 regions, 
            for error and delta
        """
        dome = None
        domd = None
        if (error >= -self.erange) & (error < -self.erange/2):
            dome = [-2*error/self.erange -1,2*error/self.erange +2,0,0,0]
        elif (error >= -self.erange/2) & (error < 0):
            dome = [0,-2*error/self.erange,2*error/self.erange +1,0,0]
        elif (error >= 0) & (error < self.erange/2):
            dome = [0,0,-2*error/self.erange +1,2*error/self.erange ,0]
        elif (error >= self.erange/2) & (error <= self.erange):
            dome = [0,0,0,-2*error/self.erange +2,2*error/self.erange -1]
        if (delta >= -self.drange) & (delta < -self.drange/2):
            domd = [-2*delta/self.drange -1,2*delta/self.drange +2,0,0,0]
        elif (delta >= -self.drange/2) & (delta < 0):
            domd = [0,-2*delta/self.drange,2*delta/self.drange +1,0,0]
        elif (delta >= 0) & (delta < self.drange/2):
            domd = [0,0,-2*delta/self.drange +1,2*delta/self.drange ,0]
        elif (delta >= self.drange/2) & (delta <= self.drange):
            domd = [0,0,0,-2*delta/self.drange +2,2*delta/self.drange -1]
        #Apply all 25 rules using minimum criterion
        for i in range(5):     #range end condition is < end, not = end.
            for j in range(5):
                self.m_deg[i,j] = min(dome[i],domd[j])

    def defuzify(self):
        """ 
            defuzzify using an RMS calculation.
            There are four values of heating,
            hhhh_heat,hhh_heat, hh_heat,h_heat
            and one cooling z = 0.
            There are 10 rules that have non-zero heating values,
            but all 25 must be evaluated in denominator.
        """
        num = HEAT4*math.sqrt(self.m_deg[0,0]**2) +\
            HEAT3*math.sqrt(self.m_deg[0,1]**2 +self.m_deg[1,0]**2) +\
            HEAT2*math.sqrt(self.m_deg[0,2]**2 + self.m_deg[2,0]**2 + self.m_deg[1,1]**2) + \
            HEAT1*math.sqrt(self.m_deg[0,3]**2 + self.m_deg[3,0]**2 + self.m_deg[1,2]**2 + \
                self.m_deg[2,1]**2)

        densq = 0
        for i in range(5):    #the sum of all squares, unweighted
            for j in range(5):
                densq = densq + self.m_deg[i,j]**2
        den = math.sqrt(densq)

        if den != 0:
            result = num/den   # should be between 0 and 1
        else:
            result = 0
            self.logger.debug("denominator = 0")
        return result

    def toggle_kiln(self, result):
        """
            Turn kiln on for the calculated length of time
        """
        if self.run_state != constants.PAUSE:
            self.kiln_on()
            time.sleep(self.interval*result)   # wait for a number of seconds
            self.kiln_off()
            remainder = self.interval - self.interval*result
            if remainder > 0:
                time.sleep(remainder)
                self.runtime = time.time() - self.start
            else:
                time.sleep(self.interval)
                self.pausetime += self.interval

class KilnCommandProcessor:
    """
        The KilnCommandProcessor class listens to the unix socket
        at /tmp/kiln_controller. After it has been instantiated,
        main calls its run() method, which listens in the socket_loop()
        method and dispatches commands to the process_commands method.
    """

    def __init__(self):
        """
            sets up logging, creates the unix socket and sets the
            run_server instance variable to True
        """
        self.logger = logging.getLogger("Command Processor")
        handler = logging.FileHandler(
                '/var/log/kilnweb/kilncommandprocessor.log'
            )
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.WARNING)
        self.sock_path = constants.SOCK_PATH
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
        self.socket_thread = None
        self.run_server = True

    def socket_loop(self):
        """
            Listens on the unix socket for incoming commands. Loops while run_server is True
            Gets data (command) from the unix socket and dispatches it to the process_command method
        """
        self.sock.listen(1)
        while self.run_server:
            try:
                conn, client_addr = self.sock.accept()
                self.logger.debug("connection from %s", str(client_addr))
                while self.run_server:
                    data = conn.recv(1024)
                    if data:
                        self.process_command(data, conn)
                    else:
                        break
            finally:
                conn.close()
                self.logger.debug('connection closed')

    def process_command(self, data, conn):
        """
            Command:
            START:  instantiates a new KilnController object
                    and starts it in its own thread
            STOP:   sends a stop message to the KilnController object
            PAUSE:  sends a message to the KilnController to pause the job
            RESUME: sends a message to the KilnController to resume paused job
            STATUS: reads the temperature of the kiln and the state of the
                    KilnController job and returns the information
        """
        command_data = json.loads(data)
        if command_data['command'].upper() == 'PING':
            conn.sendall(_to_bytes("PONG\n"))
        elif command_data['command'].upper() == constants.START:
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
        elif command_data['command'].upper() == constants.STOP:
            if self.kiln_controller is not None:
                self.kiln_controller.stop()
                self.kiln_controller_thread.join(30) # 30 sec timeout
                self.kiln_controller.job_id = None
                self.kiln_controller.logger.handlers = []
                self.kiln_controller = None
        elif command_data['command'].upper() == constants.PAUSE:
            if self.kiln_controller is not None:
                self.kiln_controller.pause()
        elif command_data['command'].upper() == constants.RESUME:
            if self.kiln_controller is not None:
                self.kiln_controller.resume()
        elif command_data['command'].upper() == constants.STATUS:
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
        """
            Starts the thread running the socket_loop() method
        """
        self.socket_thread = threading.Thread(target=self.socket_loop)
        self.socket_thread.start()
        self.socket_thread.join()

def main():
    """
        The main entry point.
    """
    assert os.geteuid() == 0, "ERROR: Must run as root"
    kcp = KilnCommandProcessor()
    try:
        kcp.run()
    except KeyboardInterrupt:
        print("bye")

def _to_bytes(strng):
    return bytes(strng, 'utf-8')

if __name__ == "__main__":
    main()
