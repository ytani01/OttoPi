#!/bin/sh -x

s1=4
s2=17
wt=450
while true; do
	for a in 500 2500 1500; do
		pigs s $s1 $a s $s2 $a mils $wt
#		sleep 1
	done
done
