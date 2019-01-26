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
    python -u normcsv.py photo_data_tab.csv video_data_tab.csv norm_data_tab.csv
"""

import sys
import time
import csv
import math

from collections import OrderedDict
from itertools import zip_longest
from datetime import datetime, timedelta


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

def split_n_trim(txt, sep='\n'):
    """Return list of non-empty strings from input splitted by blank chars
    """
    lst = txt.split(sep)
    return [x.strip() for x in lst if x.strip()]

def normalize_row(row, columns):
    """Return OrderedDict where keys list == columns and values normalized

SourceFile => Composite:SubSecDateTimeOriginal

.../P81028-105149.jpg => 2018:10:28 11:51:49.87
.../P81028-083502.jpg => 1028-083502 => 2018:10:28 08:35:02 => 2018:10:28 09:35:02.00
    """
    dtf = datetime_format()['format']
    dtl = datetime_format()['len']

    def fts2dts(fts):
        dt = datetime.strptime(fts, '%Y%m%d-%H%M%S')
        return (dt + timedelta(minutes=30)).strftime(dtf)[:dtl]

    def dateTimeFromFileName(fname):
        parts = split_n_trim(fname, '/')
        lastPart = parts[-1]
        fts = (lastPart[2:])[0:-4]
        dts = fts2dts('2018'+fts)
        print("timestamp from filename: {} => {}".format(fts, dts))
        return dts

    def normalize_value(colname, colvalue):
        val = colvalue.strip()
        if val == '' and colname == 'Composite:SubSecDateTimeOriginal':
            val = dateTimeFromFileName(row['SourceFile'].strip())

        return (colname, val)

    return OrderedDict([
        normalize_value(k,row.get(k, '')) for k in columns
    ])

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

def norm_photo(infile='in_test.csv', outfile='out_test.csv'):
    """Write selected fields, empty values replaced with data from nearest records
    """
    csvopts = csv_options()
    flds = list_out_fields()

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

    assert nlines == 2623, "nlines: {}".format(nlines)
    print("file '{}' OK, {} lines readed".format(infile, nlines))
    # check writed file, optional
    #~ check_csv_file(outfile, csvopts, flds, 2622)

def load_photos(infile):
    """Load photos to sorted array. Sort by time attribute
    """
    dtf = datetime_format()['format']
    dtl = datetime_format()['len']

    def dt2ts(dts):
        dt = datetime.strptime(dts, dtf)
        ts = dt.timestamp()
        assert dts == datetime.fromtimestamp(ts).strftime(dtf)[:dtl]
        return ts

    def new_photo(rec):
        return {
            'ts' : dt2ts(rec['Composite:SubSecDateTimeOriginal']),
            'alt': rec['Composite:GPSAltitude'],
            'lat': rec['Composite:GPSLatitude'],
            'lon': rec['Composite:GPSLongitude']
        }

    photos = []
    csvopts = csv_options()
    with open(infile, newline='') as inf:
        reader = csv.DictReader(inf, **csvopts)
        for row in reader:
            obj = new_photo(row)
            photos.append(obj)

    return sorted(photos, key=lambda x: x['ts'])

def check_photos_sorted(photos):
    """Check if list is sorted by 'ts' attribute
    """
    ts = 0
    for photo in photos:
        assert photo['ts'] >= ts
        ts = photo['ts']

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

    dtf = datetime_format()['format']
    dtl = datetime_format()['len']

    rec['SourceFile'] = video_fname
    rec['Composite:GPSAltitude'] = photo['alt']
    rec['Composite:GPSLatitude'] = photo['lat']
    rec['Composite:GPSLongitude'] = photo['lon']
    rec['Composite:SubSecDateTimeOriginal'] = datetime.fromtimestamp(ts).strftime(dtf)[:dtl]
    return rec

def norm_video(in_video, in_photo, outfile):
    """Copy coords to video record from nearest photo
    """
    csvopts = csv_options()
    flds = list_out_fields()

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
                rec = build_video_record(row['SourceFile'], photos)

                check_columns(rec.keys(), flds)
                for k,v in rec.items():
                    assert len(v.strip()) > 0, "empty column: {}".format(k)

                writer.writerow(rec)

    assert nlines == 30, "nlines: {}".format(nlines)
    print("file '{}' OK, {} lines processed".format(in_video, nlines))

def union_csv(first_infile, second_infile, outfile):
    """Union two csv files
    """
    first_nlines, second_nlines = 0, 0
    with open(outfile, 'w', newline='\r\n') as outf:
        with open(first_infile) as inf:
            for line in inf:
                first_nlines +=1
                outf.write(line)
        with open(second_infile) as inf:
            for line in inf:
                second_nlines += 1
                if second_nlines > 1:
                    outf.write(line)

    assert first_nlines + second_nlines == 1302 + 30 + 1 + 1
    print("file '{}' should be OK, {} + {} lines processed".format(outfile, first_nlines, second_nlines))

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
    photo,video,outfile = sys.argv[1:4]
    norm_photo(photo, photo + '.norm')
    norm_video(video, photo + '.norm', video + '.norm')
    union_csv(photo + '.norm', video + '.norm', outfile)
    end_time(st)

if __name__ == "__main__":
    main()
