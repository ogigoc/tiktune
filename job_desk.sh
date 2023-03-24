#!/bin/bash
cd /home/ognjen/Projects/tiktok-promo
source env/bin/activate
python main.py -c dance -d desk 2>&1 | tee -a logs.txt
