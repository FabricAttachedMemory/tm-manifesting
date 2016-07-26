#!/bin/bash

# Fire up qemu-system-aarch64 direct boot on BIOS firmware.


NETNAME="pxe_arm"

MAC=$1

QEMU="qemu-system-aarch64"
QEMU_EXTRA="-M virt -cpu cortex-a57 -machine accel=tcg"
BIOS="-bios /usr/share/ovmf/OVMF.fd"
MEMORY="-m 2048"		# Need to trim kernel and initrd

TFTP=../tftp/arm64
[ ! -d $TFTP ]  && 'Missing $TFTP' >&2 && exit 1

KERNEL="$TFTP/l4tm.vmlinuz"
INITRD="$TFTP/l4tm.cpio"

check_initrd_and_kernel $KERNEL $INITRD # in diskless.sh

INITRD="-initrd $INITRD"
KERNEL="-kernel $KERNEL"

RROOT="root=/dev/sdb1"
APPEND="$RROOT console=ttyAMA0 earlycon=pl011,0x9000000 rw"

NIC="-device virtio-net-device,mac=$MAC,netdev=thisbridge"
CONSOLE="-serial stdio"
