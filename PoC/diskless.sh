#!/bin/bash

# Fire off a qemu session for the given node (1-80) to do a diskless boot.
# See PXE/pxeboot.net.xml for more details.

BOOT_CFG=$2

QEMU=
MEMORY=
QEMU_EXTRA=
BIOS=
KERNEL=
INITRD=
APPEND=
PFLASH=
DRIVE=
FSIMG=
NETDEV=
NIC=
CONSOLE=

NODE_ID=$1
[ -z "$NODE_ID" ] && echo "usage: `basename $0` node_id" >&2 && exit 1
MANIFEST_ARCH=${MANIFEST_ARCH:-amd64}
set -u

sudo echo       # get it out of the way now

# Must match XML definition in PXE directory
[[ "$MANIFEST_ARCH" == *"arm"* ]] && NETNAME=pxe_arm || NETNAME=pxe_amd

DECIMAL=`printf '%02d' $NODE_ID`
[ "$DECIMAL" -lt 1 -o "$DECIMAL" -gt 80 ] && echo Bad node id >&2 && exit 1
MAC="52:54:48:50:45:$DECIMAL"

MANIFEST_ARCH=${MANIFEST_ARCH:-`dpkg --print-architecture`}
ARTIFACTS="$PWD/artifacts"
[ ! -d "$ARTIFACTS" ] && echo "Cannot find $ARTIFACTS" >&2 && exit 1

###########################################################################
# Networking consistency checks

# netdev helper defaults to /usr/lib/qemu/qemu-bridge-helper.
# It needs file /etc/qemu/bridge.conf, root:root, mode 640, with the line
# allow <NETNAME>
NETACCESS=/etc/qemu/bridge.conf
grep -Eq "^allow\s+$NETNAME" $NETACCESS
[ $? -ne 0 ] && echo "Missing 'allow' in $NETACCESS" >&2 && exit 1

# Avahi browsing should be enabled for service discovery
AVAHI=/etc/avahi/avahi-daemon.conf
grep -Eq "^allow-interfaces=.*$NETNAME" $AVAHI
[ $? -ne 0 ] && echo "Missing 'allow-interfaces' in $AVAHI" >&2 && exit 1

###########################################################################
# Construct the qemu command

# Add this stanza below to suppress the SDL window.  Note that's where you
# choose your boot image so insure pxelinux.cfg/default has a timeout.
# -display none

NETDEV="-netdev bridge,br=$NETNAME,id=thisbridge"	# Common

# Set QEMU arguments
source $BOOT_CFG $MAC

# Fire up QEMU
sudo $QEMU \
  $MEMORY \
  $QEMU_EXTRA \
  $BIOS \
  $KERNEL \
  $INITRD \
  --append "$APPEND" \
  $PFLASH \
  $DRIVE \
  $FSIMG \
  $NETDEV \
  $NIC \
  $CONSOLE

stty sane

# Discarded stanzas
# -chardev vc,id=console,width=1024,height=768,rows=30,cols=80
# -device virtio-serial attaches "late" in the boot process
# isa-serial is much earlier, needs boot stanza "console=ttyS0"

check_initrd_and_kernel(){
  echo "Checking kernel..."
  vmlinuz=$1
  cpio=$2
  [ ! -f "$vmlinuz" ] && echo "Missing vmlinuz file: $vmlinuz" >&2 && exit 1
  [ ! -f "$cpio" ] && echo "Missing cpio file: $cpio" >&2 && exit 1
} #end of check_cpio
