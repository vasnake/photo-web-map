#!/usr/bin/env bash
# -*- mode: shell; coding: utf-8 -*-
# (c) Valik mailto:vasnake@gmail.com
#
# Purpose
# Prepare and run show builded from photos/videos taken on usa-trip-2018
#
# Expected usage:
#   show.sh dumpInfo
#   show.sh geocode
#   show.sh map
#
################################################################################
# What do I want
#
#~ хочу смотреть фотки по дате, локации
#~ в идеале: три фильтра: дата, штат, город; отфильтрованный список фоток выводится на карту
#
#~ из фоток надо вынуть: имя файла; дата-время съемки; координаты
#~ https://photo.stackexchange.com/questions/24747/is-there-a-free-piece-of-software-that-will-export-metadata-for-a-folder-full-of
#~ ~/Downloads/Image-ExifTool-11.16/exiftool -a -G1 -s -n ~/Downloads/usa-ph/IMG_20181007_130100.jpg
#
#~ координаты надо геокодировать в названия штата, ближайшего города
#
#~ таблицу атрибутов засунуть в серверлесс аппликуху, выводящую отфильтрованные фотки
################################################################################

# http://kvz.io/blog/2013/11/21/bash-best-practices/

# Use set -o pipefail in scripts to catch mysqldump fails in e.g. mysqldump | gzip.
# The exit status of the last command that threw a non-zero exit code is returned
set -o pipefail

# Use set -o errexit (a.k.a. set -e) to make your script exit when a command fails
# Then add || true to commands that you allow to fail
#~ set -o errexit

# Use set -o nounset (a.k.a. set -u) to exit when your script tries to use undeclared variables
#~ set -o nounset

# Use set -o xtrace (a.k.a set -x) to trace what gets executed. Useful for debugging
set -o xtrace

# Surround your variables with {}.
# Otherwise bash will try to access the $ENVIRONMENT_app variable in /srv/$ENVIRONMENT_app,
# whereas you probably intended /srv/${ENVIRONMENT}_app

# Surround your variable with " in if [ "${NAME}" = "Kevin" ],
# because if $NAME isn't declared, bash will throw a syntax error (also see nounset)

# Set magic variables for current file, basename, and directory at the top of your script for convenience
__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__root="$(cd "$(dirname "${__dir}")" && pwd)" # <-- change this
__file="${__dir}/$(basename "${BASH_SOURCE[0]}")"
__base="$(basename ${__file} .sh)"

