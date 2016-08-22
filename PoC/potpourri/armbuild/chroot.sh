#!/bin/bash

set -u

FSIMG=vda.l4tm.arm64.img
MNT=/mnt/wtf
[ -d $MNT ] || mkdir $MNT
[ ! -d $MNT ] && echo "Can't obtain $MNT" 2>&1 && exit 0

sudo mount -oloop,offset=1M $FSIMG $MNT
sudo chroot $MNT
sudo umount $MNT

exit 0
