#!/bin/sh
#
# (c) 2019 Yoichi Tanibayashi
#
MYNAME=`basename $0`
MYDIR=`dirname $0`
echo "MYNAME=${MYNAME}"
echo "MYDIR=${MYDIR}"

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
# init
#

cd ${MYDIR}
BASEDIR=`pwd`
echo "BASEDIR=${BASEDIR}"

cd ..
ENVDIR=`pwd`
if [ ! -f bin/activate ]; then
    echo "${ENVDIR}: invalid venv directory"
    exit 1
fi
echo "ENVDIR=${ENVDIR}"

BINDIR="${ENVDIR}/bin"
echo "BINDIR=${BINDIR}"

#
# main
#

#
# activate Python venv
#
echo "* activate venv"
. ${BINDIR}/activate

#
# make dirs
#
echo "* mkdirs"
for d in ${LOGDIR}; do
    d1=${d}
    if [ ! -d ${d1} ]; then
        mkdir -pv $d1
    fi
done

#
# install packages
#
echo "* install packages"
sudo apt install -y ${PKGS}
if [ $? != 0 ]; then
    exit 1
fi
sudo apt autoremove -y
if [ $? != 0 ]; then
    exit 1
fi

#
# update pip3
#
echo "* update pip command"
python3 -m pip install -U pip
if [ $? != 0 ]; then
    exit 1
fi
hash -r
pip -V

#
# install python packages
#
echo "* install python packages"
pip install -r ${BASEDIR}/requirements.txt
if [ $? != 0 ]; then
    exit 1
fi

#
# copy OttoPi.conf
#
if [ ! -f ${HOME}/OttoPi.conf ]; then
    echo "* make default config file: ${HOME}/OttoPi.conf"
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
echo "* audio settings"
amixer set -i PCM 97%

#
# setup sepak
#
echo "* setup speak system"
cd ${ENVDIR}
git clone git@github.com:ytani01/speak.git
SPEAK_SETUP="${ENVDIR}/speak/setup-venv.sh"
if [ ! -x ${SPEAK_SETUP} ]; then
    echo "${SPEAK_SETUP}: no such file"
    exit 1
fi
echo "* execute ${SPEAK_SETUP}"
${SPEAK_SETUP}

#
# copy sound files
#
echo "* copy sound files"
cd ${BASEDIR}
cp -rfv sound ${HOME}

#
# create symbolic links
#
echo "* create symbolic links on ${BINDIR}"
cd ${BINDIR}
ln -sfv ${BASEDIR}/*.py .
for cmd in ${CMDS}; do
    ln -sfv ${BASEDIR}/${cmd} .
done
