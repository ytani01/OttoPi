#!/bin/sh -x
#
# (c) 2019 Yoichi Tanibayashi
#

SPEECH_TXT=${HOME}/OttoPi/speech.txt
STOP_FILE=${HOME}/speech_stop

while true; do
    if [ -f ${STOP_FILE} ]; then
	echo "stop file: ${STOP_FILE}"
    else
	cat $SPEECH_TXT | speech.sh ${STOP_FILE}
    fi
    sleep 1
done
