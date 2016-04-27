#!/bin/bash

# Get the bootable pieces: initrd CPIO and a kernel.  Stick them into
# the (presumed) tftp hosting directory that's relative to PWD.

set -u

TARGET=$1
DEST=$2

sudo find $TARGET -not -name vmlinuz -not -name initrd.img \
	    -path ./boot -prune -o -print | \
	sudo cpio --create --format 'newc' > $DEST/bender.cpio

exit 0
