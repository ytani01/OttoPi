#!/bin/sh -x
#
# (c) Yoichi Tanibayashi
#

STOP_FILE=$1

while read s; do
    if [ -f ${STOP_FILE} ]; then
	echo "stop file: ${STOP_FILE}"
	exit 0
    fi
    pkill vlc
    nice -n 5 SpeakClient.py $s
done
sleep 60
