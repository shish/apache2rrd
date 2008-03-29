#!/usr/bin/python

import rrdtool
import os
import time
import os.path
import sys
import gzip

class ApacheToRRD:
    def __init__(self, rrd):
        self.clear()
        self.last_flush = None
        self.last_date = None
        self.last_date_text = None
        self.rrd = rrd

    def init_rrd(self):
        if not os.path.exists(self.rrd):
            rrdtool.create(self.rrd,
                    '--step', '300',
                    '--start', str(self.last_flush-1),
                    'DS:gecko:GAUGE:600:0:U',
                    'DS:opera:GAUGE:600:0:U',
                    'DS:msie:GAUGE:600:0:U',
                    'DS:bots:GAUGE:600:0:U',
                    'DS:other:GAUGE:600:0:U',
                    'DS:bandwidth:GAUGE:600:0:U',
                    'RRA:AVERAGE:0.5:1:300',
                    'RRA:AVERAGE:0.5:6:384',
                    'RRA:AVERAGE:0.5:24:384',
                    'RRA:AVERAGE:0.5:288:2400'
                    )

    def flush(self):
        #print "Update at "+str(seconds)
        rrdtool.update(self.rrd,
                '-t', 'gecko:opera:msie:bots:other:bandwidth',
                '%d:%d:%d:%d:%d:%d:%d' % (
                        self.last_flush,
                        self.gecko, self.opera, self.msie, self.bots, self.other,
                        self.bandwidth)
        )
        self.clear()
        self.last_flush = self.last_flush + 300

    def clear(self):
        self.gecko = 0
        self.opera = 0
        self.msie = 0
        self.bots = 0
        self.other = 0
        self.bandwidth = 0

    def parse_log(self, filename):
        print "Reading "+filename+"..."

        if filename[-3:] == ".gz":
            fopen = gzip.open
        else:
            fopen = open

        # check the file looks ok
        if not self.last_flush:
            line = fopen(filename).readline()
            (ip, host, user, date, offset, method, url, http, status, size, referrer, agent) = line.split(" ", 11)
            self.last_flush = self.parse_date(date)
            self.init_rrd()

        # do the bulk of the parsing
        n = 0
        for line in fopen(filename):
            try:
                n = n + 1
                if n % 10000 == 0:
                    print "Line "+str(n)+"\r",
                    sys.stdout.flush()
                (ip, host, user, date, offset, method, url, http, status, size, referrer, agent) = line.split(" ", 11)
                current_timestamp = self.parse_date(date)

                while current_timestamp >= self.last_flush + 300:
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

                if size != "-":
                    self.bandwidth = self.bandwidth + int(size)
            except KeyboardInterrupt, ke:
                raise ke
            except Exception, e:
                print "Error with line:\n"+line+"\nError is:\n"+str(e)

        self.flush()

    def parse_date(self, date):
        (date, hour, minute, second) = date.split(":")
        if date != self.last_date_text:
            self.last_date = int(time.mktime(time.strptime(date, "[%d/%b/%Y")))
            self.last_date_text = date
        return self.last_date + int(hour)*60*60 + int(minute)*60 + int(second)

    def length_to_t(self, length):
        if length == "day":
            t = "-1d"
        if length == "week":
            t = "-1w"
        if length == "month":
            t = "-1m"
        if length == "year":
            t = "-1y"
        return t

    def output_browsers(self, filename, length="month"):
        t = self.length_to_t(length)

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
        "CDEF:gecko=sgecko,5,/", # values per minute
        "CDEF:opera=sopera,5,/",
        "CDEF:msie=smsie,5,/",
        "CDEF:bots=sbots,5,/",
        "CDEF:other=sother,5,/",
        "CDEF:total=gecko,opera,+,msie,+",
        "AREA:total#666666:Total",
        "LINE1:gecko#FFAA00:Gecko",
        "LINE1:opera#00AA00:Opera",
        "LINE1:msie#00AAFF:MSIE ",
        "LINE1:bots#CCCCCC:Bots ",
        "LINE1:other#888888:Other"
        )

    def output_bandwidth(self, filename, length="month"):
        t = self.length_to_t(length)

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
        "DEF:sbandwidth="+self.rrd+":bandwidth:AVERAGE", # total for 5 mins
        "CDEF:bandwidth=sbandwidth,300,/", # values per second
        "AREA:bandwidth#666666:Bandwidth"
        )

def getMAL(series, units):
    return \
        "GPRINT:"+series+":AVERAGE:'%7.2lf"+units+"' "+\
        "GPRINT:"+series+":MIN:'%7.2lf"+units+"' "+\
        "GPRINT:"+series+":MAX:'%7.2lf"+units+"' "+\
        "GPRINT:"+series+":LAST:'%7.2lf"+units+"\\n' "

if __name__ == "__main__":
    a2r = ApacheToRRD("browsers.rrd")
    for arg in sys.argv[1:]:
        a2r.parse_log(arg)
    a2r.output_browsers("graph-day.png", "day")
    a2r.output_browsers("graph-week.png", "week")
    a2r.output_browsers("graph-month.png", "month")
    a2r.output_browsers("graph-year.png", "year")
    a2r.output_bandwidth("graph-bw-week.png", "week")

