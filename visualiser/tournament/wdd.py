# Diplomacy Tournament Visualiser
# Copyright (C) 2014 Chris Brand
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urllib2
from HTMLParser import HTMLParser

from tournament.models import *

# So far, this parses out the tournament positions
# It populates results[1] with a list of 1st place (date string, name) tuples,
# and results[2] and [3] with similar lists for 2nd and 3rd place finishes.
# TODO parse http://world-diplomacy-database.com/php/results/player_fiche16.php?id_player=9638
# to extract solos and board tops by country.
class WDDParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_th_tag = False
        self.found_map = False
        self.current_ranking = 0
        self.column = 0
    def handle_starttag(self, tag, attrs):
        print "Start tag:", tag
        if tag == 'th':
            self.in_th_tag = True
        elif tag == 'map':
            self.found_map = True
        elif tag == 'tr':
            self.column = 0
        elif tag == 'td':
            self.column += 1
    def handle_endtag(self, tag):
        print "End tag:", tag
        if tag == 'th':
            self.in_th_tag = False
        elif tag == 'tr':
            self.column = 0
    def handle_data(self, data):
        # Not interested in the header stuff
        if not self.found_map:
            return
        if self.in_th_tag:
            print "TH tag data:", data
            # Need to be smarter here - find start of "Best performances in tournament",
            # and start of "Best performances in circuit", and only parse between the two
            if data == '1st':
                if 1 not in results:
                    self.current_ranking = 1
                    results[self.current_ranking] = []
            elif data == '2nd':
                if 2 not in results:
                    self.current_ranking = 2
                    results[self.current_ranking] = []
            elif data == '3rd':
                if 3 not in results:
                    self.current_ranking = 3
                    results[self.current_ranking] = []
            else:
                self.current_ranking = 0
            print "Ranking:", self.current_ranking
        if self.current_ranking > 0:
            if self.column == 1:
                self.date = data
            elif self.column == 3:
                results[self.current_ranking].append((self.date, data))
                print "Column 3:", data
                print results

parser = WDDParser()

try:
    website = urllib2.urlopen(address)
except urllib2.HTTPError, e:
    print "Cannot retrieve URL: HTTP Error Code", e.code
except urllib2.URLError, e:
    print "Cannot retrieve URL: HTTP Error Code", e.reason[1]
website_html = website.read()
website.close()
if website.geturl() != address:
   # We were redirected
   pass
results = {}
parser.feed(website_html)
