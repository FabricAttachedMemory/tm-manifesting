#!/bin/bash

set -u

FSIMG=vda.l4tm.arm64.img
MNT=/mnt/wtf
[ -d $MNT ] || mkdir $MNT
[ ! -d $MNT ] && echo "Can't obtain $MNT" 2>&1 && exit 0

sudo mount -oloop,offset=1M $FSIMG $MNT
for PATTERN in 'vmlinuz-*' 'initrd.img-*'; do
	# F=`find /$MNT/boot/ -name '$PATTERN'`
	# echo $F
	sudo cp /$MNT/boot/$PATTERN .
done
sudo umount $MNT

sudo -E qemu-system-aarch64 -m 1024 \
	-M virt -cpu cortex-a57 -machine accel=tcg \
	-kernel vmlinuz-* \
	-append "root=/dev/vda1 console=ttyAMA0 earlycon=pl011,0x9000000 rw" \
	-initrd initrd.img-* \
	-bios /usr/share/ovmf/OVMF.fd \
	-drive file=$FSIMG,format=raw,if=none,id=hd0 \
	-device virtio-blk-device,drive=hd0 \
	-netdev bridge,br=virbr0,id=thisbridge \
	-device virtio-net-device,mac=52:54:48:42:42:42,netdev=thisbridge \
	-serial stdio
