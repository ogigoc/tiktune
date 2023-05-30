#!/bin/bash
[ -z "$1" ] && { echo "Usage: $0 <device>"; exit 1; }

cd /home/ognjen/Projects/tiktok-promo
source env/bin/activate
python create_gmail.py -d $1 2>&1 | tee -a logs.txt
