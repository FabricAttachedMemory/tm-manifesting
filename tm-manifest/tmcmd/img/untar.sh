#!/bin/bash

set -u
BASE=$1

# Without SUBDIR the vmdebootstrap won't work, but be paranoid here.
SUBDIR=/opt/hpetm/manifesting/$2/
[ ! -d $SUBDIR ] && echo No such dir $SUBDIR >&2 && exit 1
cd $SUBDIR

TARBALL=$BASE.tar
[ ! -f $TARBALL ] && echo No such file $TARBALL >&2 && exit 1
UNTAR="$PWD/$BASE.untar"
[ -d "$UNTAR" ] && sudo rm -rf "$UNTAR"
mkdir "$UNTAR" || exit 86

# tar cannot mknod.  Filter those and pass others, there's always a summary
# line when tar detected any error, filter that too.  Preserve flags need sudo.
TAR="tar -C $UNTAR --preserve-permissions --same-owner -xf $TARBALL"
date
/bin/pwd
echo $TAR
ERRORS=`sudo $TAR 2>&1 >/dev/null | grep -v mknod`
ERRORS=`echo $ERRORS | grep -v "previous errors"`

[ "$ERRORS" ] && echo tar extraction failed >&2 && echo $ERRORS && exit 1

###########################################################################
# Special voodoo: move from initrd mode to full run mode.

INIT=$UNTAR/init

MODE=systemd	# systemd is the real deal; simple and sysV were experiments

if [ $MODE = systemd ]; then	# -----------------------------------------

	sudo rm -f $INIT	# paranoia
	sudo ln -s /sbin/init $INIT

elif [ $MODE = simple ]; then	# -----------------------------------------

	# This may need /initrd.img -> /boot/initrd.img-xxxxx
	sudo echo "Generate ENOEXEC to cycle kernel to /sbin/init" > $INIT
	sudo chmod 755 $INIT

elif [ $MODE = sysV ]; then	# -----------------------------------------

	# Grab the "init" program from real initrd and use it as /init.
	# It doesn't quite finish off properly when systemd is installed,
	# "Cannot find alternative telinit implementation to spawn".

	INITRDIR=/tmp/initrdir
	rm -rf $INITRDIR
	mkdir $INITRDIR
	pushd $INITRDIR
	ls -l $UNTAR/boot
	/bin/pwd
	zcat $UNTAR/boot/initrd.img* | cpio -idv
	popd
	for TARGET in conf init scripts; do
		sudo cp -r $INITRDIR/$TARGET $UNTAR
	done
	sudo chmod 755 $INIT
else				# -----------------------------------------
	echo "Dummy, $MODE is not an option" >&2 && exit 1
fi				# -----------------------------------------

###########################################################################
# Simple voodoo.
# Customize Avahi behavior

AVAHICONF=$UNTAR/etc/avahi/avahi-daemon.conf
[ -f $AVAHICONF ] && sudo sed -i -e 's/^use-ipv6=yes$/use-ipv6=no/' $AVAHICONF

# vmdebootstrap ALWAYS puts ftp.us.debian.org in /etc/apt/sources.list
# along with the chosen suite.  Sometimes this is wrong (ie, when it pairs
# ""catapult").  If 'configure-apt' is chosen, the real mirror goes into
# /etc/apt/sources.list.d/base.list and this can actually collide with
# the default.  Let there be only one.

SINGLE=$UNTAR/etc/apt/sources.list
SOURCE=$UNTAR/etc/apt/sources.list.d/base.list
[ -f $SOURCE ] && sudo mv -f $SOURCE $SINGLE

exit 0
