#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Valik mailto:vasnake@gmail.com

"""
Purpose: filter and normalize photos data given from exiftool csv dump;
copy photo meta-data to video files using date-time nearest photo.

normalize dataset: select columns subset; replace null values with default values
    SourceFile
    IFD0:Orientation
    Composite:GPSAltitude
    Composite:GPSLatitude
    Composite:GPSLongitude
    Composite:SubSecDateTimeOriginal

Expected usage:
    export PYTHONIOENCODING=UTF-8
    python -u normcsv.py photo_video_data_tab.csv norm_data_tab.csv
"""

import sys
import time
import csv
import math

from collections import OrderedDict
from itertools import zip_longest
from datetime import datetime, timedelta


class CSV:
    COLNAME_PATH = 'SourceFile'
    COLNAME_TS   = 'Composite:SubSecDateTimeOriginal'
    COLNAME_ALT  = 'Composite:GPSAltitude'
    COLNAME_LAT  = 'Composite:GPSLatitude'
    COLNAME_LON  = 'Composite:GPSLongitude'

    TS_FORMAT    = '%Y:%m:%d %H:%M:%S.%f'
    TS_LEN       = 22

    @staticmethod
    def list_out_fields():
        """Output csv columns names
        """
        lst = [
            CSV.COLNAME_PATH,
            'IFD0:Orientation',
            CSV.COLNAME_ALT,
            CSV.COLNAME_LAT,
            CSV.COLNAME_LON,
            CSV.COLNAME_TS
        ]
        return lst

    @staticmethod
    def datetime_format():
        """Date and time values format used in csv
        """
        return dict(
            format = CSV.TS_FORMAT,
            len = CSV.TS_LEN
        )

    @staticmethod
    def dt2ts(dts):
        dt = datetime.strptime(dts, CSV.TS_FORMAT)
        ts = dt.timestamp()
        assert dts == datetime.fromtimestamp(ts).strftime(CSV.TS_FORMAT)[:CSV.TS_LEN]
        return ts

    @staticmethod
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

def normalize_row(row, columns):
    """Return OrderedDict where keys list == columns and values normalized

    datetime calc. variations: SourceFile => Composite:SubSecDateTimeOriginal

    .../P81028-105149.jpg => 2018:10:28 11:51:49.00
    .../V81005-152637.mp4 => 2018:10:05 15:26:37.00
    .../VID_20181005_152619.mp4 => 2018:10:05 15:26:19.00
    """

    def dateTimeFromFileName(path):
        dtf = CSV.TS_FORMAT
        dtl = CSV.TS_LEN
        fname = split_n_trim(path.upper(), '/')[-1]

        def fn2ts(dts, fmt, delta):
            dt = datetime.strptime(dts, fmt)
            ts = dt.timestamp()
            assert dts == datetime.fromtimestamp(ts).strftime(fmt)
            return (dt + delta).strftime(dtf)[:dtl]

        if fname.startswith('P8') or fname.startswith('V8'):
            dts = fn2ts('2018'+fname[2:-4], '%Y%m%d-%H%M%S', timedelta(minutes=0))
        elif fname.startswith('VID_'):
            dts = fn2ts(fname[4:-4], '%Y%m%d_%H%M%S', timedelta(minutes=0))
        else:
            raise ValueError(fname)

        print("timestamp from filename: {} => {}".format(fname, dts))
        return dts

    def normalize_value(colname, colvalue):
        val = colvalue.strip()
        if val == '' and colname == CSV.COLNAME_TS:
            val = dateTimeFromFileName(row[CSV.COLNAME_PATH].strip())

        return (colname, val)

    return OrderedDict([
        normalize_value(k, row.get(k, '')) for k in columns
    ])

def normalize(infile='in_test.csv', outfile='out_test.csv'):
    """Write selected fields, replace empty datetime with values from filename
    """
    csvopts = CSV.csv_options()
    flds = CSV.list_out_fields()

    nlines = 0
    with open(infile, newline='') as inf:
        with open(outfile, 'w', newline='') as outf:
            reader = csv.DictReader(inf, **csvopts)
            writer = csv.DictWriter(outf, fieldnames=flds, **csvopts)
            writer.writeheader()

            for row in reader:
                nlines += 1
                # compute normalized row
                norm_row = normalize_row(row, flds)
                # check
                msg = "len(norm_row) != len(flds): {} != {}"
                assert len(norm_row) == len(flds), msg.format(len(norm_row), len(flds))
                check_columns(norm_row.keys(), flds)
                # save/store/write
                writer.writerow(norm_row)

    assert nlines == 2691, "nlines: {}".format(nlines)
    print("file '{}' OK, {} lines readed".format(infile, nlines))
    # check writed file, optional
    #~ check_csv_file(outfile, csvopts, flds, 2691)

def fillEmptyCoords(infile='in_test.csv', outfile='out_test.csv'):
    """For records with empty coords
    calculate coords from nearest records with valid coords
    """
    csvopts = CSV.csv_options()
    flds = CSV.list_out_fields()

    photos = load_recs_with_gps(infile)
    assert len(photos) == 1243
    check_photos_sorted(photos)

