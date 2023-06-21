#!/bin/bash

JSON_FILE=videos_db.json
DATA_FILE=data.dat

# Parse JSON and generate a data file
jq -r '.time[0:10]' $JSON_FILE | uniq -c | tail -n 7 > $DATA_FILE

# Convert data to the right format for gnuplot
awk '{print $2, $1}' $DATA_FILE > tmp.plot.tmp && mv tmp.plot.tmp $DATA_FILE

# Get terminal size
width=$(tput cols)
height=$(tput lines)

# Use gnuplot to generate a bar chart
gnuplot -p << EOF
set terminal dumb size $width,$height
set timefmt "%Y-%m-%d"
set xdata time
set format x "%Y-%m-%d"
set style fill solid
set boxwidth 0.5
set xlabel "Date"
set ylabel "Videos"
set title "Number of videos by date"
set lmargin at screen 0.1
set rmargin at screen 0.9
plot '$DATA_FILE' using 1:2 with boxes title 'Videos'
EOF
