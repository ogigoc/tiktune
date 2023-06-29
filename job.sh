#!/bin/bash
[ -z "$1" ] && { echo "Usage: $0 <device>"; exit 1; }

cd /home/tiktune/tiktune
source env/bin/activate
python main.py -d $1 2>&1 | tee -a logs.txt
