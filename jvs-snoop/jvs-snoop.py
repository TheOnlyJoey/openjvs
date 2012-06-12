# jvs-snoop.py
# dumps JVS I/O bus traffic to stdout

from optparse import OptionParser
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
	p.length	= get_byte(ser)

	# read contents
	p.data = []
	for i in range(num_bytes-1):
		b = get_byte(ser)
		if b == ESCAPE:				# escape char
			b = get_byte(ser)-1
		p.data.append(b)

	# checksum
	checksum = get_byte(ser)
	# TODO: verify


# start of main program
# parse command line arguments
parser = OptionParser()
parser.add_option("-p", "--port", dest="port", help="use PORT as serial device to read from", metavar="PORT", default="/dev/ttyUSB0")
parser.add_option("-r", "--raw", action="store_false", dest="cooked", default=True, help="don't parse packets, show hex data instead")

(options, args) = parser.parse_args()


ser = serial.Serial(options.port, 115200)
while 1:
	p = get_packet(ser)
	if options.cooked:
		if p.to == 0:
			print reply(packet)
		else:
			print command(packet)
	else:
		print packet
