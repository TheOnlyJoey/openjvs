# jvs_constants.py -- constants used in the JVS protocol
"This file describes the slew of constants used in the jvs.py library."

# low-level protocol constants
SYNC        = 0xE0
ESCAPE      = 0xD0
BROADCAST   = 0xFF
BUS_MASTER  = 0x00
DEVICE_ADDR_START = 0x01

# status codes from devices
# There is one status byte even when multiple commands are sent in a packet
STATUS_SUCCESS          = 0x01  # all went well
STATUS_UNSUPPORTED      = 0x02  # an unsupported command was sent
STATUS_CHECKSUM_FAILURE = 0x03  # the checksum on the command packet did not match a computed checksum
STATUS_OVERFLOW         = 0x04  # an overflow occurred while processing the command

# There is one report byte per command sent.
REPORT_SUCCESS          = 0x01  # all went well
REPORT_PARAMETER_ERROR1 = 0x02  # TODO: work out difference between this one and the next
REPORT_PARAMETER_ERROR2 = 0x03
REPORT_BUSY             = 0x04  # some attached hardware was busy, causing the request to fail


# bus commands
# broadcast commands
CMD_RESET           = 0xF0  # reset bus
CMD_RESET_ARG       = 0xD9  # fixed argument to reset command
CMD_ASSIGN_ADDR     = 0xF1  # assign address to slave
CMD_SET_COMMS_MODE  = 0xF2  # switch communications mode for devices that support it, for compatibility

# initialization commands
CMD_REQUEST_ID      = 0x10  # requests an ID string from a device
CMD_COMMAND_VERSION = 0x11  # gets command format version as two BCD digits packed in a byte
CMD_JVS_VERSION     = 0x12  # gets JVS version as two BCD digits packed in a byte
CMD_COMMS_VERSION   = 0x13  # gets communications version as two BCD digits packed in a byte
CMD_CAPABILITIES    = 0x14  # gets a special capability structure from the device
CMD_CONVEY_ID       = 0x15  # convey ID of main board to device

# I/O commands
CMD_READ_SWITCHES   = 0x20  # read switch inputs
CMD_READ_COINS      = 0x21  # read coin inputs
CMD_READ_ANALOGS    = 0x22  # read analog inputs
CMD_READ_ROTARY     = 0x23  # read rotary encoder inputs
CMD_READ_KEYPAD     = 0x24  # read keypad inputs
CMD_READ_LIGHTGUN   = 0x25  # read light gun inputs
CMD_READ_GPI        = 0x26  # read general-purpose inputs

CMD_RETRANSMIT      = 0x2F  # ask device to retransmit data
CMD_DECREASE_COINS  = 0x30  # decrease number of coins

CMD_WRITE_GPO       = 0x32  # write to general-purpose outputs
CMD_WRITE_ANALOG    = 0x33  # write to analog outputs
CMD_WRITE_DISPLAY   = 0x34  # write to an alphanumeric display

# manufacturer-specific
CMD_MANUFACTURER_START  = 0x60  # start of manufacturer-specific commands
CMD_MANUFACTURER_END    = 0x7F  # end of manufacturer-specific commands


# capability structure values
CAP_END         = 0x00  # end of structure

# inputs
CAP_PLAYERS     = 0x01  # player/switch info
CAP_COINS       = 0x02  # coin slot info
CAP_ANALOG_IN   = 0x03  # analog info
CAP_ROTARY      = 0x04  # rotary encoder info
CAP_KEYPAD      = 0x05  # keypad info
CAP_LIGHTGUN    = 0x06  # light gun info
CAP_GPI         = 0x07  # general purpose input info

# outputs
CAP_CARD        = 0x10  # card system info
CAP_HOPPER      = 0x11  # token hopper info
CAP_GPO         = 0x12  # general purpose output info
CAP_ANALOG_OUT  = 0x13  # analog output info
CAP_DISPLAY     = 0x14  # character display info
CAP_BACKUP      = 0x15  # backup memory?

# string values for encodings
ENCODINGS = [ "unknown", "ascii numeric", "ascii alphanumeric", "alphanumeric/katakana", "alphanumeric/SHIFT-JIS" ]

# button bit masks for replies to command 
# general byte
BTN_GENERAL_TEST    = 1 << 7
BTN_GENERAL_TILT1   = 1 << 6
BTN_GENERAL_TILT2   = 1 << 5
BTN_GENERAL_TILT3   = 1 << 4

# first player byte
BTN_PLAYER_START    = 1 << 7
BTN_PLAYER_SERVICE  = 1 << 6
BTN_PLAYER_UP       = 1 << 5
BTN_PLAYER_DOWN     = 1 << 4
BTN_PLAYER_LEFT     = 1 << 3
BTN_PLAYER_RIGHT    = 1 << 2
BTN_PLAYER_PUSH1    = 1 << 1
BTN_PLAYER_PUSH2    = 1 << 0

# part of second byte
BTN_PLAYER_PUSH3    = 1 << 7
BTN_PLAYER_PUSH4    = 1 << 6
BTN_PLAYER_PUSH5    = 1 << 5
BTN_PLAYER_PUSH6    = 1 << 4
BTN_PLAYER_PUSH7    = 1 << 3
BTN_PLAYER_PUSH8    = 1 << 2
BTN_PLAYER_PUSH9    = 1 << 1


# timing data for the bus, in seconds
INIT_DELAY          = 1.0   # delay after a bus reset to wait for devices to initialize
CMD_DELAY           = 0.01  # delay between commands
