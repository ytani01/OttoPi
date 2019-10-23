#!/bin/sh
#
# (c) 2019 Yoichi Tanibayashi
#

ROBOTDIR=${HOME}/OttoPi

SPEECH_SH=${ROBOTDIR}/speech.sh
SPEECH_TXT=${ROBOTDIR}/speech.txt
SPEECH_STOP_FILE=${HOME}/stop_speech
SPEECH_INTERVAL=60

MUSIC_SH=${ROBOTDIR}/music.sh
MUSIC_FILE=${ROBOTDIR}/carnival.mp3
MUSIC_STOP_FILE=${HOME}/stop_music

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
