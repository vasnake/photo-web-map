#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Valik mailto:vasnake@gmail.com

"""
Purpose: test python setup

Expected usage:

    docker run -it --rm \
        --name test-python \
        -v "${__dir}":/usr/src/project \
        -w /usr/src/project \
        python:3.7.1 python test.py
"""

import time

start_ns = time.time_ns()
print("start, nanoseconds from epoch: {}".format(start_ns))

import sys

def main():
    print("python version: {}".format(sys.version))
    assert sys.version_info >= (3, 7, 1)

if __name__ == "__main__":
    # execute only if run as a script
    main()

end_ns = time.time_ns()
dur_ns = end_ns - start_ns
print("end, nanoseconds from epoch: {}; duration: {} nanoseconds or {} microseconds".format(end_ns, dur_ns, dur_ns / 1000))
