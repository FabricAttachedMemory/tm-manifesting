#!/bin/bash

# Fire up qemu-system-x86_64 on BIOS firmware using PXE

MAC=$1
NETNAME="pxe_amd"

QEMU="qemu-system-x86_64"
QEMU_EXTRA="-enable-kvm"
MEMORY="-m 1024"   # A little tight but it demos

#KERNEL, INITRD not needed, cause of pxelinux.cfg/default...

NIC="-device virtio-net,mac=$MAC,netdev=thisbridge"
CONSOLE="-chardev stdio,id=console -device isa-serial,chardev=console"
