#!/usr/bin/env bash
set -eux -o pipefail

export PYTHONIOENCODING=UTF-8
python -u geocode.py norm_data_tab.csv map_markers_data.csv
