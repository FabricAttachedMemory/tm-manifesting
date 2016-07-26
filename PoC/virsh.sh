#!/bin/bash

set -u

OPT=$1

if [ "${2:-}" ]; then
    target=$2
fi

if [ "${3:-}" ]; then
    target_2=$3
fi
isError=0

case $OPT in
    -ls|-l|-ll)
        echo
        sudo brctl show
        echo
    ;;
    -e)
        sudo virsh net-edit $target
    ;;
    -dest)
       sudo virsh net-destroy $target
    ;;
    -def)
       sudo virsh net-define $target
    ;;
    -undef)
        sudo virsh net-undefine $target
    ;;
    -start)
       sudo virsh net-start $target
    ;;
    -re-start)
        sudo virsh net-destroy $target_2
        sudo virsh net-start $target
    ;;
    -re-conf)
        file_name=$3
        sudo virsh net-destroy $target
        sudo virsh net-undefine $target
        sudo virsh net-define $file_name
        sudo virsh net-list --all
    ;;
    *)
    isError=1
    echo "
-ls
-e [target]
-dest [target]
-def [target]
-undef [target]
-start [target]
-re-start [to-start] [to-destroy]
-re-conf [target] [xml file]"
    echo
    ;;
esac

if [ $isError == 0 ]; then
    sudo virsh net-list --all
fi
