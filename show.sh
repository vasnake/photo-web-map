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
            dumpInfo "${__dir}/usa-ph" "${__dir}/usa-vid"
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
    echo sudo docker build --rm \
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

dumpInfo() {
    local photosDir=${1}
    local videoDir=${2}

    # tags list
    #~ -a          (-duplicates)        Allow duplicate tags to be extracted
    #~ -G[NUM...]  (-groupNames)        Print group name for each tag
    #~ -s[NUM]     (-short)             Short output format
    #~ -n          (--printConv)        No print conversion
    echo Image-ExifTool-11.16/exiftool -a -G1 -s -n ${photosDir}/IMG_20181007_130100.jpg

    # export jpg metadata to csv
    #~ Image-ExifTool-11.16/exiftool -a -G1 -s -n -csv "${photosDir}" > "${__dir}/photo_data_tab.csv"

    # export mp4 metadata to csv
    #~ echo "SourceFile" > "${__dir}/video_data_tab.csv"
    #~ ls -rt -d -1 "${videoDir}"/* >> "${__dir}/video_data_tab.csv"

    # create thumbnails
    if [ "$(ls -1 thumb | wc -l)" != "1332" ]; then
        mkdir -p thumb
        pushd ${photosDir}
        for fn in IMG*.jpg; do
            convert -thumbnail 200 ${fn} thumb-${fn};
        done;
        popd
        mv -v ${photosDir}/thumb-*.jpg thumb/

        pushd ${videoDir}
        for fn in VID*.mp4; do
            ffmpeg -i ${fn} -y -an -ss 00:00:01 -vcodec png -r 1 -vframes 1 -s 256x144 thumb-${fn}.png
            convert thumb-${fn}.png thumb-${fn%%.*}.jpg
            rm thumb-${fn}.png
        done;
        popd
        mv -v ${videoDir}/thumb-*.jpg thumb/
    fi

    # docker root problem workaround for generated files
    setfacl -m "default:group::rwx" "${__dir}"

    # normalize dataset: select columns subset; replace null values with default values;
    # union with video data, interpolate video lon,lat from nearest photo
    echo sudo docker run -it --rm \
        --name csv-py \
        -v "${__dir}":/usr/src/project \
        -w /usr/src/project \
        ${DOCKERIMAGE} \
        bash normcsv.sh

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

    sudo docker run -it --rm \
        --name geocode-py \
        -v "${__dir}":/usr/src/project \
        -w /usr/src/project \
        ${DOCKERIMAGE} \
        bash geocode.sh

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

    # check CRLF
    file "${data}"
    unix2dos -n "${data}" ${data}.dos

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
