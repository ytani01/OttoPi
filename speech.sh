#!/bin/sh
#
# (c) Yoichi Tanibayashi
#
MYNAME=`basename $0`
MYDIR=`dirname $0`

STOP_FILE=$1
PKILL_WORD_MUSIC="vlc"

#####
usage () {
    echo "usage: ${MYNAME} stop_file"
}

stop_music () {
    pkill ${PKILL_WORD_MUSIC}
}

##### main
if [ X${STOP_FILE} = X ]; then
    usage
    exit 1
fi

while read s; do
    if [ -f ${STOP_FILE} ]; then
	echo "stop file: ${STOP_FILE}"
	exit 0
    fi

    stop_music
    nice -n 5 SpeakClient.py $s

    sleep 1
done
