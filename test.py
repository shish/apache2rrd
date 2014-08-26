#!/usr/bin/env python

import os
import a2r
import unittest


class Test_A2R(unittest.TestCase):
    def tearDown(self):
        if os.path.exists("test.rrd"):
            os.unlink("test.rrd")

    def test_init(self):
        a = a2r.ApacheToRRD("test.rrd")

        self.assertEqual(a.gecko, 0)
        self.assertEqual(a.other, 0)
        self.assertEqual(a.bandwidth, 0)

    def test_parse_date(self):
        a = a2r.ApacheToRRD("test.rrd")

        self.assertEqual(a.parse_date("01/Jan/1970:00:00:00"), 0)

        # this works on my system, but if the above is returning -3600
        # because timezones, then the number I chose here is wrong...
        #self.assertEqual(a.parse_date("21/Aug/2014:15:30:27"), 1408631427)



class Test_Usage(unittest.TestCase):
    def test(self):
        # just check it doesn't crash
        a2r.usage()
