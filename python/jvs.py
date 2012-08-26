# jvs.py -- low-level JVS-I/O protocol library
"""
This library provides a class called JVS that implements as much of
the JVS-I/O protocol as possible using commodity USB-RS485 converters.
"""

# imports
import serial
import time
from jvs_constants import *	# haters gonna hate

# exceptions
class Error(Exception):
	"""Base class for JVS exceptions."""
	pass

class TimeoutError(Error):
	"""Raised when waiting for a packet on the bus times out."""
	def __str__(self):
		return "A time-out occurred when receiving a packet."

class ChecksumError(Error):
	"""Raised when a received packet's included checksum does not match its computed checksum"""
	def __str__(self):
		return "Checksum failure occurred while receiving a packet."

class StatusError(Error):
	"""Raised when a device signals it is in an error state."""
	def __init__(self, cmd, status):
		self.cmd	= cmd
		self.status	= status

	def __str__(self):
		return "Device signaled status error %d while processing command %d." % (self.status, self.cmd)

class ReportError(Error):
	"""Raised when a device signals it could not successfully handle a certain command."""
	def __init__(self, cmd, report):
		self.cmd	= cmd
		self.report	= report

	def __str__(self):
		return "Device signaled report error %d while processing command %d." % (self.report, self.cmd)

class StrayPacketError(Error):
	"""Raised when a reply to a command is not addressed to the bus master."""
	def __init__(self, dest_received, dest_expected):
		self.dest_received = dest_received
		self.dest_expected = dest_expected

	def __str__(self):
		return "Received a bus packet addressed to address %d when expecting one for address %d." % (self.dest_received, self.dest_expected)

# regular classes
class Device:
	"""A device on the JVS bus. Contains some identifying information and functional information."""
	def __init__(self, address, id_data, versions, capabilities):
		self.address		= address
		self.id_data		= id_data
		self.versions		= versions
		self.capabilities	= capabilities

def bcd2num(bcd):
	"""Converts the packed dual-BCD version numbers from the protocol into a fractional value; e.g. 0x12 to 1.2."""
	return ((bcd & 0xF0) >> 4) + ((bcd & 0x0F) * 0.1)