__arg1="${1:-}"
__arg2="${2:-}"
__args=($@)
__argsLen=${#@}

################################################################################

DOCKERIMAGE="python/3.7.1/geocsv:0.1"

main() {
    echo -e "timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"

    if [ ${__argsLen} -ge 1 ]; then
        if [ "${__arg1}" = "dumpInfo" ]; then

          dumpInfo /home/valik/bigone/photo/2018-10-usa/db \
            /home/valik/bigone/photo/2018-10-usa/images/thumb \
            /home/valik/bigone/photo/2018-10-usa/images/usa-ph \
            /home/valik/bigone/photo/2018-10-usa/images/usa-vid \
            /mnt/sdb1/America/nf \
            /mnt/sdb1/America/usa-ph.nat \
            /mnt/sdb1/America/usa-vid.nat

        elif [ "${__arg1}" = "geocode" ]; then
            geocode
        elif [ "${__arg1}" = "map" ]; then
            runMap
        elif [ "${__arg1}" = "setupPython" ]; then
            setupPython
        elif [ "${__arg1}" = "removeDockerImages" ]; then
            removeDockerImages
        else
            errorExit "Unknown command: '${__arg1}'"
        fi
    else
        errorExit "You have to pass parameters. See ${__file} source code."
    fi
}

removeDockerImages() {
    sudo docker image ls -a
    sudo docker ps -q -a | xargs sudo docker stop
    sudo docker ps -q -a | xargs sudo docker rm
    sudo docker image rm $(sudo docker image ls -a -q)
    sudo docker image ls -a
}

setupPython() {
#~ https://hub.docker.com/r/library/python/
#~ https://hub.docker.com/_/python/
#~ https://docs.docker.com/get-started/part2/#recap-and-cheat-sheet-optional

    # docker?
    if [ ! command -v docker 1>/dev/null 2>&1 ]; then
        echo "docker is not installed" >&2

    #~ https://docs.docker.com/install/linux/docker-ce/debian/#uninstall-old-versions
        sudo apt-get remove docker docker-engine docker.io

    #~ https://docs.docker.com/install/linux/docker-ce/debian/#install-using-the-repository
        sudo apt-get install \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg2 \
            software-properties-common

        curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
        sudo apt-key fingerprint 0EBFCD88 | grep Docker

        sudo add-apt-repository \
            "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"

        sudo apt-get update
        sudo apt-get install docker-ce
    fi

    # check docker setup
    sudo docker image ls -a
    echo sudo docker run hello-world

    # docker root problem workaround for generated files
    setfacl -m "default:group::rwx" "${__dir}"

    # check python in docker
#~ -i, --interactive                    Keep STDIN open even if not attached
#~ -t, --tty                            Allocate a pseudo-TTY
#~ --rm                             Automatically remove the container when it exits
#~ --name string                    Assign a name to the container
#~ -v, --volume list                    Bind mount a volume
#~ -w, --workdir string                 Working directory inside the container
    echo sudo docker run -it --rm \
        --name test-python \
        -v "${__dir}":/usr/src/project \
        -w /usr/src/project \
        python:3.7.1 \
        python test.py

    # build image with needed modules
    sudo docker build --rm \
        -t ${DOCKERIMAGE} docker

    # check python modules setup
    sudo docker run -it --rm \
        --name test-python \
        -v "${__dir}":/usr/src/project \
        -w /usr/src/project \
        ${DOCKERIMAGE} \
        python test_modules.py

    sudo docker image ls -a
}

setupPyenvPython() {
# can't do: compile python step failed
# fuck it anyway, docker rulezz

    PYENV_ROOT="${HOME}/.pyenv"
    PYTHON_VERSION=3.7.1
    #~ PYTHON_VERSION=2.7.15
    PIP_VERSION=18.1
    PIPENV_VERSION=2018.11.14
    PYTHON_HOME="${PYENV_ROOT}/versions/${PYTHON_VERSION}"

    # setup pyenv:

    if ! command -v pyenv 1>/dev/null 2>&1; then
        echo "pyenv is not installed" >&2

        sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
            libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
            xz-utils tk-dev libffi-dev liblzma-dev

        curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash

        echo "export PATH=\"${PYENV_ROOT}/bin:\$PATH\"" >> ~/.bash_profile
        echo "eval \"\$(pyenv init -)\"" >> ~/.bash_profile
        echo "eval \"\$(pyenv virtualenv-init -)\"" >> ~/.bash_profile
        source ~/.bash_profile
    fi

    pyenv update

    # remove pyenv:
    #~ rm -fr ~/.pyenv
    # remove these three lines from ~/.bash_profile:
    #~ export PATH="~/.pyenv/bin:$PATH"
    #~ eval "$(pyenv init -)"
    #~ eval "$(pyenv virtualenv-init -)"

    # setup python+pipenv:

    pyenv install ${PYTHON_VERSION}

#~ Installing Python-3.7.1...
#~ ERROR: The Python ssl extension was not compiled. Missing the OpenSSL lib?
#~ Please consult to the Wiki page to fix the problem.
#~ https://github.com/pyenv/pyenv/wiki/Common-build-problems
#~ BUILD FAILED (Debian 8.8 using python-build 1.2.8)

    if [ ! -d "${PYTHON_HOME}/bin" ]; then
        errorExit "pyenv python not installed"
    fi

    pushd ${PYTHON_HOME}/bin
    ./pip install pip==${PIP_VERSION}
    ./pip install pipenv==${PIPENV_VERSION}
    popd

    # setup module env:

    ${PYTHON_HOME}/bin/pipenv install --python ${PYTHON_HOME}/bin/python
    # show env path
    ${PYTHON_HOME}/bin/pipenv --venv # "${HOME}/.local/share/virtualenvs/pipeline-UW9DiJCo/bin/python"

    # install module:

    #${PYTHON_HOME}/bin/pipenv install -e . --dev --skip-lock
    #${PYTHON_HOME}/bin/pipenv install pytest==3.4.2 --dev --skip-lock
    #${PYTHON_HOME}/bin/pipenv install twine==1.10.0 --dev --skip-lock
    #${PYTHON_HOME}/bin/pipenv install wheel==0.30.0 --dev --skip-lock

    # run tests:

    # https://docs.pytest.org/en/latest/usage.html
    #${PYTHON_HOME}/bin/pipenv run pytest -vv --junitxml=./test-report
    #${PYTHON_HOME}/bin/pipenv run pytest -vv -s -x
}

dumpVideoCodec() {
    local videoDir=${1}
    local tag=${2}

    echo "SourceFile,codec" > "${__dir}/videocodec_${tag}_tab.csv"

    pushd ${videoDir}
    for fn in *.mp4; do
        codec=$(ffprobe -v error -select_streams v:0 \
            -show_entries stream=codec_name \
            -of default=noprint_wrappers=1:nokey=1 \
            ${fn})
        echo "${videoDir}/${fn},${codec}" >> "${__dir}/videocodec_${tag}_tab.csv"
    done;
    popd
}

encodeToH264() {
    # https://gist.github.com/Vestride/278e13915894821e1d6f
    local videoDir=${1}
    pushd ${videoDir}
    for fn in V81011-095508.mp4 V81031-115234.mp4 V81031-150724.mp4; do
        echo "encode '${fn}' to h264 ..."
        ffmpeg -i "${fn}" -vcodec h264 -acodec aac -crf 18 "${fn}_h264.mp4"
    done;
    popd
}

dumpInfo() {

#          dumpInfo /home/valik/bigone/photo/2018-10-usa/db/ \
#            /home/valik/bigone/photo/2018-10-usa/images/thumb \
#            /home/valik/bigone/photo/2018-10-usa/images/usa-ph \
#            /home/valik/bigone/photo/2018-10-usa/images/usa-vid \
#            /mnt/sdb1/America/nf \
#            /mnt/sdb1/America/usa-ph.nat \
#            /mnt/sdb1/America/usa-vid.nat

            #~ dumpVideoCodec "${__dir}/usa-vid" "data1"
            #~ dumpVideoCodec "${__dir}/usa-vid.nat" "data2"
            #~ encodeToH264 "${__dir}/usa-vid.nat"

#            dumpInfo "${__dir}/usa-ph" "${__dir}/usa-vid" "data1"
#            dumpInfo "${__dir}/usa-ph.nat" "${__dir}/usa-vid.nat" "data2"
#            mergeAndNormalize "data1" "data2"

  echo list of dirs: "$*"
  # first: database dir
  # second: thumbnails dir
  # all other: photo and video dirs

  pushd ${__dir}
  python -u collect_csv.py "$@"
  popd
  exit 1

    local photosDir=${1}
    local videoDir=${2}
    local tag=${3}

    # tags list
    #~ -a          (-duplicates)        Allow duplicate tags to be extracted
    #~ -G[NUM...]  (-groupNames)        Print group name for each tag
    #~ -s[NUM]     (-short)             Short output format
    #~ -n          (--printConv)        No print conversion
    echo Image-ExifTool-11.16/exiftool -a -G1 -s -n ${photosDir}/IMG_20181007_130100.jpg

    # export jpg metadata to csv
    Image-ExifTool-11.16/exiftool -a -G1 -s -n -csv "${photosDir}" > "${__dir}/photo_${tag}_tab.csv"

    # export mp4 metadata to csv
    echo "SourceFile" > "${__dir}/video_${tag}_tab.csv"
    ls -rt -d -1 "${videoDir}"/* >> "${__dir}/video_${tag}_tab.csv"

    # create thumbnails # 2691 = 1302 + 30 + 1320 + 39
    if [ "$(ls -1 thumb | wc -l)" != "2691" ]; then
        mkdir -p thumb
        pushd ${photosDir}
        mkdir -p tmp
        for fn in *.jpg; do
            convert -thumbnail 200 ${fn} tmp/thumb-${fn};
        done;
        popd
        mv -v ${photosDir}/tmp/thumb-*.jpg thumb/

        pushd ${videoDir}
        for fn in *.mp4; do
            ffmpeg -i ${fn} -y -an -ss 00:00:01 -vcodec png -r 1 -vframes 1 -s 256x144 thumb-${fn}.png
            convert thumb-${fn}.png thumb-${fn%%.*}.jpg
            rm thumb-${fn}.png
        done;
        popd
        mv -v ${videoDir}/thumb-*.jpg thumb/
    fi
}

mergeAndNormalize() {
    local tag1=${1}
    local tag2=${2}

    # docker root problem workaround for generated files
    setfacl -m "default:group::rwx" "${__dir}"

    # select columns that needed for downstream processing
    for tag in $tag1 $tag2; do
        for part in "photo" "video"; do
            sudo docker run -it --rm \
                --name project-py \
                -v "${__dir}":/usr/src/project \
                -w /usr/src/project \
                ${DOCKERIMAGE} \
                python -u project_csv.py \
                "${part}_${tag}_tab.csv" "${part}_${tag}_tab_projected.csv"
        done;
    done;

    # merge photo data
    cat         "${__dir}/photo_${tag1}_tab_projected.csv" >  "${__dir}/photo_video_data_tab.csv"
    tail -n +2  "${__dir}/photo_${tag2}_tab_projected.csv" >> "${__dir}/photo_video_data_tab.csv"
    # merge video data
    tail -n +2  "${__dir}/video_${tag1}_tab_projected.csv" >> "${__dir}/photo_video_data_tab.csv"
    tail -n +2  "${__dir}/video_${tag2}_tab_projected.csv" >> "${__dir}/photo_video_data_tab.csv"

    # normalize dataset: select columns subset; replace null values with calculated values
    sudo docker run -it --rm \
        --name norm-py \
        -v "${__dir}":/usr/src/project \
        -w /usr/src/project \
        ${DOCKERIMAGE} \
        python -u normcsv.py \
            photo_video_data_tab.csv norm_data_tab.csv

    # output: norm_data_tab.csv
}

geocode() {
    local data="norm_data_tab.csv"
    echo "getting USA state name and city name for lon,lat coords from '${data}'"

read -r -d '' MSG << EOF
    The term geocoding generally refers to translating a human-readable address into a location on a map.
    The process of doing the opposite, translating a location on the map into a human-readable address,
    is known as reverse geocoding
EOF

    echo ${MSG}

    # docker root problem workaround for generated files
    setfacl -m "default:group::rwx" "${__dir}"

    sudo docker run -it --rm \
        --name geocode-py \
        -v "${__dir}":/usr/src/project \
        -w /usr/src/project \
        ${DOCKERIMAGE} \
        python -u geocode.py \
            norm_data_tab.csv map_markers_data.csv

    # output: map_markers_data.csv
}

runMap() {
    local data="map_markers_data.csv"

read -r -d '' MSG << EOF
    Show a map, interactive web-map, with a set of markers.
    Each marker represents a photo, photo should be displayed by clicking on a corresponding marker.
    Markers should be filtered by three conditions: date, state name, town name.

    https://github.com/turban/Leaflet.Photo
    https://github.com/joker-x/Leaflet.geoCSV
    https://gis.stackexchange.com/questions/190773/how-to-display-geotagged-photos-from-my-domain-in-leaflet

EOF

    echo ${MSG}

    # sort
    head -n 1 ${data} > ${data}.sorted
    tail -n +2 ${data} | sort >> ${data}.sorted

    # check CRLF
    file "${data}.sorted"
    unix2dos -n "${data}.sorted" "${data}.dos"

    /opt/firefox/firefox ./map.html
    #~ /opt/google/chrome/chrome --args --allow-file-access-from-files ./map.html
}

errorExit() {
    echo "$1" 1>&2
    exit 1
}

################################################################################

main

if [ "$?" = "0" ]; then
    echo "OK, command executed"
    exit 0
else
    errorExit "ERROR, can't do"
fi
