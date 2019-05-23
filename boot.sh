#!/bin/sh
#
# Sample boot.sh
#
# (c) Yoichi Tanibayashi
#
##### crontab sample ################################################
# PIN_LED=20
# PIN_SW=21
# PIN_VCC=26
# PIN_AUDIO1=12
# PIN_AUDIO2=13
# PIN_SERVO1=17
# PIN_SERVO2=27
# PIN_SERVO3=22
# PIN_SERVO4=23
# @reboot         sudo pigpiod
# @reboot         sleep 5; pigs m ${PIN_AUDIO1} 0 m ${PIN_AUDIO2} 0
# @reboot         sleep 6; pigs s ${PIN_SERVO1} 0 s ${PIN_SERVO2} 0
# @reboot         sleep 7; pigs s ${PIN_SERVO3} 0 s ${PIN_SERVO4} 0
# @reboot         ${HOME}/bin/boot.sh > ${HOME}/tmp/boot.log 2>&1 &
#####################################################################

BINDIR=${HOME}/bin
LOGDIR=${HOME}/tmp

PATH=${BINDIR}:${PATH}

MY_NAME="オットー・パイ"

SPEAK=OFF
SPEAK_SERVER="SpeakServer.py"
SPEAK_LOG="${LOGDIR}/speak.log"

#SPEAK_CMD="Speak.py"
#SPEAK_CMD="speak"
SPEAK_CMD="SpeakClient.py"
#SPEAK_CMD="speak2.sh"

SPEAKIPADDR_CMD="speakipaddr2.sh"

ROBOT_SERVER="${BINDIR}/OttoPiServer.py"
ROBOT_OPT=""
#ROBOT_OPT="-d"
ROBOT_LOG="${LOGDIR}/robot.log"

HTTP_SERVER="${BINDIR}/OttoPiHttpServer.py"
#HTTP_OPT=""
HTTP_OPT="-d"
HTTP_LOG="${LOGDIR}/http.log"

ROBOT_CLIENT="${BINDIR}/OttoPiClient.py"

MJPG_STREAMER="${BINDIR}/mjpg-streamer.sh"
MJPG_STREAMER_LOG="${LOGDIR}/mjpg-streamer.log"

if which ${SPEAK_SERVER}; then
    SPEAK=ON
    if [ -f ${SPEAK_LOG} ]; then
	mv ${SPEAK_LOG} ${SPEAK_LOG}.1
    fi
    ${SPEAK_SERVER} -d > ${SPEAK_LOG} 2>&1 &
    sleep 10
    #${SPEAK_CMD} "私は二足歩行ロボット"
    ${SPEAK_CMD} "私は二そくほこうロボット"
    ${SPEAK_CMD} "${MY_NAME} です"
fi

if [ -x ${ROBOT_SERVER} ]; then
    if [ ${SPEAK} = ON ]; then
	${SPEAK_CMD} "ロボット制御システムを起動します" &
    fi
    if [ -f ${ROBOT_LOG} ]; then
	mv ${ROBOT_LOG} ${ROBOT_LOG}.1
    fi
    cd ${BINDIR}
    ${ROBOT_SERVER} ${ROBOT_OPT} > ${ROBOT_LOG} 2>&1 &
    sleep 10
fi

if [ -x ${MJPG_STREAMER} ]; then
    ${MJPG_STREAMER} > ${MJPG_STREAMER_LOG} 2>&1 &
fi

if [ -x ${HTTP_SERVER} ]; then
    if [ ${SPEAK} = ON ]; then
	${SPEAK_CMD} "ウェブインターフェースを 起動します" &
    fi
    if [ -f ${HTTP_LOG} ]; then
	mv ${HTTP_LOG} ${HTTP_LOG}.1
    fi
    cd ${BINDIR}
    ${HTTP_SERVER} ${HTTP_OPT} > ${HTTP_LOG} 2>&1 &
    sleep 10 
fi

if [ ${SPEAK} = ON ]; then
    if which ${SPEAKIPADDR_CMD}; then
	${SPEAKIPADDR_CMD} repeat &
    fi
fi

sleep 10
${ROBOT_CLIENT} -d -c ':happy'
