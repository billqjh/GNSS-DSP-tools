#!/bin/sh

DATA=$1
DEST_DIR=$2

# L1

<${DATA} packet2wav | ./acquire-gps-l1.py /dev/stdin 69984000 -9334875 >${DEST_DIR}/m-gps-l1.dat
<${DATA} packet2wav | ./acquire-glonass-l1.py /dev/stdin 69984000 17245125 >${DEST_DIR}/m-glonass-l1.dat
<${DATA} packet2wav | ./acquire-galileo-e1b.py /dev/stdin 69984000 -9334875 >${DEST_DIR}/m-galileo-e1b.dat
<${DATA} packet2wav | ./acquire-galileo-e1c.py /dev/stdin 69984000 -9334875 >${DEST_DIR}/m-galileo-e1c.dat
<${DATA} packet2wav | ./acquire-beidou-b1i.py /dev/stdin 69984000 -23656875 >${DEST_DIR}/m-beidou-b1i.dat

# L2

<${DATA} packet2wav 2 | ./acquire-gps-l2cm.py /dev/stdin 69984000 -127126 >${DEST_DIR}/m-gps-l2cm.dat
<${DATA} packet2wav 2 | ./acquire-glonass-l2.py /dev/stdin 69984000 18272874 >${DEST_DIR}/m-glonass-l2.dat
<${DATA} packet2wav 2 | ./acquire-glonass-l3i.py /dev/stdin 69984000 -25702126 >${DEST_DIR}/m-glonass-l3i.dat
<${DATA} packet2wav 2 | ./acquire-glonass-l3q.py /dev/stdin 69984000 -25702126 >${DEST_DIR}/m-glonass-l3q.dat
<${DATA} packet2wav 2 | ./acquire-galileo-e5bi.py /dev/stdin 69984000 -20587126 >${DEST_DIR}/m-galileo-e5bi.dat
<${DATA} packet2wav 2 | ./acquire-galileo-e5bq.py /dev/stdin 69984000 -20587126 >${DEST_DIR}/m-galileo-e5bq.dat
<${DATA} packet2wav 2 | ./acquire-beidou-b2i.py /dev/stdin 69984000 -20587126 >${DEST_DIR}/m-beidou-b2i.dat
