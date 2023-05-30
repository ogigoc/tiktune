#!/bin/bash
[ -z "$1" ] && { echo "Usage: $0 <device>"; exit 1; }

cd /home/ognjen/Projects/tiktok-promo
source env/bin/activate
python scroll.py -d $1 2>&1 -a all -m 30 | tee -a logs.txt
