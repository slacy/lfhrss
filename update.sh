#!/bin/bash
cd /home/slacy/LFH
source env/bin/activate
git pull origin master
python ./lfh_feed.py
git add -u
git commit -m "Feed update $(date)"
git push origin master
