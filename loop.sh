#!/bin/sh
#
# (c) 2020 Yoichi Tanibayashi
#

SPEECH_SH=speech.sh
SPEECH_TXT=speech.txt
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
