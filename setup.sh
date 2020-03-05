#!/bin/sh -x
#
# (c) 2019 Yoichi Tanibayashi
#
BINDIR=${HOME}/bin
TOPDIR=${HOME}/OttoPi

DIRS="bin etc tmp work"

CONFFILENAME=OttoPi.conf

CMDS="MyLogger.py OttoPiWsServer.py OttoPiAuto.py OttoPiClient.py"
CMDS="${CMDS} OttoPiConfig.py OttoPiCtrl.py OttoPiHttpServer.py"
CMDS="${CMDS} OttoPiMotion.py OttoPiServer.py PiServo.py RobotButton.py"
CMDS="${CMDS} VL53L0X.py vl53l0x_python.so speech.sh boot.sh loop.sh music.sh"

###

### make dirs
for d in ${DIRS}; do
    d1 = "${HOME}/${d}"
    if [ ! -d ${d1} ]; then
        mkdir $d1
    fi
done

### setup sepak
cd ${HOME}
git clone git@github.com:ytani01/speak.git

cd ${HOME}/speak
./setup.sh

### update pip3
pip3 install -U pip
hash -r

### install python packages
cd ${TOPDIR}
sudo pip3 install -r requirements.txt

### OttoPi.conf
if [ ! -f ${HOME}/OttoPi.conf ]; then
	cp ${TOPDIR}/OttoPi.conf-sample ${HOME}/OttoPi.conf
fi

### copy commands
cd ${BINDIR}
for cmd in ${CMDS}; do
	rm -f ${BINDIR}/${cmd}
	ln -sf ${TOPDIR}/${cmd} .
done

### copy config file
if [ ! -f ${HOME}/${CONFFILENAME} ]; then
    cp ${TOPDIR}/${CONFFILENAME} ${HOME}
fi

### audio settings
amixer set -i PCM 97%

### crontab
crontab -l > ${HOME}/crontab.bak
crontab ${TOPDIR}/crontab.sample
