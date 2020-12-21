#!/bin/python
import feedgen
from feedgen.feed import FeedGenerator
import urllib3
import sys
import datetime
import pytz
import os
import eyed3
import html

http = urllib3.PoolManager()

good_count = 0
max_download = 999999
chunk_size=128*1024

years = range(2017,2020+1)
months = range(1,12+1)
days = range(1,31+1)
# tz=pytz.timezone('US/Pacific')
tz=pytz.utc

# Feed updates up to "3 days ago" so we aren't too aggressive.
now = datetime.datetime.now(tz)
dl_now = now - datetime.timedelta(days=2)

for year in years:
  for month in months:
    for day in days:
      try:
        dt = datetime.datetime(year,month,day,tzinfo=tz)
      except:
        print("SKIP D/L: BAD DATE ", year, month, day, tz)
        pass
      if dt > dl_now:
        print("SKIP Future: ", dt)
        continue
      vars = {'year': year, 'month':month, 'day':day}
      cachefile = "cache/{year:04d}_{month:02d}_{day:02d}".format(**vars)
      if os.path.exists(cachefile):
        print("SKIP D/L Cached: {year} {month} {day} ".format(**vars))
        continue
      if good_count >= max_download:
        print("SKIP MAX COUNT: {year} {month} {day} ".format(**vars))
        break
      url = "https://download.stream.publicradio.org/livefromhere/{year:04d}/{month:02d}/{day:02d}/lfh_{year:04d}{month:02d}{day:02d}.mp3".format(**vars)
      r = http.request('HEAD', url)

      if r.status == 404:
        f = open(cachefile,"w")
        f.write(str(r.status))
        f.close()
        print(url + " = " + str(r.status))
        continue

      try:
        download = http.request('GET', url, preload_content=False, retries=True, redirect=True)
      except:
        print("FAILED DOWNLOAD:",url)
        continue
      print("Downloading... " + url)
      with open(cachefile, 'wb') as out:
        for chunk in download.stream(chunk_size):
          out.write(chunk)
      download.release_conn()
      print("done!")
      good_count += 1

fg = FeedGenerator()
fg.load_extension('podcast')
fg.title("Live From Here (Unofficial Full Episode Feed)")
fg.link(href="https://raw.githubusercontent.com/slacy/lfhrss/master/lfh.rss", rel='self')
fg.description("Live From Here (Unofficial Full Episode Feed)")
fg.image('https://raw.githubusercontent.com/slacy/lfhrss/master/lfh.png', width=400, height=400)
fg.logo('https://raw.githubusercontent.com/slacy/lfhrss/master/lfh_450.png')
fg.icon('https://raw.githubusercontent.com/slacy/lfhrss/master/lfh.png')
fg.podcast.itunes_image('https://raw.githubusercontent.com/slacy/lfhrss/master/lfh.png')
fg.podcast.itunes_explicit("no")

for year in years:
  for month in months:
    for day in days:
      vars = {'year': year, 'month':month, 'day':day}
      url = "https://download.stream.publicradio.org/livefromhere/{year:04d}/{month:02d}/{day:02d}/lfh_{year:04d}{month:02d}{day:02d}.mp3".format(**vars)
      cachefile = "cache/{year:04d}_{month:02d}_{day:02d}".format(**vars)
      if not os.path.exists(cachefile):
        continue
      s = os.path.getsize(cachefile)
      if s < 1000:
        print("SKIP Too small: ", cachefile)
        continue

      audiofile = eyed3.load(cachefile)
      artist = audiofile.tag.artist.encode('latin1').decode('utf-8')
      album = audiofile.tag.album.encode('latin1').decode('utf-8')
      title = audiofile.tag.title.encode('latin1').decode('utf-8')

      try:
        dt = datetime.datetime(year,month,day,tzinfo=tz)
      except:
        print( "SKIP BAD DATE", year, month, day, tz)
        continue
      if dt > now:
        print("SKIP Future:", dt)
        continue
      fe = fg.add_entry()
      fe.id(url)
      fe.title(title)
      fe.description(artist + " / " + album + " / " + title)
      fe.pubDate(dt)
      fe.enclosure(url, str(os.path.getsize(cachefile)), 'audio/mpeg')
      fe.guid(guid=url, permalink=True)
      print(url)

# fg.atom_file('lfh.atom')
fg.rss_file('lfh.rss', pretty=True)
