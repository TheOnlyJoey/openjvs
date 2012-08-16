The OpenJVS project is started to reverse engineer the common used JVS Arcade 
protocol, and document how to use the protocol for writing a usb-hid 
for common hardware (currently using FT232 and RS485 chips).

Currently we are in the process of writing a parser for 
information we acquire using a custom board created with a 
FT232 and rs485 chip.

--- Data Gathering ---

Data can be gathered using our custom board, by sidechaining between the JVS
harness (we are using a Naomi Universal) and a Arcade board 
(we are using a Sega Lindbergh Yellow.)

JVS -> |Custom Board| -> Lindbergh
	     |
	     PC

The PC captures the data between the JVS and the Lindbergh which can be
displayed in a terminal with serial over usb.
Currently a parser is written in python, to display as much possible as
we can decode based on known Japanese documentation and guessing.

--- Final Implementation ---

The final implementation will be a general usb-hid driver that can be used
on easy to aquire hardware
