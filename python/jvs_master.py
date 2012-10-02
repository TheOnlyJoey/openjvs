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
import signal

def verbose(level, message):
	global args
	if args.verbose >= level:
		print(message)

# parse arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-s", "--serial-device",  default="/dev/ttyUSB0", metavar="DEVICE", help="Use device DEVICE as a JVS connection")
parser.add_argument("-c", "--config", dest="config_filename", default="jvs_master.cfg", metavar="FILENAME", help="use file FILENAME as config file")
parser.add_argument("--assume-devices", type=int, default=None, metavar="N", help="If given, skip regular address setting procedure and assume N devices connected.")
parser.add_argument("-v", dest="verbose", action="count", help="Enter verbose mode, which shows more information on the bus traffic. Use more than once for more output.")
parser.add_argument("-d", "--debug", dest="verbose", action='store_const', const=5, help="Turns verbosity all the way up to maximum, as a debugging aid.")
parser.add_argument("--dump", action="store_true", default=False, help="Store raw sent/received data in a dump file named openjvs_dump_<date>_<time>.log.")
args = parser.parse_args()

# all possible events
possible_events = {}

verbose(1, "Starting up...")

# read in config file
verbose(2, "Reading in config file %s" % args.config_filename)
cfg = ConfigParser.ConfigParser()
cfg.read(args.config_filename)

joystick_map = {}
devicenum = 0
playernum = 0

for section in cfg.sections():
	if section.startswith('device'):
		devicenum = int(section[len('player'):])
		possible_events[devicenum] = {}
		joystick_map[devicenum] = { }

	if section.startswith('player'):
		playernum = int(section[len('player'):])
		possible_events[devicenum][playernum] = [ ]
		joystick_map[devicenum][playernum] = [ ]
		for event in cfg.options(section):
			keylist = cfg.get(section, event).split()

			# button event
			if event.startswith('btn_'):
				joystick_map[devicenum][playernum].append(('button', uinput.__dict__[event.upper()], keylist))
				possible_events[devicenum][playernum].append(uinput.__dict__[event.upper()])

			# axis event
			elif event.startswith('abs_'):
				joystick_map[devicenum][playernum].append(('axis', uinput.__dict__[event.upper()], keylist[0], keylist[1]))
				possible_events[devicenum][playernum].append(uinput.__dict__[event.upper()] + (0, 2, 0, 0))

			elif event.startswith('key_'):
				joystick_map[devicenum][playernum].append(('keyboard', uinput.__dict__[event.upper()], keylist))
				possible_events[devicenum][playernum].append(uinput.__dict__[event.upper()])

			else:
				raise ValueError

verbose(1, "Initializing JVS")
jvs_state = jvs.JVS(args.serial_device, dump=args.dump)
verbose(2, "Opened device %s" % jvs_state.ser.name)

verbose(2, "Resetting bus, assigning address, identifying device")
jvs_state.reset(args.assume_devices)


# device list
id_meanings = [ 'Manufacturer', 'Product name', 'Serial number', 'Product version', 'Comment' ]

verbose(3, "Devices:")

for device in jvs_state.devices:
	# dump data about device
	if args.verbose >= 3:
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
	if 'switches' in device.capabilities and device.address in possible_events:
		device.uinput_devices = { }
		if 0 in possible_events[device.address]:
			device.uinput_devices[0] = uinput.Device(possible_events[device.address][0], name='openjvs_a%dsys' % device.address)		# add system device, for TEST and TILT switches

		for player in range(1, device.capabilities['switches']['players']+1):
			if player in possible_events[device.address]:
				device.uinput_devices[player] = uinput.Device(possible_events[device.address][player], name='openjvs_a%dp%d' % (device.address, player))	# add player device
				verbose(3, "\t\t- Creating device openjvs_a%dp%d for player %d" % (device.address, player, player))
		verbose(3, "")	# empty line


# for reading out switches
status_str = ''
old_length = 0
old_sw = None

# hook SIGTERM to exit gracefully
do_exit = False
def cleanup_handler(signal, frame):
	global do_exit
	verbose(1, "Shutting down.")
	do_exit = True

signal.signal(signal.SIGINT,  cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)


# main loop
verbose(1, "Entering main loop...")

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

								elif map_entry[0] == 'keyboard':
									for swid in map_entry[2]:
										if (old_sw == None) or (old_sw[player_id][swid] != sw[player_id][swid]):
											if sw[player_id][swid]:
												device.uinput_devices[player_id].emit(map_entry[1], 1, syn=False)
											else:
												device.uinput_devices[player_id].emit(map_entry[1], 0, syn=False)

								else:
									raise ValueError
				device.uinput_devices[player_id].syn()	# fire all events
				old_sw = sw
			except jvs.TimeoutError:
				verbose(2, "Timeout occurred while reading switches.")