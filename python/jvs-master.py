# jvs-master.py
"""
Attempt to set up the JVS-I/O bus over a commodity USB/RS-485 converter,
and expose the button functionality as a collection standard Linux input
devices via the uinput kernel module.
"""

# imports
import argparse
import jvs
import uinput

# parse arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-s", "--serial-device",  default="/dev/ttyUSB0", metavar="DEVICE", help="Use device DEVICE as a JVS connection")
parser.add_argument("--assume-devices", type=int, default=None, metavar="N", help="If given, skip regular address setting procedure and assume N devices connected.")
parser.add_argument("-v", dest="verbose", action="count", help="Enter verbose mode, which shows more information on the bus traffic. Use more than once for more output.")
parser.add_argument("-d", "--dump", action="store_true", default=False, help="Store raw sent/received data in a dump file named openjvs_dump_<date>_<time>.log.")
args = parser.parse_args()

if args.verbose > 0:
	print("Starting up...")

if args.verbose > 1:
	print("Initializing JVS state")
jvs_state = jvs.JVS(args.serial_device, dump=args.dump)
if args.verbose > 1:
	print("Opened device %s" % jvs_state.ser.name)

if args.verbose > 1:
	print("Resetting bus, assigning address, identifying device")
jvs_state.reset(args.assume_devices)

# print a bunch of data
id_meanings = [ 'Manufacturer', 'Product name', 'Serial number', 'Product version', 'Comment' ]
if args.verbose > 0:
	print("Devices:")

# all possible events
events = (
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

for device in jvs_state.devices:
	# dump data about device
	if args.verbose > 1:
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

	# create a system uinput device, and a uinput device for each player, within each capable bus device
	if 'switches' in device.capabilities:
		print dir(device)
		device.uinput_devices = [ uinput.Device(events[2:5], name='openjvs_a%dsys' % device.address) ]	# add system device, for TEST and TILT switches
		for player in range(0, device.capabilities['switches']['players']):
			device.uinput_devices.append(uinput.Device(events[0:2+device.capabilities['switches']['switches']-4], name='openjvs_a%dp%d' % (device.address, player)))	# add player device
			if args.verbose > 1:
				print "\t\t- Creating device openjvs_a%dp%d for player %d" % (device.address, player, player)
		if args.verbose > 1:
			print

# read out switches
status_str = ''
old_length = 0
old_sw = None

try:
	while True:
		for device in jvs_state.devices:
			if 'switches' in device.capabilities:
				try:
					sw = jvs_state.read_switches(device.address, device.capabilities['switches']['players'])

					# read out system switches
					for (swnum, swid) in enumerate([ 'test', 'tilt1', 'tilt2', 'tilt3' ]):
						# check to emit initial event or event on switch status change
						if (old_sw == None) or (old_sw[0][swid] != sw[0][swid]):
							btnid = uinput.__dict__['BTN_%d' % swnum]

							if sw[player][swid]:
								device.uinput_devices[0].emit(btnid, 1, syn=False)
							else:
								device.uinput_devices[0].emit(btnid, 0, syn=False)

					# read out player switches
					for player in range(1, device.capabilities['switches']['players']+1):
						device.uinput_devices[player].emit(uinput.ABS_X, 1 + sw[player]['left'] - sw[player]['right'], syn=False)
						device.uinput_devices[player].emit(uinput.ABS_Y, 1 + sw[player]['down'] - sw[player]['up'], syn=False)
						for swnum in range(1, device.capabilities['switches']['switches']-3):
							swid  = 'push%d' % swnum
							btnid = uinput.__dict__['BTN_%d' % swnum]

							# check to emit initial event or event on switch status change
							if (old_sw == None) or (old_sw[player][swid] != sw[player][swid]):
								if sw[player][swid]:
									device.uinput_devices[player].emit(btnid, 1, syn=False)
								else:
									device.uinput_devices[player].emit(btnid, 0, syn=False)
						device.uinput_devices[player].syn()	# fire all events
					old_sw = sw
				except jvs.TimeoutError:
					if args.verbose > 0:
						print 'Timeout occurred while reading switches.'
except:
	jvs_state.ser.close()
	print "Shutting down."
