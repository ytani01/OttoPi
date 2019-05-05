#!/bin/sh

P1=22
P2=27
P3=17
P4=4

move() {
    pigs s $P1 $1 s $P2 $2 s $P3 $3 s $P4 $4 mils $5
}

reset() {
    move 1500 1500 1500 1500 500
    move 0 0 0 0 500
}

#####
reset

while true; do
    move 1300 1500 1500 1300 200
    move 1500 1300 1300 1500 200
    move 1300 1500 1300 1500 200
    move 1700 1500 1500 1700 200
    move 1500 1700 1700 1500 200
    move 1700 1500 1700 1500 200
    reset
done
