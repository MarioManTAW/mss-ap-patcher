#!/bin/sh
if [ -z "$1" ]
then
    echo "No patch file specified. Aborting."
elif [ ! -f "$1" ]
then
    echo "Specified patch file appears not to exist. Aborting."
else
    bin/wit extract -s vanilla -D tmp -o
    python3 patcher.py $1
    bin/wit copy tmp -o ${1%.*}.wbfs
    rm -rf tmp
fi