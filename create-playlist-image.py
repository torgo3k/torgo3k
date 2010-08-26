#!/usr/bin/env python

import os
import shutil
import sys
import time
import urllib
from xml.dom import minidom

TMPFILE = '/tmp/upcoming.html'
NUM_HOURS_TO_LIST = 60
STATS_URL = 'http://localhost:8080/requests/status.xml'
PLAYLIST_URL = "http://localhost:8080/requests/playlist.xml"

try:
    output_file = sys.argv[1]
except IndexError:
    print "Usage: create-playlist-image.py output.png"
    sys.exit(0)

# lifted from python's minidom examples...
def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

# get info from the vlc server
stats = minidom.parse(urllib.urlopen(STATS_URL))
time_in_current_file = int(getText(stats.getElementsByTagName("time")[0].childNodes))
playlist = minidom.parse(urllib.urlopen(PLAYLIST_URL))

# parse the playlist into an array of titles & lengths
names = [ ]
lengths = [ ]
i = 0
current_index = 0
for node in playlist.getElementsByTagName("node"):
    for node2 in node.getElementsByTagName("node"):
        if node2.attributes["name"].value == 'Playlist':
            for leaf in node2.getElementsByTagName("leaf"):
                try:
                    if leaf.attributes["current"].value == "current":
                        current_index = i
                except:
                    pass
                names.append(leaf.attributes["name"].value)
                lengths.append(int(leaf.attributes["duration"].value)/1000000)
                i = i + 1

# decide which time range to display
now = time.time()
start_time = now - time_in_current_file
end_time = start_time + (NUM_HOURS_TO_LIST * 60 * 60)

# loop through the episodes until we reach end_time
upcoming = [ ]
i = current_index
starts_at = start_time
ends_at = starts_at + lengths[i]
upcoming.append([ names[i], starts_at ])
while ends_at <= end_time:
    i = (i+1) % len(names)
    starts_at = ends_at
    upcoming.append([ names[i], starts_at ])
    ends_at = starts_at + lengths[i]


# start building the HTML
have_table = False
text=[ '<html>\n',
       '<head>\n',
       '<style type="text/css">\n',
       '\tbody { color: white; background-color: black; font-family: Sans; font-size: 12px; }\n',
       '\ttable { padding-left: 20px; font-size: 12px; }\n', # indent the tables
       '\ttd { padding-right: 15px }\n', # internal cell spacing
       '\t.day { font-weight: bold }\n',
       '</style>\n',
       '</head>\n',
       '<body>\n',
       '<p><i>(If this image looks out-of-date, reload the page in your browser)</i></p>' ]

current_day = -1
for episode in upcoming:
    name = episode[0].replace("&","&amp;").replace(".avi","")
    secs = episode[1]

    ltime = time.localtime(secs)
    if current_day != ltime.tm_yday:
        if current_day != -1:
            text.append('</table>\n\n')
        current_day = ltime.tm_yday
        daystr = time.strftime("%A, %B %d", ltime)
        text.extend([ '<p><span class="day">', daystr, '</span></p>\n', '<table>\n' ])

    timestr = time.strftime('%I:%M %p', ltime)
    text.append('<tr>')
    text.extend(['<td>',timestr,'</td>'])
    ep = ''
    if len(name) > 6 and name[0] == 'S' and name[3] == 'E' and name[6] == ' ':
        ep = name[:6]
        name = name[6:]
        if name[:3] == ' - ':
            name = name[3:]
    text.extend(['<td>',ep,'</td>'])
    text.extend(['<td>',name,'</td>'])
    text.append('</tr>\n')

text.extend(['</table>\n','</body>\n','</html>\n'])
f = open(TMPFILE,'w+')
f.write(''.join(text))
f.close()
os.system(''.join(['CutyCapt --min-width=600 --url=file://',TMPFILE,' --out=',output_file]));
os.remove(TMPFILE)
