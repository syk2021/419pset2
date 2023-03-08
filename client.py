#!/usr/bin/env python

# -----------------------------------------------------------------------
# echoclient.py
# Author: Bob Dondero
# -----------------------------------------------------------------------

from sys import exit, argv, stderr
from socket import socket

# -----------------------------------------------------------------------


def main():

    if len(argv) != 3:
        print('Usage: python %s host port' % argv[0])
        exit(1)

    try:
        host = argv[1]
        port = int(argv[2])

        line = input()
        if line is None:
            return

        with socket() as sock:
            sock.connect((host, port))

            out_flo = sock.makefile(mode='w', encoding='utf-8')
            out_flo.write(line + '\n')
            out_flo.flush()

            in_flo = sock.makefile(mode='r', encoding='utf-8')
            echoed_line = in_flo.readline()

        if echoed_line == '':
            print('The echo server crashed', file=stderr)
        else:
            print(echoed_line, end='')

    except Exception as ex:
        print(ex, file=stderr)
        exit(1)

# -----------------------------------------------------------------------


if __name__ == '__main__':
    main()
