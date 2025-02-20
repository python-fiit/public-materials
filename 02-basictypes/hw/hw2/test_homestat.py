#!/usr/bin/env python3

import homestat as t
import unittest


class TestStatistics(unittest.TestCase):
    def assertHasOrder(self, iterable, func=None):
        if func is None:
            func = lambda a, b: a <= b

        back = None
        for item in iterable:
            if back is not None:
                self.assertTrue(func(back, item))
            back = item

    def assertSubSequence(self, a, b):
        for i in a:
            self.assertIn(i, b)

    def setUp(self):
        self._stat = t.make_stat('home.html')
        self._cmp = lambda a, b: a[1] >= b[1]

    def test_extract_years(self):
        self.assertListEqual(
            t.extract_years(self._stat),
            list(map(str, range(2004, 2013))))

    def test_extract_general_correct_order(self):
        self.assertHasOrder(
            t.extract_general(self._stat), func=self._cmp)

    def _check_type(self, item):
        self.assertIs(type(item), tuple)
        self.assertEqual(len(item), 2)
        self.assertIs(type(item[0]), str)
        self.assertIs(type(item[1]), int)

    def test_extract_general_correct_type(self):
        for item in t.extract_general(self._stat):
            self._check_type(item)

    def test_extract_male_correct_order(self):
        self.assertHasOrder(
            t.extract_general_male(self._stat), func=self._cmp)

    def test_extract_male_correct_type(self):
        for item in t.extract_general_male(self._stat):
            self._check_type(item)

    def test_extract_female_correct_order(self):
        self.assertHasOrder(
            t.extract_general_female(self._stat), func=self._cmp)

    def test_extract_female_correct_type(self):
        for item in t.extract_general_female(self._stat):
            self._check_type(item)

    def test_extract_year_correct_order(self):
        for year in t.extract_years(self._stat):
            self.assertHasOrder(
                t.extract_year(self._stat, year), func=self._cmp)

    def test_extract_year_correct_type(self):
        for year in t.extract_years(self._stat):
            for item in t.extract_year(self._stat, year):
                self._check_type(item)

    def test_extract_year_male_correct_order(self):
        for year in t.extract_years(self._stat):
            self.assertHasOrder(
                t.extract_year_male(self._stat, year), func=self._cmp)

    def test_extract_year_male_correct_type(self):
        for year in t.extract_years(self._stat):
            for item in t.extract_year_male(self._stat, year):
                self._check_type(item)

    def test_extract_year_female_correct_order(self):
        for year in t.extract_years(self._stat):
            self.assertHasOrder(
                t.extract_year_female(self._stat, year), func=self._cmp)

    def test_extract_year_female_correct_type(self):
        for year in t.extract_years(self._stat):
            for item in t.extract_year_female(self._stat, year):
                self._check_type(item)

    def test_general_equals_male_plus_female(self):
        alls = t.extract_general(self._stat)
        males = t.extract_general_male(self._stat)
        females = t.extract_general_female(self._stat)

        self.assertEqual(len(alls), len(males) + len(females))
        self.assertSubSequence(males, alls)
        self.assertSubSequence(females, alls)

    def test_year_equals_male_plus_female(self):
        for year in t.extract_years(self._stat):
            alls = t.extract_year(self._stat, year)
            males = t.extract_year_male(self._stat, year)
            females = t.extract_year_female(self._stat, year)

            self.assertEqual(len(alls), len(males) + len(females))
            self.assertSubSequence(males, alls)
            self.assertSubSequence(females, alls)

    def test_correct_sex(self):
        self.assertSubSequence(
            (('Дмитрий', 36), ('Илья', 19), ('Игорь', 12), ('Роман', 8),
             ('Кирилл', 7), ('Никита', 5), ('Лёва', 1), ('Алехандро', 1)),
            t.extract_general_male(self._stat))

        self.assertSubSequence(
            (('Елена', 18), ('Ксения', 5), ('Любовь', 2),
             ('Алёна', 2), ('Елизавета', 1)),
            t.extract_general_female(self._stat))

    def test_correct_stat(self):
        self.assertSubSequence(
            (('Артём', 1), ('Олег', 1), ('Елена', 1), ('Анна', 1)),
            t.extract_year(self._stat, '2004'))
        self.assertEqual(10, len(t.extract_year(self._stat, '2004')))

        self.assertSubSequence(
            (('Дмитрий', 5), ('Сергей', 1), ('Алексей', 2),
             ('Елена', 4), ('Евгения', 1), ('Наташа', 1)),
            t.extract_year(self._stat, '2005'))
        self.assertEqual(31, len(t.extract_year(self._stat, '2005')))

        self.assertSubSequence(
            (('Михаил', 3), ('Фёдор', 1), ('Павел', 5),
             ('Екатерина', 3), ('Ирина', 1)),
            t.extract_year(self._stat, '2006'))
        self.assertEqual(38, len(t.extract_year(self._stat, '2006')))

        self.assertSubSequence(
            (('Александр', 6), ('Антон', 2), ('Михаил', 3), ('Егор', 1),
             ('Ксения', 3), ('Дарья', 2), ('Юлия', 1)),
            t.extract_year(self._stat, '2007'))
        self.assertEqual(53, len(t.extract_year(self._stat, '2007')))

        self.assertSubSequence(
            (('Сергей', 5), ('Евгений', 2), ('Артур', 1), ('Алехандро', 1),
             ('Елена', 2), ('Наталья', 1), ('Лидия', 1)),
            t.extract_year(self._stat, '2008'))
        self.assertEqual(40, len(t.extract_year(self._stat, '2008')))

        self.assertSubSequence(
            (('Никита', 2), ('Илья', 5), ('Леонид', 1), ('Данил', 1),
             ('Елена', 2), ('Евгения', 1), ('Елизавета', 1)),
            t.extract_year(self._stat, '2009'))
        self.assertEqual(40, len(t.extract_year(self._stat, '2009')))

        self.assertSubSequence(
            (('Андрей', 4), ('Игорь', 2), ('Роберт', 1), ('Борис', 1),
             ('Дарья', 2), ('Лилия', 1), ('Надежда', 1)),
            t.extract_year(self._stat, '2010'))
        self.assertEqual(41, len(t.extract_year(self._stat, '2010')))

        self.assertSubSequence(
            (('Антон', 3), ('Григорий', 1), ('Георгий', 1),
             ('Ирина', 4), ('Валерия', 1), ('Марина', 1), ('Любовь', 1)),
            t.extract_year(self._stat, '2011'))
        self.assertEqual(43, len(t.extract_year(self._stat, '2011')))

        self.assertSubSequence(
            (('Дмитрий', 6), ('Олег', 2), ('Лёва', 1), ('Даниил', 1),
             ('Татьяна', 3), ('Мария', 2), ('Алиса', 1)),
            t.extract_year(self._stat, '2012'))
        self.assertEqual(44, len(t.extract_year(self._stat, '2012')))


if __name__ == '__main__':
    unittest.main()
