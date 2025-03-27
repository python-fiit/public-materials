import os
import sys
import itertools


def project_stats(path, extensions):
    """
    Вернуть число строк в исходниках проекта.

    Файлами, входящими в проект, считаются все файлы
    в папке ``path`` (и подпапках), имеющие расширение
    из множества ``extensions``.
    """

    # <= 3 strings here


def total_number_of_lines(filenames):
    """
    Вернуть общее число строк в файлах ``filenames``.
    """

    # <= 2 strings here


def number_of_lines(filename):
    """
    Вернуть число строк в файле.
    """

    # <= 3 strings here


def iter_filenames(path):
    """
    Итератор по именам файлов в дереве.
    """

    # <= 4 strings here


def with_extensions(extensions, filenames):
    """
    Оставить из итератора ``filenames`` только
    имена файлов, у которых расширение - одно из ``extensions``.
    """

    # <= 3 strings here


def get_extension(filename):
    """ Вернуть расширение файла """

    # <= 3 strings here


def print_usage():
    print("Usage: python project_sourse_stats_3.py <project_path>")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    project_path = sys.argv[1]
    print(project_stats(project_path, {'.py'}))
