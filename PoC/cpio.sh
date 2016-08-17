#!/bin/bash

# Get the bootable pieces: initrd CPIO and a kernel.  Stick them into
# the (presumed) tftp hosting directory that's relative to PWD.

set -u
DISTRO=$1
MANIFEST_ARCH=${MANIFEST_ARCH:-`dpkg --print-architecture`}

# Where the preceeding untar.sh has unpacked and fixed the FS layout.
SUBDIR=artifacts
[ ! -d $SUBDIR ] && echo No such dir $SUBDIR >&2 && exit 1
[ ! -d ../tftp ] && echo No such dir ../tftp >&2 && exit 1
cd $SUBDIR

UNTAR=$DISTRO.untar
[ ! -d $UNTAR ] && echo "Missing $UNTAR" >&2 && exit 1
cd $UNTAR
TARGET=../../../tftp/$MANIFEST_ARCH

sudo echo	# just to get the password set before the pipeline

# Strip out the kernel and initrd.  Skip the top symlinks and the 
# entire boot directory

sudo find . -not -name vmlinuz -not -name initrd.img \
	    -path ./boot -prune -o -print | \
	sudo cpio --create --format 'newc' > $TARGET/$DISTRO.cpio

KERNEL=`basename boot/vmlinuz*`
cp boot/$KERNEL  $TARGET/$DISTRO.vmlinuz

exit 0