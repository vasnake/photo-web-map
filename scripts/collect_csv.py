#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Valik mailto:vasnake@gmail.com

"""
Purpose: collect jpg and mp4 files

Expected usage:

    python collect_csv.py db_dir thumb_dir first_dir [other dirs]
"""

import time
import sys
import os


def collect_files_info(path):
    print("collect files in path `{}`".format(path))
    res = []
    _, subdirs, files = os.walk(path)

    for fname in files:
        res.append(fname)

    for subdir in subdirs:
        subres = collect_files_info(subdir)
        res = res + subres

    return res


def main(argv):
    print("python version: {}".format(sys.version))
    assert sys.version_info >= (3, 5, 5)

    db_dir, thumb_dir = argv[1:3]
    files_dirs = argv[3:]

    print("arguments:\ndb: <{}>\nthumb: <{}>\nfiles: <{}>".format(
        db_dir, thumb_dir, ",".join(files_dirs)
    ))

    all_files_info = []
    for fd in files_dirs:
        files_info = collect_files_info(fd)
        all_files_info = all_files_info + files_info

    print(all_files_info)


if __name__ == "__main__":
    main(sys.argv)
