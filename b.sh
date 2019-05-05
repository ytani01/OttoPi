#!/bin/sh
. ./common.sh

reset
sleep 2

i=1500
d=20
s=10
while [ $i -ge 700 ]
do
echo $i
move $i $i $i $i $s
i=$(($i - $d))
done

while [ $i -le 2200 ]
do
echo $i
move $i $i $i $i $s
i=$(($i + $d))
done

while [ $i -ge 1500 ]
do
echo $i
move $i $i $i $i $s
i=$(($i - $d))
done