def load_recs_with_gps(infile):
    """Load photos with coords to sorted array. Sort by time attribute
    """

    def new_photo(rec):
        return {
            'ts' : CSV.dt2ts(rec[CSV.COLNAME_TS]),
            'alt': rec[CSV.COLNAME_ALT],
            'lat': rec[CSV.COLNAME_LAT],
            'lon': rec[CSV.COLNAME_LON]
        }

    def gps_ok(obj):
        return (len(obj['lat']) > 0 and len(obj['lon']) > 0)

    photos = []
    csvopts = CSV.csv_options()
    with open(infile, newline='') as inf:
        reader = csv.DictReader(inf, **csvopts)
        for row in reader:
            obj = new_photo(row)
            if gps_ok(obj):
                photos.append(obj)

    print("loaded records with coords: {}".format(len(photos)))
    return sorted(photos, key=lambda x: x['ts'])

def findPhoto(ts, photos):
    """Find photo nearest by time
    """
    def binsearch(lo, hi):
        if (hi - lo) <= 0:
            return hi
        if ts <= photos[lo]['ts']:
            return lo
        if ts >= photos[hi]['ts']:
            return hi
        mid = int((hi - lo) / 2)
        if ts <= photos[lo+mid]['ts']:
            return binsearch(lo, lo+mid)
        return binsearch(lo+mid+1, hi)

    maxidx = len(photos) - 1
    idx = binsearch(0, maxidx)
    idx_ts = photos[idx]['ts']

    def closer(alt_idx):
        if alt_idx < 0 or alt_idx > maxidx:
            return false
        alt_ts = photos[alt_idx]['ts']
        return ( abs(ts - alt_ts) <= abs(ts - idx_ts) )

    photo = photos[idx]
    if ts < idx_ts and closer(idx - 1):
        photo = photos[idx - 1]
    elif ts > idx_ts and closer(idx + 1):
        photo = photos[idx + 1]

    assert abs(ts - photo['ts']) <= 381
    return photo

def build_video_record(video_fname, photos):
    """Using video filename as datetime source, copy attributes from nearest photo.
    Return OrderedDict record for writing to csv
    """
    flds = list_out_fields()
    # init values
    rec = OrderedDict([(k, '0') for k in flds])

    def fn2ts(fn):
        """Decode filename to timestamp.
        if fn: VID_20181030_100115.mp4 then dt: 2018-10-30 10:01:15
        """
        fmt = "%Y%m%d_%H%M%S"
        dts = fn[4:][:-4] # 20181030_100115
        dt = datetime.strptime(dts, fmt)
        ts = dt.timestamp()
        assert dts == datetime.fromtimestamp(ts).strftime(fmt)[:15]
        return ts

    ts = fn2ts(video_fname.split('/')[-1])
    photo = findPhoto(ts, photos)

    dtf = CSV.datetime_format()['format']
    dtl = CSV.datetime_format()['len']

    rec[CSV.COLNAME_PATH] = video_fname
    rec[CSV.COLNAME_ALT] = photo['alt']
    rec[CSV.COLNAME_LAT] = photo['lat']
    rec[CSV.COLNAME_LON] = photo['lon']
    rec[CSV.COLNAME_TS] = datetime.fromtimestamp(ts).strftime(dtf)[:dtl]
    return rec

def norm_video(in_video, in_photo, outfile):
    """Copy coords to video record from nearest photo
    """
    csvopts = CSV.csv_options()
    flds = CSV.list_out_fields()

    photos = load_photos(in_photo)
    assert len(photos) == 1302
    check_photos_sorted(photos)

    nlines = 0
    with open(in_video, newline='') as inf:
        with open(outfile, 'w', newline='') as outf:
            reader = csv.DictReader(inf, **csvopts)
            writer = csv.DictWriter(outf, fieldnames=flds, **csvopts)
            writer.writeheader()

            for row in reader:
                nlines += 1
                rec = build_video_record(row[CSV.COLNAME_PATH], photos)

                check_columns(rec.keys(), flds)
                for k,v in rec.items():
                    assert len(v.strip()) > 0, "empty column: {}".format(k)

                writer.writerow(rec)

    assert nlines == 30, "nlines: {}".format(nlines)
    print("file '{}' OK, {} lines processed".format(in_video, nlines))

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

def check_columns(cols, expected_cols):
    """Assert that cols list is equal expected_cols list
    """
    pairs = zip_longest(cols, expected_cols, fillvalue='oops')
    for c,e in pairs:
        assert c == e, "column {} != expected col {}".format(c, e)

def check_csv_file(fname, csvopts, exp_flds, exp_nrecs):
    """Check if file have all fields and values are not empty
    """
    nlines = 0
    with open(fname, newline='') as inf:
        reader = csv.DictReader(inf, **csvopts)
        for row in reader:
            nlines += 1
            assert len(row) == len(exp_flds), "len(row): {}".format(len(row))
            check_columns(row.keys(), exp_flds)
            for k,v in row.items():
                assert len(v.strip()) > 0, "empty column value: {}".format(k)

    assert nlines == exp_nrecs, "nlines: {}, should be {}".format(nlines, exp_nrecs)
    print("file '{}' OK, {} lines checked".format(fname, nlines))

def check_photos_sorted(photos):
    """Check if list is sorted by 'ts' attribute
    """
    ts = 0
    for photo in photos:
        assert photo['ts'] >= ts
        ts = photo['ts']

def split_n_trim(txt, sep='\n'):
    """Return list of non-empty strings from input splitted by blank chars
    """
    lst = txt.split(sep)
    return [x.strip() for x in lst if x.strip()]

def main():
    st = start_time()
    infile,outfile = sys.argv[1:3]
    normalize(infile, infile + '.with_ts')
    fillEmptyCoords(infile + '.with_ts', outfile)
    end_time(st)

if __name__ == "__main__":
    main()
