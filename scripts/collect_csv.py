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
    print("INFO: collect files in path `{}`".format(path))
    res = []
    if os.path.isdir(path):
        for root, subdirs, files in os.walk(path):
            print("DEBUG: root: `{}`, subdirs: `{}`, files: `{}`".format(root, subdirs, files)[:100])
            abs_root = os.path.abspath(root)
            for fname in files:
                abs_fname = os.path.join(abs_root, fname)
                print("DEBUG: abs. file path: `{}`".format(abs_fname))
                res.append(abs_fname)
    else:
        print("ERROR: given path is not a directory")

    return res


def main(argv):
    print("INFO: python version: {}".format(sys.version))
    assert sys.version_info >= (3, 5, 5)

    db_dir, thumb_dir = argv[1:3]
    files_dirs = argv[3:]

    print("INFO: arguments:\ndb: <{}>\nthumb: <{}>\nfiles: <{}>".format(
        db_dir, thumb_dir, ",".join(files_dirs)
    ))

    all_files_info = []
    for fd in files_dirs:
        files_info = collect_files_info(fd)
        all_files_info = all_files_info + files_info

    print("INFO: all files info: {}".format(all_files_info))


if __name__ == "__main__":
    main(sys.argv)
