#!/usr/bin/env bash

for i in {1..48}
do
   python Hurricane_master.py -t $i -v True
done

ffmpeg -r 12 -i ./output/%05d.png  demo.mp4