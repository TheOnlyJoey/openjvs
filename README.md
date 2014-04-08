# OpenJVS #
## Warning ##
Development by me has all but stalled. If you're interested in taking
over the repo, I'm sure something can be arranged.

## Introduction ##
The OpenJVS project aims to reverse engineer the commonly used JVS-I/O
protocol for arcade cabinet input devices. It also aims to document
it and provide reference implementations of useful hard- and software.

Currently we are finalizing our understanding of the protocol and
developing hard- and software to serve as bus master for a device.

### Contact ###
The principal maintainer of this project is Roy Smeding; reachable
through GitHub as roysmeding and e-mail as roy.smeding@gmail.com.

## Subdirectories ##
Subdirectories are split up by subproject. Currently, the following
subdirectories are present:

### python ###
This subdirectory contains two programs, jvs-master and jvs-snoop,
written in the Python programming language. They interface to the bus
-- one as a bus master, the other as a listener via a splitter cable
for debugging.

## wiki ##
Information about the protocol can be found on our wiki, at https://github.com/TheOnlyJoey/openjvs/wiki
