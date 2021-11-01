#!/bin/sh
#
# (c) 2020 Yoichi Tanibayashi
#
MYNAME=`basename $0`
MYDIR=`dirname $0`
cd $MYDIR
MYDIR=`pwd`


SPEECH_SH=${MYDIR}/speech.sh
SPEECH_TXT=${HOME}/speech.txt
SPEECH_STOP_FILE=${HOME}/stop_speech
SPEECH_INTERVAL=120

##### main
while true; do
    if [ ! -f ${SPEECH_STOP_FILE} ]; then
	cat ${SPEECH_TXT} | ${SPEECH_SH} ${SPEECH_STOP_FILE}
    fi

    if [ -f ${SPEECH_STOP_FILE} ]; then
	sleep 2
    else
	sleep ${SPEECH_INTERVAL}
    fi
done
