# jvs-master.py
"""
Attempt to set up the JVS-I/O bus over a commodity USB/RS-485 converter,
and expose the button functionality as a collection standard Linux input
devices via the uinput kernel module.
"""

# imports
import argparse
import ConfigParser
import jvs
import uinput
import sys
import traceback

# parse arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-s", "--serial-device",  default="/dev/ttyUSB0", metavar="DEVICE", help="Use device DEVICE as a JVS connection")
parser.add_argument("-c", "--config", dest="config_filename", default="jvs_master.cfg", metavar="FILENAME", help="use file FILENAME as config file")
parser.add_argument("--assume-devices", type=int, default=None, metavar="N", help="If given, skip regular address setting procedure and assume N devices connected.")
parser.add_argument("-v", dest="verbose", action="count", help="Enter verbose mode, which shows more information on the bus traffic. Use more than once for more output.")
parser.add_argument("-d", "--dump", action="store_true", default=False, help="Store raw sent/received data in a dump file named openjvs_dump_<date>_<time>.log.")
args = parser.parse_args()

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
		uinput.BTN_8,
		uinput.BTN_START
	)

if args.verbose > 0:
	print("Starting up...")

if args.verbose > 2:
	print("Reading in config file %s" % args.config_filename)

# read in config
cfg = ConfigParser.ConfigParser()
cfg.read(args.config_filename)

joystick_map = {}
devicenum = 0
playernum = 0

for section in cfg.sections():
	if section.startswith('device'):
		devicenum = int(section[len('player'):])
		joystick_map[devicenum] = { }

	if section.startswith('player'):
		playernum = int(section[len('player'):])
		joystick_map[devicenum][playernum] = [ ]
		for event in cfg.options(section):
			keylist = cfg.get(section, event).split()

			# button event
			if event.startswith('btn_'):
				joystick_map[devicenum][playernum].append(('button', uinput.__dict__[event.upper()], keylist))

			# axis event
			elif event.startswith('abs_'):
				joystick_map[devicenum][playernum].append(('axis', uinput.__dict__[event.upper()], keylist[0], keylist[1]))

			else:
				raise ValueError

print joystick_map

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

# hook SIGTERM to exit gracefully
do_exit = False
def cleanup_handler(signal, frame):
	global do_exit
	print "Shutting down."
	do_exit = True

signal.signal(signal.SIGINT,  cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)

while not do_exit:
	for device in jvs_state.devices:
		if 'switches' in device.capabilities:
			try:
				sw = jvs_state.read_switches(device.address, device.capabilities['switches']['players'])
				if device.address in joystick_map:
					for player_id in range(0, device.capabilities['switches']['players']+1):
						if player_id in joystick_map[device.address]:
							for map_entry in joystick_map[devicenum][playernum]:
								if map_entry[0] == 'button':
									for swid in map_entry[2]:
										if (old_sw == None) or (old_sw[player_id][swid] != sw[player_id][swid]):
											if sw[player_id][swid]:
												device.uinput_devices[player_id].emit(map_entry[1], 1, syn=False)
											else:
												device.uinput_devices[player_id].emit(map_entry[1], 0, syn=False)

								elif map_entry[0] == 'axis': 
									device.uinput_devices[player_id].emit(map_entry[1], 1 + sw[player_id][map_entry[2]] - sw[player_id][map_entry[3]], syn=False)

								else:
									raise ValueError
				device.uinput_devices[player_id].syn()	# fire all events
				old_sw = sw
			except jvs.TimeoutError:
				if args.verbose > 0:
					print 'Timeout occurred while reading switches.'
