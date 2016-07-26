#!/bin/bash

# Fire up qemu-system-x86_64 on BIOS firmware using PXE boot

MAC=$1
NETNAME="pxe_arm"

QEMU="qemu-system-aarch64"
MEMORY="-m 2048"     # Need to trim kernel and initrd
QEMU_EXTRA="-M virt -cpu cortex-a57 -machine accel=tcg"
BIOS="-bios $PWD/firmware/QEMU_EFI.fd"

NIC="-device virtio-net-device,mac=$MAC,netdev=thisbridge"
CONSOLE="-serial stdio"
