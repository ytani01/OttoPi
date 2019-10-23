#!/bin/sh -x
#
# (c) 2019 Yoichi Tanibayashi
#

PLAY_CMD="cvlc --loop --alsa-gain 0.4"
PKILL_WORD="vlc"
MUSIC_FILE="${HOME}/OttoPi/sound/carnival.mp3"
STOP_FILE="${HOME}/stop_music"

pkill ${PKILL_WORD}
sleep 1

while true; do
    if pgrep aplay; then
       sleep 2
       continue
    fi
       
    if [ -f ${STOP_FILE} ]; then
	echo "stop file: ${STOP_FILE}"
	pkill ${PKILL_WORD}
    else
	if ! pgrep ${PKILL_WORD}; then
	    sleep 1
	    nice -n 5 ${PLAY_CMD} ${MUSIC_FILE} &
	fi
    fi
    sleep 1
done