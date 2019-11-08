#!/bin/sh

echo A
sleep 5 &
echo B
sleep 10 &
echo C

wait
echo Z
