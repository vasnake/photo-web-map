#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Valik mailto:vasnake@gmail.com

"""
Purpose: collect jpg and mp4 files

Expected usage:

    python collect_csv.py db_dir thumb_dir first_dir second_dir [other dirs]
"""

import time
import sys

def main(argv):
    print("python version: {}".format(sys.version))
    assert sys.version_info >= (3, 5, 5)
    db_dir, thumb_dir = argv[1:3]
    files_dirs = argv[3:]
    print("db: <{}>\nthumb: <{}>\nfiles: <{}>".format(
        db_dir, thumb_dir, ",".join(files_dirs)
    ))

if __name__ == "__main__":
    main(sys.argv)
