# jvs-snoop.py
# dumps JVS I/O bus traffic to stdout

from optparse import OptionParser
import sys
import serial

# constants
SYNC	= 0xE0
ESCAPE	= 0xD0

def get_byte(ser):
	return ord(ser.read())

class packet:
	to		= 0x00
	length	= 0x00
	data	= None

	def __str__(self):
		s = 'packet to {0} length {1}: {2}'.format(self.to, self.length, ' '.join(map('{X}'.format, self.data)))

def get_packet(ser)
	p = packet()

	# read sync
	b = 0
	while b != SYNC:
		b = ord(ser.read())

	# read header
	p.to 		= get_byte(ser)
	p.length	= get_byte(ser)-1	# length field includes the sum byte, we don't want that

	computed_checksum = (p.to + p.length) % 256

	# read contents
	p.data = []
	for i in range(p.length):
		b = get_byte(ser)
		if b == ESCAPE:				# escape byte
			b = get_byte(ser)-1
		computed_checksum = (computed_checksum + b) % 256
		p.data.append(b)

	# checksum
	checksum = get_byte(ser)
	if computed_checksum == checksum:
		return p

# dump a command packet and return the command identifiers so we know what to expect in the reply
def dump_commands(p):
	i = 0
	last_commands = []
	while i < p.length:
		code = p.data[i]
		sys.stdout.write('command code {X}'.format(code))
		last_commands.append(code)
		i+=1
		# big command code switch
		# broadcast commands
		if   code == 0xF0:
			sys.stdout.write(' (bus reset)')
		elif code == 0xF1:
			sys.stdout.write(' (assign addr)')
		elif code == 0xF2:
			sys.stdout.write(' (set communications mode)')

		# initialization commands
		elif code == 0x10:
			sys.stdout.write(' (read ID data)')
		elif code == 0x11:
			sys.stdout.write(' (get command format version)')
		elif code == 0x12:
			sys.stdout.write(' (get JVS version)')
		elif code == 0x13:
			sys.stdout.write(' (get communications version)')
		elif code == 0x14:
			sys.stdout.write(' (get slave features)')
		elif code == 0x15:
			sys.stdout.write(' (convey ID data of main board)')

		# input commands
		elif code == 0x20:
			sys.stdout.write(' (read switch inputs)')
		elif code == 0x21:
			sys.stdout.write(' (read coin inputs)')
		elif code == 0x22:
			sys.stdout.write(' (read analog inputs)')
		elif code == 0x23:
			sys.stdout.write(' (read rotary inputs)')
		elif code == 0x24:
			sys.stdout.write(' (read keypad input)')
		elif code == 0x25:
			sys.stdout.write(' (read screen pointer position)')
		elif code == 0x26:
			sys.stdout.write(' (read general-purpose input)')

		elif code == 0x2E:
			sys.stdout.write(' (read number of payouts remaining)')
		elif code == 0x2F:
			sys.stdout.write(' (request data retransmit)')

		# output commands
		elif code == 30:
			sys.stdout.write(' (decrease the number of coins)')
		elif code == 31:
			sys.stdout.write(' (do a payout?)')
		elif code == 32:
			sys.stdout.write(' (general-purpose output)')
		elif code == 33:
			sys.stdout.write(' (analog output)')
		elif code == 34:
			sys.stdout.write(' (output character data)')
		elif code == 35:
			sys.stdout.write(' (output coins?)')
		elif code == 36:
			sys.stdout.write(' (subtract payouts?)')
		elif code == 37:
			sys.stdout.write(' (general-purpose output 2)')
		elif code == 38:
			sys.stdout.write(' (general-purpose output 3)')

		# manufacturer-specific codes
		elif code >= 0x60 and code <= 0x7F:
			sys.stdout.write(' (manufacturer-specific)')
			i = p.length	# we don't know the data format for these so effectively drop the packet

		# else
		else:
			sys.stdout.write(' (unknown command)')
			i = p.length	# we don't know the data format for these so effectively drop the packet
		return last_commands

# dump reply packet, specifying the last command sequence sent
def dump_replies(p, last_commands):
	status = p.data[i]
	print 'reply status: {X}'.format(status)
	i+=1

	return

# start of main program
# parse command line arguments
parser = OptionParser()
parser.add_option("-p", "--port", dest="port", help="use PORT as serial device to read from", metavar="PORT", default="/dev/ttyUSB0")
parser.add_option("-r", "--raw", action="store_false", dest="cooked", default=True, help="don't parse packets, show hex data instead")

(options, args) = parser.parse_args()

# main loop
ser = serial.Serial(options.port, 115200)
while 1:
	p = get_packet(ser)
	if options.cooked:
		if p.to == 0:	# if the packet is addressed to the master, treat it as a reply
			dump_replies(p, last_commands)
		else:			# else treat it as a command from the master
			last_commands = dump_commands(p)
	else:
		print packet
