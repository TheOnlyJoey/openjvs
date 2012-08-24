# jvs-master.py
"""
Attempt to set up the JVS-I/O bus over a commodity USB/RS-485 converter,
and expose the button functionality as a standard Linux joystick device.

Meant to be run as a command-line program.
"""

# imports
import argparse
import jvs
import jvs_constants
import uinput

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
if args.verbose > 1:
	print("Opened device %s" % jvs_state.ser.name)

if args.verbose > 1:
	print("Resetting bus, assigning address, identifying device")
jvs_state.reset()

# print a bunch of data
id_meanings = [ 'Manufacturer', 'Product name', 'Serial number', 'Product version', 'Comment' ]
if args.verbose > 0:
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
		for (version_key, version_number) in device.versions.items():
			print("\t\t\t- %s: %1.1f" % (version_key, version_number))
		print

		# capability data
		print("\t\t- Capabilities:")
		for (cap_key, cap_args) in device.capabilities.items():
			print("\t\t\t- %s: %s" % (cap_key, repr(cap_args)))
		print

# create the uinput device
events = (
	        uinput.BTN_JOYSTICK,
    	    uinput.ABS_X + (0, 2, 0, 0),
        	uinput.ABS_Y + (0, 2, 0, 0),
			uinput.BTN_1,
			uinput.BTN_2,
			uinput.BTN_3,
			uinput.BTN_4,

			uinput.BTN_5,
			uinput.BTN_6,
			uinput.BTN_7,
			uinput.BTN_8
        )

uinput_device = uinput.Device(events, name='openjvs')

# read out switches
status_str = ''
old_length = 0
old_sw = None
# TODO: read out all info
try:
	while True:
		for device in jvs_state.devices:
			if 'switches' in device.capabilities:
				sw = jvs_state.read_switches(device.address, device.capabilities['switches']['players'])
				if old_sw != None:
					uinput_device.emit(uinput.ABS_X, 1 + sw[1]['right'] - sw[1]['left'], syn=False)
					uinput_device.emit(uinput.ABS_Y, 1 + sw[1]['down'] - sw[1]['up'], syn=False)
					for swnum in range(1, 9):
						if old_sw[1]['push%d' % swnum] != sw[1]['push%d' % swnum]:
							if sw[1]['push%d' % swnum]:
								uinput_device.emit(uinput.__dict__['BTN_%d' % swnum], 1, syn=False)
							else:
								uinput_device.emit(uinput.__dict__['BTN_%d' % swnum], 0, syn=False)
					uinput_device.syn()	# fire all events
				old_sw = sw
except:
	jvs_state.ser.close()
	print "Shutting down."
