#!/bin/sh
#
# (c) 2019 Yoichi Tanibayashi
#
LOGDIR=${HOME}/tmp

PKGS="pigpio vlc python3-pip python3-venv"

CMDS="boot.sh"
CMDS="${CMDS} MyLogger.py OttoPiAuto.py OttoPiClient.py"
CMDS="${CMDS} OttoPiConfig.py OttoPiCtrl.py"
CMDS="${CMDS} OttoPiHttpServer.py templates static"
CMDS="${CMDS} OttoPiMotion.py OttoPiServer.py PiServo.py RobotButton.py"
CMDS="${CMDS} OttoPiWebsockServer.py OttoPiBleServer.py BlePeripheral.py"
CMDS="${CMDS} VL53L0X.py vl53l0x_python.so"
CMDS="${CMDS} loop.sh speech.sh speech.txt music.sh speakipaddr2.sh"
CMDS="${CMDS} activate-do.sh"

#
# functions
#
usage () {
    echo
    echo "    usage: ${MYNAME}"
    echo
}

ts_echo () {
    DATESTR=`date +'%Y/%m/%d(%a) %H:%M:%S'`
    echo "* ${DATESTR}> $*"
}

ts_echo_do () {
    ts_echo $*
    $*
    if [ $? -ne 0 ]; then
        ts_echo "ERROR: ${MYNAME}: failed"
        exit 1
    fi
}

#
# main
#
MYNAME=`basename $0`
ts_echo "MYNAME=${MYNAME}"

MYDIR=`dirname $0`
ts_echo "MYDIR=${MYDIR}"

cd ${MYDIR}
BASEDIR=`pwd`
ts_echo "BASEDIR=${BASEDIR}"

cd ..
VENVDIR=`pwd`
ts_echo "VENVDIR=${VENVDIR}"

BINDIR="${VENVDIR}/bin"
ts_echo "BINDIR=${BINDIR}"

#
# check venv and activate it
#
if [ -z "${VIRTUAL_ENV}" ]; then
    ACTIVATE="${BINDIR}/activate"
    ts_echo "ACTIVATE=${ACTIVATE}"

    if [ ! -f ${ACTIVATE} ]; then
        ts_echo "ERROR: ${ACTIVATE}: no such file"
        exit 1
    fi
    . ${ACTIVATE}
fi
if [ ${VIRTUAL_ENV} != ${VENVDIR} ]; then
    ts_echo "ERROR: VIRTUAL_ENV=${VIRTUAL_ENV} != VENVIDR=${VENVDIR}"
    exit 1
fi
ts_echo "VIRTUAL_ENV=${VIRTUAL_ENV}"

#
# make dirs
#
ts_echo "* mkdirs"
for d in ${LOGDIR}; do
    d1=${d}
    if [ ! -d ${d1} ]; then
        mkdir -pv $d1
    fi
done

#
# install packages
#
ts_echo "* install packages"
ts_echo_do sudo apt install -y ${PKGS}
ts_echo_do sudo apt autoremove -y

#
# update pip3
#
ts_echo_do python3 -m pip install -U pip
hash -r
pip -V

#
# install python packages
#
ts_echo "* install python packages"
ts_echo_do pip install -r ${BASEDIR}/requirements.txt

#
# copy OttoPi.conf
#
if [ ! -f ${HOME}/OttoPi.conf ]; then
    ts_echo "* make default config file: ${HOME}/OttoPi.conf"
    cp -v ${BASEDIR}/OttoPi.conf-sample ${HOME}/OttoPi.conf
fi

#
# crontab
#
#crontab -l > ${HOME}/crontab.bak
#crontab ${BASEDIR}/crontab.sample

#
# audio settings
#
ts_echo "* audio settings"
ts_echo_do amixer set -i PCM 97%

#
# setup sepak
#
ts_echo "* setup speak system"
cd ${VENVDIR}
if [ -d speak ]; then
    ts_echo "speak: directory already exists"
else
    ts_echo_do git clone git@github.com:ytani01/speak.git
fi

SPEAK_SETUP="${VENVDIR}/speak/setup-venv.sh"
if [ ! -x ${SPEAK_SETUP} ]; then
    ts_echo "${SPEAK_SETUP}: no such file"
    exit 1
fi
ts_echo "* execute ${SPEAK_SETUP}"
${SPEAK_SETUP}

#
# copy sound files
#
ts_echo "* copy sound files"
cd ${BASEDIR}
cp -rfv sound ${HOME}

#
# create symbolic links
#
ts_echo "* create symbolic links on ${BINDIR}"
cd ${BINDIR}
ln -sfv ${BASEDIR}/*.py .
for cmd in ${CMDS}; do
    ln -sfv ${BASEDIR}/${cmd} .
done