class JVS:
	"""Basic JVS object encapsulating all state involved in a JVS connection"""
	def __init__(self, port):
		"""Initializes the JVS connection. Doesn't cause a bus reset or device enumeration to take place"""
		self.ser = serial.Serial(port=port, baudrate=115200, timeout=5)	# initialize serial connection

		# initialize internal state
		self.devices = []

	def read_byte(self):
		"""Read a single byte, with no framing whatsoever. Used internally to read in a packet."""
		byte = self.ser.read(1)
		if len(byte) == 0:
			raise TimeoutError()	# read timed out
		else:
			return ord(byte)			# return byte as number

	def write_byte(self, byte):
		"""Write out a single byte with no framing. Used internally to write out a packet."""
		self.ser.write(chr(byte))

	def read_packet(self):
		"""Reads a full packet from the bus. Returns a Packet instance or throws TimeoutError."""
		byte = 0
		while byte != SYNC:	# look for sync
			byte = self.read_byte()

		destination = self.read_byte()
		length = self.read_byte()
		data = []
		checksum_computed = destination+length
		for _ in range(1, length):   # message contents
			byte = self.read_byte()
			if byte == ESCAPE:
				byte = self.read_byte()+1
			data.append(byte)
			checksum_computed = (checksum_computed + byte) % 256   # compute checksum

		checksum_received = self.read_byte()   # received checksum
		if checksum_received == checksum_computed:
			return destination, data
		else:
			raise ChecksumError()

	def write_packet(self, destination, data):
		"""Writes a full packet to the bus."""
		self.write_byte(SYNC)
		self.write_byte(destination)
		self.write_byte(len(data)+1)
		checksum = destination+len(data)+1
		for byte in data:
			if byte == SYNC or byte == ESCAPE:	# escape sync/escape bytes in message
				self.write_byte(ESCAPE)
				self.write_byte(byte-1)
			else:
				self.write_byte(byte)

			checksum = (checksum + byte) % 256
		self.write_byte(checksum)

	def cmd(self, addr, cmd):
		"""Writes a packet to the bus and listens back, then reads out status and report codes and throws relevant errors if necessary."""
		self.write_packet(addr, cmd)
		dest, data = self.read_packet()

		# error checks
		if dest != BUS_MASTER:
			raise StrayPacketError(dest, BUS_MASTER)	# this packet is supposed to be for us but it's not
		if data[0] != STATUS_SUCCESS:
			raise StatusError(cmd[0], data[0])			# status error -- error with the device
		if data[1] != REPORT_SUCCESS:
			raise ReportError(cmd[0], data[1])			# report error -- error with this command in particular

		time.sleep(CMD_DELAY)
		return data[2:]									# slice off status and report codes

	def get_capabilities(self, addr):
		"""Requests capability data from the device indicated by addr and formats it into a more Python-friendly data structure."""
		data = self.cmd(addr, [ CMD_CAPABILITIES ])
		position = 0
		capabilities = { }
		while position < len(data):
			if   data[position] == CAP_END:		break

			# inputs
			elif data[position] == CAP_PLAYERS:
				capabilities['switches'] = { 'players':data[position+1], 'switches':data[position+2] }
			elif data[position] == CAP_COINS:
				capabilities['coins'] = data[position+1]
			elif data[position] == CAP_ANALOG_IN:
				capabilities['analog_in'] = { 'channels':data[position+1], 'bits':data[position+2] }
			elif data[position] == CAP_ROTARY:
				capabilities['rotary'] = data[position+1]
			elif data[position] == CAP_KEYPAD:
				capabilities['keypad'] = True
			elif data[position] == CAP_LIGHTGUN:
				capabilities['lightgun'] = { 'xbits':data[position+1], 'ybits':data[position+2], 'channels':data[position+3] }
			elif data[position] == CAP_GPI:
				capabilities['gpi'] = (data[position+1]<<8) | data[position+2]


			# outputs
			elif data[position] == CAP_CARD:
				capabilities['card'] = data[position+1]
			elif data[position] == CAP_HOPPER:
				capabilities['hopper'] = data[position+1]
			elif data[position] == CAP_GPO:
				capabilities['gpo'] = data[position+1]
			elif data[position] == CAP_ANALOG_OUT:
				capabilities['analog_out'] = data[position+1]
			elif data[position] == CAP_DISPLAY:
				capabilities['display'] = { 'cols':data[position+1], 'rows':data[position+2], 'enc':ENCODINGS[data[position+3]] }
			elif data[position] == CAP_BACKUP:
				capabilities['backup'] = True

			position += 4

		return capabilities

	def reset(self, num_devices = None):
		"""Sends a bus reset and initializes all devices."""
		# reset the bus
		self.write_packet(BROADCAST, [ CMD_RESET, CMD_RESET_ARG ])	# send the reset packet twice as per spec
		time.sleep(INIT_DELAY)										# wait for the devices to initialize

		# assign addresses to devices
		if num_devices == None:
			device_addr = 0x01			# the address we start at, 0x00 is master
			devlist = [ ]				# temporary list of addresses to query them after this part
			sense = self.ser.getCD()	# sense line will indicate whether the protocol is done
			while sense:
				self.cmd(BROADCAST, [ CMD_ASSIGN_ADDR, device_addr ])
				devlist.append(device_addr)
				sense = self.ser.getCD()
				device_addr += 1
		else:
			for device_addr in range(1, num_devices+1):
				self.cmd(BROADCAST, [ CMD_ASSIGN_ADDR, device_addr ])
				devlist.append(device_addr)
				

		# identify devices: request ID string, version numbers and capability struct
		for device in devlist:
			# make ID data from a list of bytes into a string, and then into a list of strings
			id_data			= ''.join([ chr(b) for b in self.cmd(device, [ CMD_REQUEST_ID ])[:-1]]).split(';')

			# the three version numbers
			command_version	= bcd2num(self.cmd(device, [ CMD_COMMAND_VERSION	])[0])
			jvs_version		= bcd2num(self.cmd(device, [ CMD_JVS_VERSION		])[0])
			comms_version	= bcd2num(self.cmd(device, [ CMD_COMMS_VERSION		])[0])

			# capabilities structure, tells us what the device can do
			capabilities	= self.get_capabilities(device)

			# store inside class
			self.devices.append(Device(device, id_data,
				{ 'command':comms_version, 'jvs':jvs_version, 'comms':comms_version },
				capabilities))

	def read_switches(self, addr, num_players):
		"""Reads out the switch states of a given device. Return value is a list of dicts by player and then by button type. Player 0 contains the general switch states."""
		data = self.cmd(addr, [ CMD_READ_SWITCHES, num_players, 2 ])	# execute command -- always read 2 bytes/player

		ret = [ ]
		ret.append({	 'test':bool(data[0] & BTN_GENERAL_TEST),
					'tilt1':bool(data[0] & BTN_GENERAL_TILT1),
					'tilt2':bool(data[0] & BTN_GENERAL_TILT2),
					'tilt3':bool(data[0] & BTN_GENERAL_TILT3) })

		for player in range(0, num_players):
			ret.append({	  'start':bool(data[player*2+1] & BTN_PLAYER_START),
							'service':bool(data[player*2+1] & BTN_PLAYER_SERVICE),
							     'up':bool(data[player*2+1] & BTN_PLAYER_UP),
							   'down':bool(data[player*2+1] & BTN_PLAYER_DOWN),
							   'left':bool(data[player*2+1] & BTN_PLAYER_LEFT),
							  'right':bool(data[player*2+1] & BTN_PLAYER_RIGHT),
							  'push1':bool(data[player*2+1] & BTN_PLAYER_PUSH1),
							  'push2':bool(data[player*2+1] & BTN_PLAYER_PUSH2),

							  'push3':bool(data[player*2+2] & BTN_PLAYER_PUSH3),
							  'push4':bool(data[player*2+2] & BTN_PLAYER_PUSH4),
							  'push5':bool(data[player*2+2] & BTN_PLAYER_PUSH5),
							  'push6':bool(data[player*2+2] & BTN_PLAYER_PUSH6),
							  'push7':bool(data[player*2+2] & BTN_PLAYER_PUSH7),
							  'push8':bool(data[player*2+2] & BTN_PLAYER_PUSH8) })

		return ret
