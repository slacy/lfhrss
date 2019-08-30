#!/bin/bash
cd /home/slacy/LFH
git pull origin master
python ./lfh_feed.py
git add -u
git commit -m "Feed update $(date)"
git push origin master
