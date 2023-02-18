from dronekit import connect
import sys

try:
    from PySide6.QtWidgets import *
    from PySide6.QtGui import *
    from PySide6.QtCore import *
except:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *

from QPrimaryFlightDisplay import QPrimaryFlightDisplay

# Create a Qt application
app = QApplication(sys.argv)

# Create PFD widget as standalone a window
# Actually, it is designed to be a widget in a QMainWindow
pfd = QPrimaryFlightDisplay()

# Set UI scale of the display
# This is necessary to make the display look good on different screen sizes
# For different DPI settings it is necessary to change the scale
pfd.zoom = 1

# Connect to the Vehicle
vehicle = connect("udp:127.0.0.1:14551", wait_ready=True)

# Create a callback to run regularly while the vehicle is connected
# It is used to update the display of the vehicle state
# Redrawing the display is fast enough to be done in real time


def update():
    # Update the display of the vehicle state
    pfd.roll = vehicle.attitude.roll
    pfd.pitch = vehicle.attitude.pitch
    pfd.heading = vehicle.heading
    pfd.airspeed = vehicle.airspeed
    pfd.alt = vehicle.location.global_relative_frame.alt
    pfd.vspeed = -vehicle.velocity[-1]
    pfd.skipskid = 0
    pfd.arm = vehicle.armed
    if pfd.battery != None:
        pfd.battery = vehicle.battery.level
    else:
        pfd.battery = 0
    # Redraw the display
    pfd.update()


# Create a timer to update the display of the vehicle state
timer = QTimer()
# Connect the timer to the callback function
timer.timeout.connect(update)
# Start the timer
timer.start(1000 / 60)

# Start the application
pfd.show()
try:
    sys.exit(app.exec())
except AttributeError:
    sys.exit(app.exec_())
