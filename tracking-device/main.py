import os
import time
import gc
import pycom
from machine import RTC
from machine import SD
from machine import Timer
from L76GNSS import L76GNSS
from pycoproc_1 import Pycoproc
from LIS2HH12 import LIS2HH12


pycom.heartbeat(False)
pycom.rgbled(0x777777) # Light Blue

gc.enable()

pycom.rgbled(0x7F7F00) # Yellow
# Device setup
py = Pycoproc(Pycoproc.PYTRACK) # Pytrack
l76 = L76GNSS(pytrack=py, timeout=30) # GPS

# Setup timer
chrono = Timer.Chrono()
fixTime = 20.00*60.00 # 20 minutes

# Get coordinates
coord = l76.coordinates()
if coord[0] == None or coord[1] == None:
    pycom.rgbled(0xFF7F00) # Yellow
    print("Waiting for GPS... Position: {}".format(coord))
    
    chrono.start()
    while  coord[0] == None or coord[1] == None or chrono.read() > fixTime:
        coord = l76.coordinates()
        time.sleep(5)
    chrono.stop()
    chrono.reset()

if coord[0] == None or coord[1] == None:
    pycom.rgbled(0xFF0000) # Red
    print("No GPS within time limit")
    time.sleep(10)
else:
    pycom.rgbled(0x00FF00) # Green
    print("GPS position established: {}".format(coord))
    time.sleep(1)

# Load SD card
sd = SD()
os.mount(sd, '/sd')
os.listdir('/sd')

# Write coordinates to SD card
if  not coord[0] == None and not coord[1] == None:
    f = open('/sd/coordinates.txt', 'a') # Append
    f.write("{}".format(coord[1])) # Longitude
    f.write(' ')
    f.write("{}".format(coord[0])) # Latitude
    f.close()
    print("Coordinates written to SD card")
else:
    print("Error no data added to SD card. \nReason: Coordinates {}".format(coord))

# Read SD card
print('Reading from file:')
f = open('/sd/coordinates.txt', 'r')
print(f.readlines())
f.close()
print("Read from file.")
time.sleep(1)

# Enable pybytes
pybytes_enabled = False
if 'pybytes' in globals():
    if(pybytes.isconnected()):
        print('Pybytes is connected')
        pybytes_enabled = True

# Send to pybytes
if(pybytes_enabled and not coord[0] == None and not coord[1] == None):
    print("Sending to pybytes: {}".format(coord))
    pybytes.send_signal(1, coord)
else:
    print("Skipped sending {} to pybytes".format(coord))
time.sleep(1)

# display the reset reason code and the sleep remaining in seconds
# possible values of wakeup reason are:
# WAKE_REASON_ACCELEROMETER = 1
# WAKE_REASON_PUSH_BUTTON = 2
# WAKE_REASON_TIMER = 4
# WAKE_REASON_INT_PIN = 8

# Get accelerometer values
acc = LIS2HH12(py) # Accelerometer
print("Acceleration: " + str(acc.acceleration()))
print("Roll: " + str(acc.roll()))
print("Pitch: " + str(acc.pitch()))

print("Wakeup reason: " + str(py.get_wake_reason()))
# print("Approximate sleep remaining: " + str(py.get_sleep_remaining()) + " sec") # Might crash the repl
time.sleep(1)

# enable activity and also inactivity interrupts, using the default callback handler
py.setup_int_wake_up(True, True)
print("setup wake up")

# set the acceleration threshold to 2000mG (2G) and the min duration to 200ms
acc.enable_activity_interrupt(2000, 200)
print("enabled activity interrupt")

print("Sleeping... Shake to wake up")
pycom.rgbled(0xFF0ADD) # Purple
time.sleep(1)

# go to sleep for 5 minutes maximum if no accelerometer interrupt happens
py.setup_sleep(300) # If run from repl this will crash the repl
py.go_to_sleep(gps=True)
