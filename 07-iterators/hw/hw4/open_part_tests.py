#!/usr/bin/env python3

import datetime
import unittest
import urllib.request

import hw4 as t


TEST_LOG = 'https://alexbers.com/python/test.log'


class Test(unittest.TestCase):
    def setUp(self):
        with urllib.request.urlopen(TEST_LOG) as f:
            self.data = f.read().decode('utf-8').split('\n')

        self.stat = t.make_stat()

    def test(self):
        for line in filter(lambda s: 'OPTION' not in s, self.data):
            self.stat.add_line(line)

        self.assertDictEqual(self.stat.results(), TEST)


TEST = {
    'FastestPage': '/img/r.png',
    'MostActiveClient': '192.168.12.155',
    'MostActiveClientByDay': {datetime.date(2012, 7, 8): '192.168.12.155'},
    'MostPopularBrowser': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; '
                          'Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR '
                          '3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; '
                          'Tablet PC 2.0; .NET4.0C; .NET4.0E; InfoPath.3; '
                          'MS-RTC LM 8)',
    'MostPopularPage': '/img/ao.gif',
    'SlowestAveragePage': '/call_centr.php',
    'SlowestPage': '/menu-top.php'}


if __name__ == '__main__':
    unittest.main()
