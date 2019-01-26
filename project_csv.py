#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Valik mailto:vasnake@gmail.com

"""
Purpose: project columns

normalize dataset: select columns subset
    SourceFile
    IFD0:Orientation
    Composite:GPSAltitude
    Composite:GPSLatitude
    Composite:GPSLongitude
    Composite:SubSecDateTimeOriginal

Expected usage:
    export PYTHONIOENCODING=UTF-8
    python -u project_csv.py in.csv out.csv
"""

import sys
import time
import csv
import math

from collections import OrderedDict
from itertools import zip_longest
from datetime import datetime


def list_out_fields():
    """Output csv columns names
    """
    lst = """
        SourceFile
        IFD0:Orientation
        Composite:GPSAltitude
        Composite:GPSLatitude
        Composite:GPSLongitude
        Composite:SubSecDateTimeOriginal
    """
    return split_n_trim(lst)

def datetime_format():
    """Date and time values format used in csv
    """
    return {'format': '%Y:%m:%d %H:%M:%S.%f', 'len': 22}

def csv_options():
    """CSV format options
    """
    return dict(
        delimiter=',',
        quotechar='"',
        doublequote=True,
        escapechar='"',
        quoting=csv.QUOTE_NONE,
        lineterminator="\r\n",
        skipinitialspace=False,
        strict=True
    )

def split_n_trim(txt):
    """Return list of non-empty strings from input splitted by blank chars
    """
    lst = txt.splitlines()
    return [x.strip() for x in lst if x.strip()]

def check_columns(cols, expected_cols):
    """Assert that cols list is equal expected_cols list
    """
    pairs = zip_longest(cols, expected_cols, fillvalue='oops')
    for c,e in pairs:
        assert c == e, "column {} != expected col {}".format(c, e)

def normalize_value(colname, colvalue):
    return (colname, colvalue.strip())

def getOrElse(row, k, nv):
    try:
        val = row[k]
    except KeyError:
        val = nv
    return val

def normalize_row(row, columns):
    """Return OrderedDict where keys list == columns and values normalized
    """
    return OrderedDict([
        normalize_value(col, row.get(col, '')) for col in columns
    ])

def fix_nulls(iter):
    for line in iter:
        yield line.replace('\0', '')

def project(infile='in_test.csv', outfile='out_test.csv'):
    """Write selected fields
    """
    csvopts = csv_options()
    flds = list_out_fields()

    nlines = 0
    with open(infile, newline='') as inf:
        with open(outfile, 'w', newline='') as outf:
            reader = csv.DictReader(fix_nulls(inf), **csvopts)
            writer = csv.DictWriter(outf, fieldnames=flds, **csvopts)
            writer.writeheader()

            for row in reader:
                nlines += 1
                # project
                norm_row = normalize_row(row, flds)
                # check row
                msg = "len(norm_row) != len(flds): {} != {}"
                assert len(norm_row) == len(flds), msg.format(len(norm_row), len(flds))
                check_columns(norm_row.keys(), flds)
                # store/save/write
                writer.writerow(norm_row)

    print("file '{}' OK, {} lines readed".format(infile, nlines))

def start_time():
    start_ns = time.time_ns()
    print("start, nanoseconds from epoch: {}".format(start_ns))
    return start_ns

def end_time(start_ns):
    end_ns = time.time_ns()
    dur_ns = end_ns - start_ns

    print("""end, nanoseconds from epoch: {};
        duration: {} nanoseconds
        or {} microseconds
        or {} milliseconds
        or {} seconds""".format(
        end_ns, dur_ns, dur_ns / 1000, dur_ns / 1000000, dur_ns / 1000000000
    ))

    return end_ns

def main():
    st = start_time()
    infile,outfile = sys.argv[1:3]
    project(infile, outfile)
    end_time(st)

if __name__ == "__main__":
    main()
