#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Valik mailto:vasnake@gmail.com

"""
Purpose: add address info (state, town) to csv columns

Expected usage:
    export PYTHONIOENCODING=UTF-8
    python -u geocode.py norm_data_tab.csv map_markers_data.csv
"""

import sys
import csv

import reverse_geocoder as rg

from normcsv import start_time, end_time, csv_options


COLNAME_LAT = 'Composite:GPSLatitude'
COLNAME_LON = 'Composite:GPSLongitude'
COLNAME_STATE = 'state'
COLNAME_TOWN = 'town'

RG_COLNAME_STATE = 'admin1'
RG_COLNAME_TOWN = 'name'

COLUMNS_MAPPING = [
    (RG_COLNAME_STATE, COLNAME_STATE),
    (RG_COLNAME_TOWN, COLNAME_TOWN)
]


def added_fields():
    """Return list of col. names that should be added to csv
    """
    return [cn for rgcn,cn in COLUMNS_MAPPING]

def add_town(row):
    """Reverse geocoding here.
    Add 'state' and 'town' values to row.
    Return modified row.
    """
    coordinates = float(row[COLNAME_LAT]), float(row[COLNAME_LON])
    town = rg.get(coordinates)

    for rgcn,cn in COLUMNS_MAPPING:
        row[cn] = town[rgcn]

    return row

def show_progress(n):
    if n % 10 == 0:
        print(n)

def geocode(infile='test.csv', outfile='geocoded_test.csv'):
    """For each record in infile enrich it with 'state', 'town' columns and write to outfile.
    """
    csvopts = csv_options()

    nlines = 0
    with open(infile, newline='') as inf:
        with open(outfile, 'w', newline='') as outf:
            reader = csv.DictReader(inf, **csvopts)
            flds = reader.fieldnames + added_fields()
            writer = csv.DictWriter(outf, fieldnames=flds, **csvopts)
            writer.writeheader()

            for row in reader:
                nlines += 1
                writer.writerow(add_town(row))
                show_progress(nlines)

    assert nlines == 1302 + 30, "nlines: {}".format(nlines)

def main():
    st = start_time()
    infile,outfile = sys.argv[1:3]
    geocode(infile, outfile)
    end_time(st)

if __name__ == "__main__":
    main()
