#!/usr/bin/env python3

import argparse
import os.path
import time
import struct
import sys


class TarParser:
    _HEADER_FMT1 = '100s8s8s8s12s12s8sc100s255s'
    _HEADER_FMT2 = '6s2s32s32s8s8s155s12s'
    _HEADER_FMT3 = '6s2s32s32s8s8s12s12s112s31x'
    _READ_BLOCK = 16 * 2**20

    _FILE_TYPES = {
        b'0': 'Regular file',
        b'1': 'Hard link',
        b'2': 'Symbolic link',
        b'3': 'Character device node',
        b'4': 'Block device node',
        b'5': 'Directory',
        b'6': 'FIFO node',
        b'7': 'Reserved',
        b'D': 'Directory entry',
        b'K': 'Long linkname',
        b'L': 'Long pathname',
        b'M': 'Continue of last file',
        b'N': 'Rename/symlink command',
        b'S': "`sparse' regular file",
        b'V': "`name' is tape/volume header name"
    }

    def __init__(self, filename):
        '''
        Открывает tar-архив `filename' и производит его предобработку
        (если требуется)
        '''

        ### TODO

    def extract(self, dest=os.getcwd()):
        '''
        Распаковывает данный tar-архив в каталог `dest'
        '''

        ### TODO

    def files(self):
        '''
        Возвращает итератор имён файлов (с путями) в архиве
        '''

        ### TODO

    def file_stat(self, filename):
        '''
        Возвращает информацию о файле `filename' в архиве.

        Пример (некоторые поля могут отсутствовать, подробности см. в описании
        формата tar):
        [
            ('Filename', '/NSimulator'),
            ('Type', 'Directory'),
            ('Mode', '0000755'),
            ('UID', '1000'),
            ('GID', '1000'),
            ('Size', '0'),
            ('Modification time', '29 Mar 2014 03:52:45'),
            ('Checksum', '5492'),
            ('User name', 'victor'),
            ('Group name', 'victor')
        ]
        '''
        if filename not in self.files:
            raise ValueError(filename)

        info = [('Filename', filename)]

        ### TODO

        return info


def print_file_info(stat, f=sys.stdout):
    max_width = max(map(lambda s: len(s[0]), stat))
    for field in stat:
        print("{{:>{}}} : {{}}".format(max_width).format(*field), file=f)


def main():
    parser = argparse.ArgumentParser(
        usage='{} [OPTIONS] FILE'.format(os.path.basename(sys.argv[0])),
        description='Tar extractor')
    parser.add_argument('-l', '--list', action='store_true', dest='ls',
                        help='list the contents of an archive')
    parser.add_argument('-x', '--extract', action='store_true', dest='extract',
                        help='extract files from an archive')
    parser.add_argument('-i', '--info', action='store_true', dest='info',
                        help='get information about files in an archive')
    parser.add_argument('fn', metavar='FILE',
                        help='name of an archive')

    args = parser.parse_args()
    if not (args.ls or args.extract or args.info):
        sys.exit("Error: action must be specified")

    try:
        tar = TarParser(args.fn)

        if args.info:
            for fn in sorted(tar.files()):
                print_file_info(tar.file_stat(fn))
                print()
        elif args.ls:
            for fn in sorted(tar.files()):
                print(fn)

        if args.extract:
            tar.extract()
    except Exception as e:
        sys.exit(e)

if __name__ == '__main__':
    main()
