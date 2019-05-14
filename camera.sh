#!/bin/sh

TIME_SEC=100
TIMELAPS_SEC=2
WIDTH=1024
HEIGHT=768

CAMERA_CMD="raspistill \
-t ${TIME_SEC}000 \
-tl ${TIMELAPS_SEC}000 \
-w ${WIDTH} -h ${HEIGHT} \
-vs -vf \
-o img%05d.jpg"

exec $CAMERA_CMD
