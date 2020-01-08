#!/usr/bin/env bash
set -eux -o pipefail
export PYTHONIOENCODING=UTF-8

python -u normcsv.py \
    photo_data_tab.csv video_data_tab.csv \
    norm_data_tab.csv
