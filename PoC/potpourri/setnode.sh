#!/bin/bash

set -u

NODES=$1
MANIFEST=$2

if [ "$NODES" = all ]; then
	NODES=`tm-manifest listnodes | jq -r '."200".nodes[]' | sort`
fi

START=`date +%s`
for N in $NODES; do
	echo $N
	tm-manifest getnode $N >/dev/null 2>&1
	[ $? -ne 0 ] && echo "Can't getnode $N" >&2 && exit 
	tm-manifest unsetnode $N >/dev/null 2>&1
	tm-manifest setnode $N $MANIFEST	# This status is ok
done
let ELAPSED=`date +%s`-$START

function sec2ascii() {
	let H=$1/3600
	let M=$1/60
	let S=$1%60
	printf "%2d:%02d:%02d" $H $M $S
}

echo "`sec2ascii $ELAPSED` all bindings started"

FINISHED=0
while [ $FINISHED -lt 40 ]; do
	sleep 5
	FINISHED=`find /var/lib/tmms/tftp/images -name status.json | xargs cat | grep ready | grep status | wc -l`
	let ELAPSED=`date +%s`-$START
	echo "`sec2ascii $ELAPSED` $FINISHED bindings finished"
done
exit 0
