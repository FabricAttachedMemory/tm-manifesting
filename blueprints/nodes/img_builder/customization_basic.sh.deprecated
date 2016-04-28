#!/bin/bash
#
# Customie golden system image.
#

MANIFEST=/opt/hpetm/manifesting/
# if [ ! -d "$MANIFEST" ]; then
#   echo "/opt/hpetm/manifesting/ folder doesn't exist!"
#   exit 1
# fi

PKG_LIST=


function check_chroot {
    # Check if chrooted, source:
    # http://stackoverflow.com/questions/75182/detecting-a-chroot-jail-from-within
    root_inode=$(stat -c %i /);
    if [ $root_inode -lt 5 ]; then # TODO: IDK IF THAT'S A LEGIT WAY TO DO THAT
      echo "========================"
      echo "Warning! You are not chrooted to any file system image!"
      echo "This may cause unexpected data corruption on your main system!"
      echo "========================"
      exit 1
    fi
} # check_chroot


function cleanout_kernel {
  check_chroot
  touch /all.good
  # Those two are not needed for a diskless image and take too much space.
  # find /boot/ -name vmlinuz* -delete
  # find /boot/ -name initrd.img* -delete
} #cleanout_kernel


function set_fstab {
  CONTENT=$1
  content_match=`grep "$CONTENT" /etc/fstab`
  #Don't add more if the same content already in the file
  if [ -z "$content_match" ]; then
    echo -e "$CONTENT" >> /etc/fstab
    return 0
  fi
  return 1
} #set_fstab


function set_hostname {
  if [ -z "${1:-}" ]; then
    echo "missing [hostname] argument."
    exit 1
  fi
  HOSTNAME=$1
  echo "$HOSTNAME" > /etc/hostname
} #set_hostname


function configure_etc_default {
  # TODO:
  # configure etc/default/
  #
  echo "Not Implemented."
} # configure_etc_default


function configure_avahi_daemon {
  # TODO:
  # /init
  # /etc/avahi/avahi-daemon.conf
  # /etc/apt/sources.list.d/base.list and /etc/apt/sources.list
  #
  echo "Not Implemented."
} # configure_avahi_daemon


function configure_init {

    check_chroot

    MODE=$1
    INIT=/init

    if [ $MODE = systemd ]; then

        cd /
        rm -f $INIT    # paranoia
        ln -s /sbin/init $INIT

    elif [ $MODE = simple ]; then
        # This may need /initrd.img -> /boot/initrd.img-xxxxx
        echo "Generate ENOEXEC to cycle kernel to /sbin/init" > $INIT
        chmod 755 $INIT

    elif [ $MODE = sysV ]; then

        # Grab the "init" program from real initrd and use it as /init.
        # It doesn't quite finish off properly when systemd is installed,
        # "Cannot find alternative telinit implementation to spawn".

        INITRDIR=/tmp/initrdir
        rm -rf $INITRDIR
        mkdir $INITRDIR
        pushd $INITRDIR
        ls -l /boot
        /bin/pwd
        zcat /boot/initrd.img* | cpio -idv
        popd
        for TARGET in conf init scripts; do
            cp -r $INITRDIR/$TARGET /
        done
        chmod 755 $INIT
    fi
} # configure_init


# check_chroot

# configure_init systemd

# if [ -z "${1:-}" ]; then
#   echo "missing [img-cfg.sh] argument."
#   exit 1
# fi
#
# IMG_CFG=$1
# source $IMG_CFG
#
#
# if [ ! -z "$HOSTNAME" ]; then
#   set_hostname $HOSTNAME
# fi
#
#
# if [ ! -z "$IS_REMOVE_KERNEL" ]; then
#   cleanout_kernel
# fi
#
#
# if [ ! -z "$FSTAB_CONTENT" ]; then
#   set_fstab "$FSTAB_CONTENT"
# fi
