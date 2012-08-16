# jvs-master.py -- JVS bus master over USB-to-RS232 hardware

import sys
import serial
import time

# low-level protocol constants
SYNC			= 0xE0
ESCAPE			= 0xD0

# command results
STATUS_OK		= 0x01
REPORT_SUCCESS	= 0x01

# capability struct constants
# inputs
CAP_END			= 0x00	# end of structure
CAP_PLAYERS		= 0x01	# player/switch info
CAP_COINS		= 0x02	# coin slot info
CAP_ANALOG		= 0x03	# analog info
CAP_ROTARY		= 0x04	# rotary encoder info
CAP_KEYPAD		= 0x05	# keypad info
CAP_LIGHTGUN	= 0x06	# light gun info
CAP_GPI			= 0x07	# general purpose input info

# outputs
CAP_CARD		= 0x10	# card system info
CAP_HOPPER		= 0x11	# token hopper info
CAP_GPO			= 0x12	# general purpose output info
CAP_ANALOG		= 0x13	# analog output info
CAP_DISPLAY		= 0x14	# character display info
CAP_BACKUP		= 0x15	# backup memory?

# the display encodings supported by the protocol
encodings = [ "unknown", "ascii numeric", "ascii alphanumeric", "alphanumeric/katakana", "alphanumeric/SHIFT-JIS" ]

# receive a single byte from the bus
def get_byte(ser):
	b = ser.read(1)
	if len(b) == 0:
		return None
	else:
		return ord(b)

# receive a full packet from the bus. This assumes there is a packet waiting. TODO: make it time out
def get_packet(ser):
	b = 0
	while b != SYNC:
		b = get_byte(ser)

	dest = get_byte(ser)
	l = get_byte(ser)		# length
	seq = [ ]
	s = dest+l
	for i in range(1, l):	# message contents
		b = get_byte(ser)
		if b == ESCAPE:
			b = get_byte(ser)+1
		seq.append(b)
		s = (s + b) % 256	# compute checksum

	s_rec = get_byte(ser)	# received checksum
	if s_rec == s:
		return [ dest, seq ]
	else:
		print "checksum failure: received %d, computed %d" % (s_rec, s)
		return None

# send a single byte to the bus
def send_byte(ser, byte):
	ser.write(chr(byte))

# send a full packet to the bus.
def send_packet(ser, dest, seq):
	send_byte(ser, SYNC)
	send_byte(ser, dest)
	send_byte(ser, len(seq)+1)
	s = dest+len(seq)+1
	for b in seq:
		if b == SYNC or b == ESCAPE:	# escape sync/escape bytes in message
			send_byte(ser, ESCAPE)
			send_byte(ser, b-1)
		else:
			send_byte(ser, b)

		s = (s + b) % 256
	send_byte(ser, s)

if __name__ == "__main__":
	# start of main program -- resets the bus and identifies the attached device
	# okay basic sanity check

	# main loop
	print "opening serial port..."
	if len(sys.argv)>1:
		ser = serial.Serial(port=sys.argv[1], baudrate=115200, timeout=1)
	else:
		ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=1)

	print "initializing bus..."
	send_packet(ser, 0xff, [ 0xf0, 0xd9 ])	# bus reset

	time.sleep(1)
	print "Sending address...",
	send_packet(ser, 0xff, [ 0xf1, 0x01 ])	# assume one connected device -- send address 1
	reply = get_packet(ser)
	if reply == None:
		print "no reply received"
		sys.exit()

	elif (reply[1][0] != STATUS_OK) or (reply[1][1] != REPORT_SUCCESS):
		print "Error setting address"
		print "error codes: ", reply[1][0], reply[1][1]
		sys.exit()

	else:
		print "OK"

	time.sleep(1)
	print "asking for identification...",
	send_packet(ser, 0x01, [ 0x10 ]) # request ID string
	reply = get_packet(ser)
	if reply[1][0] != STATUS_OK or reply[1][1] != REPORT_SUCCESS:
		print "Error getting identification string"
		print "error codes: ", reply[1][0], reply[1][1]
		sys.exit()

	for b in reply[1]:
		if b == 0:
			break
		sys.stdout.write(chr(b))

	print "\nasking for versions..."
	send_packet(ser, 0x01, [ 0x11, 0x12, 0x13 ]) # request version numbers
	reply = get_packet(ser)
	if reply[1][0] != STATUS_OK:
		print "device error, status code %d" % reply[1][0]
	
	if reply[1][1] != REPORT_SUCCESS:
		print "\tError getting communications version number, code %d" % reply[1][1]
		sys.exit()
	else:
		print "\tCommand format v%d.%d" % ((reply[1][2]&0xF0)>>4, reply[1][2]&0x0F)

	if reply[1][3] != REPORT_SUCCESS:
		print "\tError getting communications version number, code %d" % reply[1][3]
		sys.exit()
	else:
		print "\tJVS v%d.%d" % ((reply[1][4]&0xF0)>>4, reply[1][4]&0x0F)

	if reply[1][5] != REPORT_SUCCESS:
		print "\tError getting communications version number, code %d" % reply[1][5]
		sys.exit()
	else:
		print "\tCommunications protocol v%d.%d" % ((reply[1][6]&0xF0)>>4, reply[1][6]&0x0F)

	print "asking for capabilities..."
	send_packet(ser, 0x01, [ 0x14 ])	# request capability info
	reply = get_packet(ser)
	if reply[1][0] != STATUS_OK:
		print "device error, status code %d" % reply[1][0]

	i = 0
	while (2+i*4) < len(reply[1]):
		sys.stdout.write("\t")
		if reply[1][2+i*4] == CAP_END:
			print "end of record"
			break
		elif reply[1][2+i*4] == CAP_PLAYERS:
			print "%d players, %d switches per player" % (reply[1][i*4+3], reply[1][i*4+4])
		elif reply[1][2+i*4] == CAP_COINS:
			print "%d coin slots" % reply[1][i*4+3]
		elif reply[1][2+i*4] == CAP_ANALOG:
			print "%d analog channels, %d number of effective bits per channel" % (reply[1][i*4+3], reply[1][i*4+4])
		elif reply[1][2+i*4] == CAP_ROTARY:
			print "%d rotary encoder channels" % reply[1][i*4+3]
		elif reply[1][2+i*4] == CAP_KEYPAD:
			print "keypad present"
		elif reply[1][2+i*4] == CAP_LIGHTGUN:
			print "light gun with %d effective x bits, %d effective y bits and %d channels" % (reply[1][i*4+3], reply[1][i*4+4], reply[1][i*4+5])
		elif reply[1][2+i*4] == CAP_GPI:
			print "%d general-purpose inputs" % ((reply[1][i*4+3]<<8) | reply[1][i*4+4])

		elif reply[1][2+i*4] == CAP_CARD:
			print "card system with %d slots" % reply[1][i*4+3]
		elif reply[1][2+i*4] == CAP_HOPPER:
			print "token hopper with %d channels" % reply[1][i*4+3]
		elif reply[1][2+i*4] == CAP_GPO:
			print "%d general-purpose output banks" % reply[1][i*4+3]
		elif reply[1][2+i*4] == CAP_ANALOG:
			print "%d analog output channels" % reply[1][i*4+3]
		elif reply[1][2+i*4] == CAP_DISPLAY:
			print "alphanumeric display: %d characters/line, %d lines, %s encoding" % (reply[1][i*4+3], reply[1][i*4+4], encodings[reply[1][i*4+5]])
		elif reply[1][2+i*4] == CAP_BACKUP:
			print "backup present"
		i += 1

	print "done."
