#!/usr/bin/env python3
import abc
import re
import sys
from collections import defaultdict, Counter, OrderedDict
from datetime import datetime
from operator import itemgetter


LOG_RE = re.compile(r'''
  (?P<IP>(\d{1,3}\.){3}\d{1,3})
  \s+-\s+-\s+
  \[(?P<TIMESTAMP>[^\]]*)\]
  \s+
  "(?P<REQUEST>[^"]+)"
  \s+
  (?P<STATUS>\d+)
  \s+
  (?P<SIZE>\d+)
  \s+
  "(?P<REFERRER>[^"]+)"
  \s+
  "(?P<USER_AGENT>[^"]+)"
  \s+
  (?P<PROCESS_TIME>\d+)?
  \s*
''', re.VERBOSE)


def parse_to_dict(line):
    m = LOG_RE.match(line)
    return m.groupdict()


def parse_ints(parsed_dict):
    for field in ('STATUS', 'SIZE', 'PROCESS_TIME'):
        if field in parsed_dict:
            parsed_dict[field] = int(parsed_dict[field])

    return parsed_dict


def parse_datetime(parsed_dict):
    parsed_dict['DATETIME'] = datetime.strptime(
        parsed_dict['TIMESTAMP'], '%d/%b/%Y:%H:%M:%S %z')
    return parsed_dict


REQUEST_RE = re.compile(r'''
  (?P<REQUEST_METHOD>[A-Z]+)\s(?P<REQUEST_URL>[^ ]+)\sHTTP/
''', re.VERBOSE)


def parse_request(parsed_dict):
    parsed_dict.update(REQUEST_RE.match(parsed_dict['REQUEST']).groupdict())
    return parsed_dict


PARSERS = (parse_to_dict, parse_ints, parse_datetime, parse_request)


def parse_file(lines, parsers=PARSERS):
    for line in lines:
        try:
            parsed = line
            for parser in parsers:
                parsed = parser(parsed)
            yield parsed
        except Exception as e:
            pass


def prepare_output(stats: dict, offset=0, indent=2) -> str:
    """
    This function provides very simple yaml-like format
    (And we will parse it's output with yaml so use it carefully)
    """
    result = []
    for key, val in sorted(stats.items(), key=itemgetter(0)):
        if indent:
            result.extend([' '] * offset)
        result.extend([
            str(key),
            ': ',
            str(val) if not isinstance(val, dict) else '\n' + prepare_output(
                val, offset=offset + indent, indent=indent),
            '\n'
        ])

    return ''.join(result)


class Statistics(metaclass=abc.ABCMeta):
    @property
    def name(self):
        return type(self).__name__

    @abc.abstractclassmethod
    def handle_record(self, record):
        pass

    @abc.abstractproperty
    def result(self):
        pass


class SlowestPage(Statistics):
    def __init__(self):
        self.slowest_page = None
        self.slowest_page_speed = 0

    def handle_record(self, record):
        if record['PROCESS_TIME'] >= self.slowest_page_speed:
            self.slowest_page_speed = record['PROCESS_TIME']
            self.slowest_page = record['REQUEST_URL']

    def result(self):
        return self.slowest_page


class FastestPage(Statistics):
    def __init__(self):
        self.fastest_page = None
        self.fastest_page_speed = 10 ** 100

    def handle_record(self, record):
        if record['PROCESS_TIME'] <= self.fastest_page_speed:
            self.fastest_page_speed = record['PROCESS_TIME']
            self.fastest_page = record['REQUEST_URL']

    def result(self):
        return self.fastest_page


class SlowestAveragePage(Statistics):
    def __init__(self):
        self.pages = defaultdict(lambda: {'count': 0, 'cumulative_time': 0})

    def handle_record(self, record):
        page = record['REQUEST_URL']
        self.pages[page]['count'] += 1
        self.pages[page]['cumulative_time'] += record['PROCESS_TIME']

    def result(self):
        def average(dct):
            return dct['cumulative_time'] / dct['count']

        page, stat = max(self.pages.items(), key=lambda tpl: average(tpl[1]))
        return page


def most_common_lex_minimal(counter):
    max_count = None
    answers = []
    for (item, count) in counter.most_common():
        if max_count is None:
            max_count = count

        if count != max_count:
            break

        answers.append(item)
    return min(answers)


class MostPopularPage(Statistics):
    def __init__(self):
        self.pages = Counter()

    def handle_record(self, record):
        self.pages[record['REQUEST_URL']] += 1

    def result(self):
        return most_common_lex_minimal(self.pages)


class MostActiveClient(Statistics):
    def __init__(self):
        self.clients = Counter()

    def handle_record(self, record):
        self.clients[record['IP']] += 1

    def result(self):
        return most_common_lex_minimal(self.clients)


class MostPopularBrowser(Statistics):
    def __init__(self):
        self.browsers = Counter()

    def handle_record(self, record):
        self.browsers[record['USER_AGENT']] += 1

    def result(self):
        return most_common_lex_minimal(self.browsers)


class MostActiveClientByDay(Statistics):
    def __init__(self):
        self.stat_by_day = defaultdict(Counter)

    def handle_record(self, record):
        self.stat_by_day[record['DATETIME'].date()][record['IP']] += 1

    def result(self):
        return OrderedDict(sorted(
            ((date, most_common_lex_minimal(counter))
             for date, counter in self.stat_by_day.items()),
            key=itemgetter(0)
        ))


ALL_STATS = (SlowestPage, FastestPage, SlowestAveragePage, MostPopularPage,
             MostActiveClient, MostPopularBrowser, MostActiveClientByDay)

# ALL_STATS = tuple(cls for cls in sys.modules[__name__].__dict__.values() if
#                   (inspect.isclass(cls) and issubclass(cls, Statistics) and
#                    not inspect.isabstract(cls)))


def harvest_stats(feed, statistics=ALL_STATS):
    stats_builders = list(map(lambda x: x(), statistics))
    for record in feed:
        for sb in stats_builders:
            sb.handle_record(record)

    return {
        sb.name: sb.result()
        for sb in stats_builders
    }


def main():
    with sys.stdin as f:
        stats = harvest_stats(parse_file(f))
        print(prepare_output(stats))


if __name__ == '__main__':
    main()
