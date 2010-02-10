#!/usr/bin/python

import rrdtool
import os
import time
import os.path
import sys
import gzip
import bz2
import getopt
import sys


class ApacheToRRD:
    """
    A class containing the functionality necessary to convert an
    apache log file to an RRD database
    """

    def __init__(self, rrd):
        self.__clear()
        self.last_flush = None
        self.last_date = None
        self.last_date_text = None
        self.rrd = rrd

    def __init_rrd(self):
        if not os.path.exists(self.rrd):
            rrdtool.create(self.rrd,
                    '--step', '300',
                    '--start', str(self.last_flush-1),
                    'DS:gecko:GAUGE:600:0:U',
                    'DS:opera:GAUGE:600:0:U',
                    'DS:webkit:GAUGE:600:0:U',
                    'DS:msie:GAUGE:600:0:U',
                    'DS:bots:GAUGE:600:0:U',
                    'DS:other:GAUGE:600:0:U',
                    'DS:bandwidth:GAUGE:600:0:U',
                    'RRA:AVERAGE:0.5:1:300',
                    'RRA:AVERAGE:0.5:6:384',
                    'RRA:AVERAGE:0.5:24:384',
                    'RRA:AVERAGE:0.5:288:2400'
                    )

    def __flush(self):
        #print "Update at "+str(seconds)
        try:
            rrdtool.update(self.rrd,
                '-t', 'gecko:opera:msie:webkit:bots:other:bandwidth',
                '%d:%d:%d:%d:%d:%d:%d:%d' % (
                    self.last_flush,
                    self.gecko, self.opera, self.msie,
                    self.webkit, self.bots, self.other,
                    self.bandwidth)
            )
        except:
            pass
        self.__clear()
        self.last_flush = self.last_flush + 300

    def __clear(self):
        self.gecko = 0
        self.opera = 0
        self.msie = 0
        self.bots = 0
        self.webkit = 0
        self.other = 0
        self.bandwidth = 0

    def parse_log(self, filename):
        print "Reading "+filename+"..."

        if filename[-3:] == ".gz":
            fopen = gzip.open
        elif filename[-4:] == ".bz2":
            fopen = bz2.BZ2File
        elif filename == "-":
            fopen = get_stdin
        else:
            fopen = open

        # check the file looks ok, and find the start time
        if not self.last_flush:
            line = fopen(filename).readline()
            (ip, host, user, date, offset, method, url, http, status, size, referrer, agent) = line.split(" ", 11)
            self.last_flush = self.parse_date(date)
            self.__init_rrd()

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
                    self.__flush()

                if agent.find("WebKit") >= 0:
                    self.webkit = self.webkit + 1
                elif agent.find("Opera") >= 0:
                    self.opera = self.opera + 1
                elif agent.find("Gecko") >= 0:
                    self.gecko = self.gecko + 1
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

        self.__flush()

    def parse_date(self, date):
        """
        Turn an apache formatted date into a unix timestamp.

        Caching the date here makes the script as a whole run 5x as fast
        """
        (date, hour, minute, second) = date.split(":")
        if date != self.last_date_text:
            print "New day: "+date[1:]
            self.last_date = int(time.mktime(time.strptime(date, "[%d/%b/%Y")))
            self.last_date_text = date
        return self.last_date + int(hour)*60*60 + int(minute)*60 + int(second)

    def __length_to_t(self, length):
        if length == "day":
            t = "-1d"
        if length == "week":
            t = "-1w"
        if length == "month":
            t = "-1m"
        if length == "year":
            t = "-1y"
        if length == "2year":
            t = "-2y"
        return t

    def output_browsers(self, filename, length="month"):
        t = self.__length_to_t(length)

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
        "DEF:swebkit="+self.rrd+":webkit:AVERAGE",
        "DEF:sbots="+self.rrd+":bots:AVERAGE",
        "DEF:sother="+self.rrd+":other:AVERAGE",
        "CDEF:gecko=sgecko,5,/", # values per minute
        "CDEF:opera=sopera,5,/",
        "CDEF:msie=smsie,5,/",
        "CDEF:webkit=swebkit,5,/",
        "CDEF:bots=sbots,5,/",
        "CDEF:other=sother,5,/",
        "CDEF:total=gecko,opera,+,msie,+",
        "AREA:total#666666:Total",
        "LINE1:gecko#FFAA00:Gecko",
        "LINE1:opera#00AA00:Opera",
        "LINE1:msie#00AAFF:MSIE ",
        "LINE1:webkit#FFAAFF:WebKit ",
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


def get_stdin(filename):
    # same API as open(filename)
    return sys.stdin


def usage():
    print """
Usage:
  a2r -r file.rrd [log file] [log file] [log file] [...]
  a2r -r file.rrd -b -t week -o bandwidth-week.png
  a2r -r file.rrd -u -t year -o useragent-year.png

  -r rrd file to use
     .gz and .bz2 are handled automatically
     for exteral commands, pipe and use "-" for stdin
  -o output file name
  -b output a bandwidth graph
  -u output a user-agent graph
  -t timescale (day, week, month, year)
  -h help
    """


def main():
    rrdfile = None
    output = None
    output_mode = None
    timescale = None

    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'r:o:but:h')
    except getopt.GetoptError, err:
        print str(err)
        usage()
        return 2

    for o, a in optlist:
        if o == "-r":
            rrdfile = a
        elif o == "-o":
            output = a
        elif o == "-b":
            output_mode = "bandwidth"
        elif o == "-u":
            output_mode = "browsers"
        elif o == "-t":
            timescale = a
        elif o == "-h":
            usage()
            return 0

    if not rrdfile:
        print "RRD file must be specified"
        return 1

    if (output or output_mode or timescale) and (not output or not output_mode or not timescale):
        print "Output, output mode, and timescale must all be specified together"
        return 1

    if timescale and timescale not in ["day", "week", "month", "year", "2year"]:
        print "Timescale not recognised"
        return 1

    a2r = ApacheToRRD(rrdfile)

    for arg in args:
        a2r.parse_log(arg)

    if output:
        if output_mode == "browsers":
            a2r.output_browsers(output, timescale)
        if output_mode == "bandwidth":
            a2r.output_bandwidth(output, timescale)

if __name__ == "__main__":
    main()

