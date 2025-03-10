#!/usr/bin/env python3

import phil as t
from urllib.request import urlopen
from urllib.parse import quote
from urllib.error import URLError, HTTPError
import unittest


PHIL = 'Философия'


def _has_link(name, link):
    try:
        with urlopen('http://ru.wikipedia.org/wiki/' + quote(name)) as page:
            content = page.read().decode('utf-8', errors='ignore')
    except (URLError, HTTPError):
        return False

    quoted_link = quote(link, safe='()_,-/')
    return (quoted_link in content or
            quoted_link.replace('/', '%2F') in content)


class TestLinksExtractor(unittest.TestCase):
    TEXT = '<a href="/wiki/A">t</a>text<a href="/wiki/B">t</a>'

    def _check_with_bound(self, text, begin, end, links=None):
        if links is None:
            links = set()

        self.assertSetEqual(set(t.extract_links(text, begin, end)), links)

    def _check(self, text, links=None):
        self._check_with_bound(text, 0, len(text), links)

    def test_category(self):
        self._check('<a href="/wiki/category:unknown%2ecategory">text</a>')

    def test_anchors(self):
        self._check('<a href="/wiki/Link#tt">text</a>')
        self._check('<a href="#qq">text</a>')

    def test_another_link(self):
        self._check('<a href="/w/index.php?title=tt">tt</a>')

    def test_simple_link(self):
        self._check('<a href="/wiki/Link_one">qq</a>', {'Link_one'})

    def test_tag_case_insensitivity(self):
        self._check('<A Href="/wiki/Link_one">qq</A>', {'Link_one'})

    def test_tag_spaces(self):
        self._check("<a  href='/wiki/Link_one'>qq</a", {'Link_one'})

    def test_russian_letters(self):
        self._check(
            '<a href="/wiki/46_%D0%B3%D0%BE" title="qq">x</a>', {'46_го'})

    def test_link_case_sensitivity(self):
        self._check(
            '<a href="/wiki/L">t1</a><a href="/wiki/l">t2</a>', {'L', 'l'})
        self._check(
            '<a href="/wiki/L">t1</a><a href="/wiki/L">t2</a>', {'L'})

    def test_multiple_links(self):
        self._check("""<a href="/wiki/L">t1</a><a href='/wiki/l'>t2</a>"""
                    """<a href='/wiki/L'>t3</a>""", {'L', 'l'})
        self._check(self.TEXT, {'A', 'B'})

    def test_multiline(self):
        self._check("""<a href="/wiki/L">t1</a>
<a href='/wiki/l'>t2</a><a href='/wiki/L'>t3</a>""", {'L', 'l'})

    def test_general(self):
        self._check("""<a href='/wiki/C:x'>link</a><span>Some text
</span><a  href="/wiki/Link_one">link</a><a href="/wiki/Link_one#tt"></a><div>
<a href='#qq'><span>qq</span></a> <a href="/w/index.php?title=tt"></a></div>
<a href='/wiki/1946_%D0%B3%D0%BE%D0%B4' title="1946 год">1946</a>
<a href=''""", {'Link_one', '1946_год'})

    def test_left_border(self):
        self._check_with_bound(self.TEXT, 10, len(self.TEXT), {'B'})

    def test_right_border(self):
        self._check_with_bound(self.TEXT, 0, len(self.TEXT) - 10, {'A'})

    def test_left_right_border(self):
        self._check_with_bound(self.TEXT, 10, len(self.TEXT) - 10)


class TestChainFinder(unittest.TestCase):
    def assertIsEmptyChain(self, chain):
        self.assertIsNone(chain)

    def assertIsChain(self, chain, start):
        self.assertIsNotNone(chain)
        self.assertIs(type(chain), list)
        self.assertEqual(chain[0], start)
        self.assertEqual(chain[-1], PHIL)

        for (index, value) in enumerate(chain):
            if index + 1 < len(chain):
                self.assertTrue(_has_link(value, chain[index + 1]))

    def _check(self, begin, end=PHIL, result=True):
        with self.subTest(begin):
            if result:
                self.assertIsChain(t.find_chain(begin, end), begin)
            else:
                self.assertIsEmptyChain(t.find_chain(begin, end))

    def test_simple_chain(self):
        self._check(PHIL)

    def test_wrong_word(self):
        self._check('фвыавыафывавыавыфа', result=False)

    def test_start_case_insensitivity(self):
        self._check('Математика')
        self._check('математика')

    def test_something(self):
        self._check('Архимед')
        self._check('Религия')
        self._check('Бумага')
        self._check('Компьютер')

    def test_special_symbols(self):
        self._check('музыка')
        self._check('Музыка_(значения)')

    def test_russian_yo_ye(self):
        self._check('Самолет')
        self._check('Самолёт')


def make_suite():
    suite = unittest.TestSuite()
    for test in (TestLinksExtractor, TestChainFinder):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test))
    return suite


if __name__ == '__main__':
    unittest.main()
