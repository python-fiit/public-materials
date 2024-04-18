"""Модуль со вспомогательными функциями"""
from contextlib import contextmanager


def parse_int(string):
    """Число, указанное в строке или None в случае ошибки"""
    try:
        return int(string)
    except ValueError:
        return None


def to_int(iterable):
    """Переводит коллекцию в кортеж целых чисел"""
    return tuple(map(int, iterable))


def first_or_default(iterable, default=None):
    """Первый элемент коллекции либо указанный"""
    for value in iterable:
        return value

    return default


@contextmanager
def at_exit(func):
    """Контекст, вызывающий указанную функцию после завершения блока"""
    try:
        yield
    finally:
        func()
