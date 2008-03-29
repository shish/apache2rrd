#!/usr/bin/python

import rrdtool
import os
import time
import os.path

#87.4.77.240 travmap.shishnet.org - [23/Mar/2008:00:00:00 +0000] "GET /map.php?lang=en&server=s3.travian.it&alliance=id%3A5099&caption=CRES&groupby=player&casen=on&azoom=on&format=png HTTP/1.1" 200 7205 "http://travian.ws/analyser.pl?s=it33&aid=5099" "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)"

class ApacheToRRD:
    def __init__(self, rrd):
        self.clear()
        self.last_flush = 0
        self.date_start = None
        self.rrd = rrd

    def init_rrd(self):
        if not os.path.exists(self.rrd):
            rrdtool.create(self.rrd,
                            '--step', '300',
                            '--start', str(self.date_start-1),
                            'DS:gecko:GAUGE:600:0:U',
                            'DS:opera:GAUGE:600:0:U',
                            'DS:msie:GAUGE:600:0:U',
                            'DS:bots:GAUGE:600:0:U',
                            'DS:other:GAUGE:600:0:U',
                            'RRA:AVERAGE:0.5:1:300',
                            'RRA:AVERAGE:0.5:6:384',
                            'RRA:AVERAGE:0.5:24:384',
                            'RRA:AVERAGE:0.5:288:2400'
                            )

    def flush(self):
        seconds = self.date_start + self.last_flush * 60
        print '%d:%d:%d:%d:%d:%d' % (seconds, self.gecko, self.opera, self.msie, self.bots, self.other)
        rrdtool.update(self.rrd,
                '-t', 'gecko:opera:msie:bots:other',
                '%d:%d:%d:%d:%d:%d' % (seconds, self.gecko, self.opera, self.msie, self.bots, self.other))
        self.clear()
        self.last_flush = self.last_flush + 5

    def clear(self):
        self.gecko = 0
        self.opera = 0
        self.msie = 0
        self.bots = 0
        self.other = 0

    def parse_log(self, filename):
        # check the file looks ok
        line = open(filename).readline()
        (ip, host, user, date, offset, method, url, http, status, size, referrer, agent) = line.split(" ", 11)
        (day, hour, minute, second) = date.split(":")
        self.date_start = self.parse_date(day)
        self.init_rrd()

        # do the bulk of the parsing
        for line in file(filename):
            (ip, host, user, date, offset, method, url, http, status, size, referrer, agent) = line.split(" ", 11)
            (day, hour, minute, second) = date.split(":")
            day_minute = int(hour) * 60 + int(minute)

            while day_minute >= self.last_flush + 5:
                self.flush()

            if agent.find("Gecko") >= 0:
                self.gecko = self.gecko + 1
            elif agent.find("Opera") >= 0:
                self.opera = self.opera + 1
            elif agent.find("Bot") >= 0:
                self.bots = self.bots + 1
            elif agent.find("MSIE") >= 0:
                self.msie = self.msie + 1
            else:
                self.other = self.other + 1

        self.flush()

    def parse_date(self, date):
        return int(time.mktime(time.strptime(date, "[%d/%b/%Y")))

    def output_browsers(self, filename, length="month"):
        if length == "day":
            t = "-1d"
        if length == "week":
            t = "-1w"
        if length == "month":
            t = "-1m"
        if length == "year":
            t = "-1y"

#       "--vertical 'Hits' --unit h",
#       "--rigid --upper-limit 30",
        rrdtool.graph(filename,
                '--start', t,
                '--width', "500", '--height', "150",
                '--imgformat', 'PNG',
                '--no-minor',
                '--units-length', "7",
        "--color", "ARROW#FFFFFF",
        "--color", "BACK#000000",
        "--color", "SHADEA#666666",
        "--color", "SHADEB#666666",
        "--color", "CANVAS#222222",
        "--color", "MGRID#888888",
        "--color", "GRID#444444",
        "--color", "FONT#FFFFFF",
        "DEF:sgecko="+self.rrd+":gecko:AVERAGE", # values per second
        "DEF:sopera="+self.rrd+":opera:AVERAGE",
        "DEF:smsie="+self.rrd+":msie:AVERAGE",
        "DEF:sbots="+self.rrd+":bots:AVERAGE",
        "DEF:sother="+self.rrd+":other:AVERAGE",
        "CDEF:gecko=sgecko,60,*", # values per minute
        "CDEF:opera=sopera,60,*",
        "CDEF:msie=smsie,60,*",
        "CDEF:bots=sbots,60,*",
        "CDEF:other=sother,60,*",
        "CDEF:total=gecko,opera,+,msie,+",
        "COMMENT:%12s%-14s%-14s%-14s%-14s" % (" ", "Average", "Min", "Max", "Current"),
        "AREA:total#666666:'Total'",
        "LINE1:gecko#FFAA00:'Gecko'",
        "LINE1:opera#00AA00:'Opera'",
        "LINE1:msie#00AAFF:'MSIE '",
        "LINE1:bots#CCCCCC:'Bots '",
        "LINE1:other#888888:'Other'"
        )

def getMAL(series, units):
    return \
        "GPRINT:"+series+":AVERAGE:'%7.2lf"+units+"' "+\
        "GPRINT:"+series+":MIN:'%7.2lf"+units+"' "+\
        "GPRINT:"+series+":MAX:'%7.2lf"+units+"' "+\
        "GPRINT:"+series+":LAST:'%7.2lf"+units+"\\n' "

a2r = ApacheToRRD("browsers.rrd")
#a2r.parse_log("access.log")
a2r.output_browsers("graph.png", "week")
#                system("rrdtool update "+self.rrd+" -t gecko:opera:msie:bots:other N:$gecko:$opera:$msie:$bots:$other");
