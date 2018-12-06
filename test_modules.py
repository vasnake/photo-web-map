#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Valik mailto:vasnake@gmail.com

"""
Purpose: test python modules setup

Expected usage:

    docker run -it --rm \
        --name test-python \
        -v "${__dir}":/usr/src/project \
        -w /usr/src/project \
        python:3.7.1 python test_modules.py
"""

import sys
import time

def test_geocode():
    import reverse_geocoder as rg
    coordinates = [(51.5214588, -0.1729636)]
    results = rg.search(coordinates)
    print("coords: '{}', address: '{}'".format(coordinates, results))

def test_csv(filename, ncols=88):
    """
    https://docs.python.org/3/library/csv.html
    """
    import csv
    nlines = 0
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',',
            quotechar='"', doublequote=True, escapechar='"', quoting=csv.QUOTE_NONE,
            lineterminator="\r\n", skipinitialspace=False, strict=True)
        for row in reader:
            #~ print(', '.join(row))
            nlines += 1
            assert len(row) == ncols, "len(row): {}".format(len(row))
            # sed -n '1{p;q}' test.csv | grep -o "," | wc # 87      87     174

    print("file '{}' OK, {} lines readed".format(filename, nlines))

def start_time():
    start_ns = time.time_ns()
    print("start, nanoseconds from epoch: {}".format(start_ns))
    return start_ns

def end_time(start_ns):
    end_ns = time.time_ns()
    dur_ns = end_ns - start_ns

    print("end, nanoseconds from epoch: {}; duration: {} nanoseconds or {} microseconds or {} milliseconds".format(
        end_ns, dur_ns, dur_ns / 1000, dur_ns / 1000000
    ))

    return end_ns

def main():
    st = start_time()
    print("python version: {}".format(sys.version))
    assert sys.version_info >= (3, 7, 1)
    test_csv('test.csv', 88)
    test_geocode()
    end_time(st)

if __name__ == "__main__":
    # execute only if run as a script
    main()
