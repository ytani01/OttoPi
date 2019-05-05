#!/bin/sh

P1=22
P2=27
P3=17
P4=4

move() {
    pigs s $P1 $1 s $P2 $2 s $P3 $3 s $P4 $4 mils 500
}

reset() {
    move 1500 1500 1500 1500
    move 0 0 0 0
}

#####
reset
