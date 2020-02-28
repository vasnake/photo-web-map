#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Valik mailto:vasnake@gmail.com

"""
Purpose: collect jpg and mp4 files

Expected usage:

    python collect_csv.py db_dir thumb_dir first_dir [other dirs]
"""

import os
import sys


def collect_all_files(path):
    print("INFO: collect files in path `{}` ...".format(path))
    res = []
    if os.path.isdir(path):
        for root, subdirs, files in os.walk(path):
            # print("DEBUG: root: `{}`, subdirs: `{}`, files: `{}`".format(root, subdirs, files)[:100])
            abs_root = os.path.abspath(root)
            for fname in files:
                abs_fname = os.path.join(abs_root, fname)
                print("DEBUG: file: `{}`".format(abs_fname))
                res.append(abs_fname)
    else:
        print("ERROR: given path is not a directory")

    return res


def filter_files(lst, ext=""):
    dotext = ".{}".format(ext)

    def in_condition(x):
        cnd = False
        if ext:
            head, tail = os.path.splitext(x)
            cnd = (dotext == tail)
        return cnd

    return [x for x in lst if in_condition(x)]


def main(argv):
    print("INFO: python version: {}".format(sys.version))
    assert sys.version_info >= (3, 5, 5)

    db_dir, thumb_dir = argv[1:3]
    files_dirs = argv[3:]

    print("INFO: arguments:\n\tdb dir: `{}`\n\tthumb dir: `{}`\n\tfiles dirs: `[{}]`".format(
        db_dir, thumb_dir, ", ".join(files_dirs)
    ))

    all_files = []
    for fd in files_dirs:
        files = collect_all_files(fd)
        all_files += files

    print("INFO: all files: \n{}".format("\n".join(all_files)))

    jpg_files = filter_files(all_files, ext="py")
    print("INFO: jpg files: \n{}".format("\n".join(jpg_files)))
    mp4_files = filter_files(all_files, ext="css")
    print("INFO: mp4 files: \n{}".format("\n".join(mp4_files)))


if __name__ == "__main__":
    main(sys.argv)
