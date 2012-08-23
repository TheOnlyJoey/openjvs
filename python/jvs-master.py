# jvs-master.py
"""
Attempt to set up the JVS-I/O bus over a commodity USB/RS-485 converter,
and expose the button functionality as a standard Linux joystick device.

Meant to be run as a command-line program.
"""

# imports
import argparse
import jvs

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-s", "--serial-device",  default="/dev/ttyUSB0", help="Use device DEVICE as a JVS connection")
parser.add_argument("-v", "--verbose", action="count", help="Enter verbose mode, which shows more information on the bus traffic. Use more than once for more output.")
args = parser.parse_args()

if args.verbose > 0:
	print("Starting up...")

if args.verbose > 1:
	print("Initializing JVS state")
jvs_state = jvs.JVS(args.serial_device)
print("Opened device %s" % jvs_state.ser.name)

if args.verbose > 1:
	print("Resetting bus, assigning address, identifying device")
jvs_state.reset()

# print a bunch of data
id_meanings = [ 'Manufacturer', 'Product name', 'Product version', 'Comment' ]
print("Devices:")
for device in jvs_state.devices:
	print("\t- Address %d:" % device.address)

	# id data
	print("\t\t- ID:")
	for (id_key, id_string) in enumerate(device.id_data):
		print("\t\t\t- %s: %s" % (id_meanings[id_key], id_string))
	print

	# version numbers
	print("\t\t- Versions:")
	for (version_key, version_number) in enumerate(device.versions):
		print("\t\t\t- %s: %1.1f" % (version_key, version_number))
	print
