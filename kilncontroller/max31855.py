#!/usr/bin/python
''' Python driver for MAX38166 thermcouple '''
import time
import random

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Assume we're not running on Pi hardware, import stub instead
    import stubGPIO as GPIO

class MAX31855():
    '''Python driver for [MAX38155 Cold-Junction Compensated Thermocouple-to-Digital Converter]
    (http://www.maximintegrated.com/datasheet/index.mvp/id/7273)
     Requires:
     - The [GPIO Library](https://code.google.com/p/raspberry-gpio-python/) 
       (Already on most Raspberry Pi OS builds)
     - A [Raspberry Pi](http://www.raspberrypi.org/)

    '''
    def __init__(self, cs_pin, clock_pin, data_pin, units = "c", board = GPIO.BCM):
        '''Initialize Soft (Bitbang) SPI bus

        Parameters:
        - cs_pin:    Chip Select (CS) / Slave Select (SS) pin (Any GPIO)  
        - clock_pin: Clock (SCLK / SCK) pin (Any GPIO)
        - data_pin:  Data input (SO / MOSI) pin (Any GPIO)
        - units:     (optional) unit of measurement to return. 
                     ("c" (default) | "k" | "f")
        - board:     (optional) pin numbering method as per RPi.GPIO library 
                     (GPIO.BCM (default) | GPIO.BOARD)
        '''
        self.cs_pin = cs_pin
        self.clock_pin = clock_pin
        self.data_pin = data_pin
        self.units = units
        self.data = None
        self.board = board

        # Initialize needed GPIO
        GPIO.setmode(self.board)
        GPIO.setwarnings(False)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.setup(self.clock_pin, GPIO.OUT)
        GPIO.setup(self.data_pin, GPIO.IN)

        # Pull chip select high to make chip inactive
        GPIO.output(self.cs_pin, GPIO.HIGH)

    def get(self):
        '''Reads SPI bus and returns current value of thermocouple.
            in case of error, reads three times, waiting a random interval 
            between reads. If error occurs after third read, raises error'''
        read_error = None
        count = 0
        while True:
            self.read()
            read_error = self.checkErrors()
            count += 1
            if read_error is not None and count <= 3:
                continue
            elif read_error and count <= 3:
                time.sleep(random.randint(1000)/1000)
                continue
            elif read_error:
                raise read_error
            else:
                break

        return getattr(self, "to_" + self.units)(self.data_to_tc_temperature())

    def get_rj(self):
        '''Reads SPI bus and returns current value of reference junction.'''
        self.read()
        return getattr(self, "to_" + self.units)(self.data_to_rj_temperature())

    def read(self):
        '''Reads 32 bits of the SPI bus & stores as an integer in self.data.'''
        bytesin = 0
        # Select the chip
        GPIO.output(self.cs_pin, GPIO.LOW)
        # Read in 32 bits
        for _ in range(32):
            GPIO.output(self.clock_pin, GPIO.LOW)
            bytesin = bytesin << 1
            if GPIO.input(self.data_pin):
                bytesin = bytesin | 1
            GPIO.output(self.clock_pin, GPIO.HIGH)
        # Unselect the chip
        GPIO.output(self.cs_pin, GPIO.HIGH)
        # Save data
        self.data = bytesin

    def checkErrors(self, data_32 = None):
        '''Checks error bits to see if there are any SCV, SCG, or OC faults'''
        if data_32 is None:
            data_32 = self.data
        anyErrors = (data_32 & 0x10000) != 0    # Fault bit, D16
        noConnection = (data_32 & 1) != 0       # OC bit, D0
        shortToGround = (data_32 & 2) != 0      # SCG bit, D1
        shortToVCC = (data_32 & 4) != 0         # SCV bit, D2
        if anyErrors:
            if noConnection:
                return MAX31855Error("No Connection")
            if shortToGround:
                return MAX31855Error("Thermocouple short to ground")
            if shortToVCC:
                return MAX31855Error("Thermocouple short to VCC")
            # Perhaps another SPI device is trying to send data?
            # Did you remember to initialize all other SPI devices?
            return MAX31855Error("Unknown Error")
        else:
            return None

    def data_to_tc_temperature(self, data_32 = None):
        '''Takes an integer and returns a thermocouple temperature in celsius.'''
        if data_32 is None:
            data_32 = self.data
        tc_data = (data_32 >> 18) & 0x3FFF
        return self.convert_tc_data(tc_data)

    def data_to_rj_temperature(self, data_32 = None):
        '''Takes an integer and returns a reference junction temperature in celsius.'''
        if data_32 is None:
            data_32 = self.data
        rj_data = (data_32 >> 4) & 0xFFF
        return self.convert_rj_data(rj_data)

    def convert_tc_data(self, tc_data):
        '''Convert thermocouple data to a useful number (celsius).'''
        if tc_data & 0x2000:
            # two's compliment
            without_resolution = ~tc_data & 0x1FFF
            without_resolution += 1
            without_resolution *= -1
        else:
            without_resolution = tc_data & 0x1FFF
        return without_resolution * 0.25

    def convert_rj_data(self, rj_data):
        '''Convert reference junction data to a useful number (celsius).'''
        if rj_data & 0x800:
            without_resolution = ~rj_data & 0x7FF
            without_resolution += 1
            without_resolution *= -1
        else:
            without_resolution = rj_data & 0x7FF
        return without_resolution * 0.0625

    def to_c(self, celsius):
        '''Celsius passthrough for generic to_* method.'''
        return celsius

    def to_k(self, celsius):
        '''Convert celsius to kelvin.'''
        return celsius + 273.15

    def to_f(self, celsius):
        '''Convert celsius to fahrenheit.'''
        return celsius * 9.0/5.0 + 32

    def cleanup(self):
        '''Selective GPIO cleanup'''
        GPIO.setup(self.cs_pin, GPIO.IN)
        GPIO.setup(self.clock_pin, GPIO.IN)

class MAX31855Error(Exception):
    '''Returns thermocouple errors'''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

if __name__ == "__main__":

    # Multi-chip example
    import time
    CS_PINS = [4, 17, 18, 24]
    CLOCK_PIN = 23
    DATA_PIN = 22
    UNITS = "f"
    thermocouples = []
    for pin in CS_PINS:
        thermocouples.append(MAX31855(pin, CLOCK_PIN, DATA_PIN, UNITS))
    RUNNING = True
    while RUNNING:
        try:
            for thermocouple in thermocouples:
                rj = thermocouple.get_rj()
                try:
                    tc = thermocouple.get()
                except MAX31855Error as e:
                    tc = "Error: "+ e.value
                    RUNNING = False
                print(f"tc: {tc} and rj: {rj}")
            time.sleep(1)
        except KeyboardInterrupt:
            RUNNING = False
    for thermocouple in thermocouples:
        thermocouple.cleanup()

''' (c) 2023 Control Physics - all rights reserved '''
