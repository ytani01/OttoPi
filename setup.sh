#!/bin/sh -x
#
# (c) 2019 Yoichi Tanibayashi
#
BINDIR=${HOME}/bin
TOPDIR=${HOME}/OttoPi

CMDS="MyLogger.py OttoPiAuto.py OttoPiClient.py OttoPiConfig.py OttoPiCtrl.py OttoPiHttpServer.py OttoPiMotion.py OttoPiServer.py PiServo.py RobotButton.py VL53L0X.py vl53l0x_python.so speech.sh loop.sh boot.sh"

pip3 install -U pip
hash -r

cd ${TOPDIR}
sudo pip3 install -r requirements.txt

### OttoPi.conf
if [ ! -f ${BINDIR}/OttoPi.conf ]; then
	cp ${TOPDIR}/OttoPi.conf-sample ${BINDIR}/OttoPi.conf
fi

### copy commands
cd ${BINDIR}
for cmd in ${CMDS}; do
	rm -f ${BINDIR}/${cmd}
	ln -sf ${TOPDIR}/${cmd} .
done
