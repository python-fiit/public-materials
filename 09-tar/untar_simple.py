# Tar: https://en.wikipedia.org/wiki/Tar_(computing)

# formats for struct.unpack
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


def list_files(archive_path):
    pass
