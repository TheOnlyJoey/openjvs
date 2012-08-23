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

### python ###
This subdirectory contains two programs, jvs-master and jvs-snoop, written in the Python programming language. They interface to the bus -- one as a bus master, the other as a listener via a splitter cable for debugging.

### jvs-hid ###
This subdirectory is meant for the hard- and software for a custom USB device
that will translate as much of the protocol as possible to USB using a
microcontroller. Development on this has only just started at the time of
this writing.
