from kilnserver import app
from kilnserver.redis_state import RedisState
import os, sys, time, math, string, numpy
from max31855 import *  #must be in same directory as this code
import RPi.GPIO as GPIO   #must run using lower left button: sudo idle3
from numpy import column_stack, savetxt

class KilnController:
  def __init__(self, segments):
    self.segments = segments
    self.build_temp_table()
    #set the GPIO pin to LOW, cuz my driver chip is inverting, so net active HIGH
    self.gpio_pin = 26   #this is the pin number, not the GPIO channel number -
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)  #HIGH is on, LOW is off

  def __del__(self):
    GPIO.cleanup()

  def read_temp(self):
    thermocouple = MAX31855(24,23,22, 'f', board=GPIO.BOARD)
    temp = thermocouple.get()
    return float(temp)

  def duration(self):
    minutes = 0
    start_temp = self.read_temp()
    prev_target = 0
    for segment in self.segments:
      ramp = abs(segment['target'] - prev_target) / (segment['rate'] / 60.0)
      minutes += ramp + segment['dwell']
      prev_target = segment['target']
    return round(minutes)

  def build_temp_table(self):
    start_temp = self.read_temp()
    app.logger.debug("start_temp is %s" % (repr(start_temp)))
    previous_target = start_temp
    self.temp_table = [start_temp]

    for segment in self.segments:
      app.logger.debug("segment: rate: %s target: %s dwell: %s" % (repr(segment['rate']),repr(segment['target']),repr(segment['dwell'])))
      rate_mins = segment['rate'] / 60.0
      ramp = int(round(abs((segment['target'] - previous_target) / rate_mins)))
      j = 1
      t = 0
      for m in range(t, t + int(ramp)):
        self.temp_table.append((segment['target'] - previous_target) * j / ramp + previous_target)
        j += 1
      for m in range(t + int(ramp), t + int(ramp + segment['dwell'])):
        self.temp_table.append(segment['target'])
        j += 1
      t = round(t + ramp + segment['dwell'])
      previous_target = segment['target']

  def set_point(self):
    seconds = time.time() - self.start
    minute = int(math.floor(seconds / 60))
    dT = (self.temp_table[minute+1] - self.temp_table[minute])
    dt = seconds / 60 - minute
    return self.temp_table[minute] + dT * dt

  def kiln_on(self):
    GPIO.output(self.gpio_pin, GPIO.HIGH)

  def kiln_off(self):
    GPIO.output(self.gpio_pin, GPIO.LOW)

  def run(self):
    m = numpy.empty((5,5),dtype=float)*0    # degree of membership matrix

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
    runtime = 0   # minutes
    pausetime = 0   # minutes
    tempdata = [self.read_temp()]
    setdata = [self.set_point()]
    timedata = [runtime]

    rs = RedisState(self.tag)
    while (runtime - pausetime) < self.duration():
      # Check run state
      
      # find error and delta-error
      tmeas = self.read_temp()   # degrees F
      setpoint = self.set_point()  # degrees F
      e = tmeas - setpoint # present error degrees F
      d = e - lasterr # positive for increasing error, neg for decreasing error - degrees F
      print "e = ",'%.3f' % e, "  d = " '%.3f' % d
      print "measured temperature = ", '%.3f' % tmeas, "  setpoint = ", '%.3f' % setpoint
      lasterr = e

      tempdata.append(tmeas)   #record data for plotting later
      setdata.append(setpoint)
      timedata.append(runtime)

      # find degree of membership in the 5 membership functions for e and d
      # make sure universe of discourse is large enough by increasing its size if e
      # or d lie outside the default range.

      if e > erange: erange = e  #adjust universe of discourse if error is outside present range
      if e < -erange: erange = -e  
      if d > drange: drange = d  #same for d
      if d < -drange:  drange = -d

      #    print"erange = ", erange, "   drange = ", drange

      #generate 5 entry degree of membership lists for each of 4 regions, for e and d

      if (e >= -erange) & (e < -erange/2): dome = [-2*e/erange -1,2*e/erange +2,0,0,0]
      if (e >= -erange/2) & (e < 0): dome = [0,-2*e/erange,2*e/erange +1,0,0]
      if (e >= 0) & (e < erange/2): dome = [0,0,-2*e/erange +1,2*e/erange ,0]
      if (e >= erange/2) & (e <= erange): dome = [0,0,0,-2*e/erange +2,2*e/erange -1]

      if (d >= -drange) & (d < -drange/2): domd = [-2*d/drange -1,2*d/drange +2,0,0,0]
      if (d >= -drange/2) & (d < 0): domd = [0,-2*d/drange,2*d/drange +1,0,0]
      if (d >= 0) & (d < drange/2): domd = [0,0,-2*d/drange +1,2*d/drange ,0]
      if (d >= drange/2) & (d <= drange): domd = [0,0,0,-2*d/drange +2,2*d/drange -1]
      
      if (dome <0) or (domd <0):
          print " dome= ", dome, "  domd= ", domd, " erange= ", erange, " drange = ", drange

      #Apply all 25 rules using minimum criterion
      for i in range(0,5):     #range end condition is < end, not = end.
        for j in range(0,5):
            m[i,j] = min(dome[i],domd[j])  # should be zero except in  four cases
      print m

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

      if den != 0: result = num/den   # should be between 0 and 1
      if den == 0: result = 0
      if den == 0: print("denominator = 0")
      print" num = ",'%.5f' % num,"den = ",'%.5f' % den,"output = ",'%.5f' % result

      self.kiln_on()
      time.sleep(proportion*interval*result)   # wait for a number of seconds
      self.kiln_off()
      remainder = interval - proportion*interval*result  #should be positive, but...
      if remainder > 0: time.sleep(interval - proportion*interval*result) 
      runtime = (time.time() - self.start)/60      #present time since start, minutes
      print "runtime = ", runtime, " minutes"
      print " " 

    #end of while loop


# DataOut = column_stack((timedata, tempdata, setdata))
# savetxt('output.dat', DataOut, fmt =( '%6.3f','%6.3f', '%6.3f'))
# 
# n = len(tempdata)
# squares = [0]*n
# for i in range(0,n): squares[i] = (tempdata[i]-setdata[i])**2
# temprms = math.sqrt(sum(squares)/n)
# print "rms temperature error = ", temprms, " degrees F"



   






        

    


        

    

