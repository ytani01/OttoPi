#!/bin/sh -x
#
# (c) 2019 Yoichi Tanibayashi
#
BINDIR=${HOME}/bin
TOPDIR=${HOME}/OttoPi

cd ${TOPDIR}
sudo pip3 install -r requirements.txt

### OttoPi.conf
if [ ! -f ${BINDIR}/OttoPi.conf ]; then
	cp ${TOPDIR}/OttoPi.conf-sample ${BINDIR}/OttoPi.conf
fi
