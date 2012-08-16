# OpenJVS #
## Introduction ##
The OpenJVS project aims to reverse engineer the commonly used JVS-I/O
protocol for arcade cabinet input devices. It also aims to document
it and provide reference implementations of useful hard- and software.

Currently we are finalizing our understanding of the protocol and developing
hard- and software to serve as bus master for a device.

### Contact ###
The principal maintainer of this project is Roy Smeding; reachable through GitHub as roysmeding and e-mail as roy.smeding@gmail.com.

## Subdirectories ##
Subdirectories are split up by subproject. Currently, the following
subdirectories are present:

### jvs-snoop ###
This program snoops on existing JVS traffic using a splitter cable between a
bus host (arcade controller) and slave(s) (I/O boards).

### jvs-master ###
This program aims to provide a joystick interface over standard USB-to-RS485
hardware. Due to limitations in the hardware it will only support one slave
device.

### jvs-hid ###
This subdirectory is meant for the hard- and software for a custom USB device
that will translate as much of the protocol as possible to USB using a
microcontroller. Development on this has only just started at the time of
this writing.
