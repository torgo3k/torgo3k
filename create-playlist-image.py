#!/usr/bin/env python

NUM_HOURS_TO_LIST = 60
STATS_URL = 'http://localhost:8080/requests/status.xml'
PLAYLIST_URL = "http://localhost:8080/requests/playlist.xml"

CONVERT_EXEC = "nice -n10 /usr/bin/convert"

LINE_DIMENSIONS = '500x28'
BACKGROUND_COLOR = 'black'
FOREGROUND_COLOR = 'white'
FONT_REGULAR = "Droid-Sans-Regular" # run "identify -list font" from the command line
FONT_BOLD = "Droid-Sans-Bold" # run "identify -list font" from the command line
POINTSIZE = '14'

import os
import shutil
import sys
import time
import urllib

from xml.dom import minidom

try:
	output_file = sys.argv[1]
except IndexError:
	print "Usage: create-playlist-image.py output-image-filename"
	sys.exit(0)

# lifted from python's minidom examples...
def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

# FIXME: this is inefficient and not very flexible.
# maybe use html -> html2ps -> imagemagick convert ps->gif?
def addLine(font, str):
    #print str
    LEFT_SPACER = '   '
    os.system( CONVERT_EXEC+' -append playlist.mpc blankline.mpc playlist.mpc' )
    cmd = CONVERT_EXEC + ' playlist.mpc -gravity "SouthWest" -fill '+FOREGROUND_COLOR+' -font "'+font+'"  -pointsize '+POINTSIZE+' -draw \'text 0,3 "'
    cmd += LEFT_SPACER + str
    cmd += '"\' playlist.mpc'
    os.system( cmd )

# get info from the vlc server
stats = minidom.parse(urllib.urlopen(STATS_URL))
time_in_current_file = int(getText(stats.getElementsByTagName("time")[0].childNodes))
playlist = minidom.parse(urllib.urlopen(PLAYLIST_URL))

# parse the playlist into an array of titles & lengths
names = [ ]
lengths = [ ]
i = 0
current_index = 0
for node in playlist.getElementsByTagName( "node" ):
	for node2 in node.getElementsByTagName( "node" ):
		if node2.attributes["name"].value == 'Playlist':
			for leaf in node2.getElementsByTagName( "leaf" ):
				try:
					if leaf.attributes["current"].value == "current":
						current_index = i
				except:
					pass
				names.append( leaf.attributes["name"].value )
				lengths.append( int(leaf.attributes["duration"].value)/1000000 )
				i = i + 1

# decide which time range to display
now = time.time()
start_time = now - time_in_current_file
end_time = start_time + (NUM_HOURS_TO_LIST * 60 * 60)

# loop through the episodes until we reach end_time
current_day = -1
upcoming = [ ]
i = current_index
starts_at = start_time
ends_at = starts_at + lengths[i]
upcoming.append( [ names[i], starts_at ] )
while ends_at <= end_time:
	i = (i+1) % len(names)
	starts_at = ends_at
	upcoming.append( [ names[i], starts_at ] )
	ends_at = starts_at + lengths[i]


# now, making the upcoming file:
cmd = CONVERT_EXEC + ' -size '+LINE_DIMENSIONS+' xc:'+BACKGROUND_COLOR+' blankline.mpc'
#print cmd
os.system(cmd)
cmd ='cp bankline.mpc playlist.mpc'
#print cmd
os.system(cmd)

for episode in upcoming:
	name = episode[0].replace("'","`")
	secs = episode[1]

	ltime = time.localtime( secs )
	if current_day != ltime.tm_yday:
		current_day = ltime.tm_yday
		daystr = time.strftime( "%A, %B %d", ltime )
		addLine( FONT_REGULAR, '' )
		addLine( FONT_BOLD, daystr )

	timestr = time.strftime( '%I:%M %p', ltime )
	addLine( FONT_REGULAR, '    ' + timestr + '   ' + name )

addLine( FONT_REGULAR, '' )
os.system( CONVERT_EXEC + ' playlist.mpc ' + output_file )

# clean up the temp files
try:
	os.remove('blankline.mpc')
	os.remove('blankline.cache')
	os.remove('playlist.mpc')
	os.remove('playlist.cache')
except:
	pass
