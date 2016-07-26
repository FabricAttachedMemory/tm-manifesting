#!/bin/bash

#  Fire up qemu-system-aarch64 direct boot on BIOS firmware using extended
# image (300MB+). VDA1 drive.

MAC=$1
NETNAME="pxe_ar"

QEMU="qemu-system-aarch64"
QEMU_EXTRA="-M virt -cpu cortex-a57 -machine accel=tcg"
BIOS="-bios /usr/share/ovmf/OVMF.fd"
MEMORY="-m 2048" # Need to trim kernel and initrd

KERNEL="-kernel ${ARTIFACTS}/l4tm.untar/boot/vmlinuz-*"
INITRD="-initrd ${ARTIFACTS}/l4tm.untar/boot/initrd.img*"
RROOT="root=/dev/vda1"
APPEND="$RROOT console=ttyAMA0 earlycon=pl011,0x9000000 rw"
FSIMG="-drive file=${ARTIFACTS}/l4tm.img,format=raw,if=none,id=hd0"
DRIVE="-device virtio-blk-device,drive=hd0"

NIC="-device virtio-net-device,mac=$MAC,netdev=thisbridge"
CONSOLE="-serial stdio"
