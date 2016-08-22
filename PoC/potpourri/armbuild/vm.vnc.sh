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
	cp /$MNT/boot/$PATTERN .
done
sudo umount $MNT

sudo -E qemu-system-aarch64 -m 2048 \
	-M virt -cpu cortex-a57 -machine accel=tcg \
	-kernel vmlinuz-* \
	-append "root=/dev/vda1 console=ttyAMA0 earlycon=pl011,0x9000000 rw" \
	-initrd initrd.img-* \
	-bios /usr/share/ovmf/OVMF.fd \
	-drive file=$FSIMG,format=raw,if=none,id=hd0 \
	-device virtio-blk-device,drive=hd0 \
	-netdev bridge,br=br2HP,id=thisbridge \
	-device virtio-net-device,mac=52:54:48:50:45:07,netdev=thisbridge \
	-vnc 127.0.0.1:27
