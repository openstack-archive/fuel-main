#!/bin/sh

while getopts "d:" opt; do
    case $opt in
        d)
            DATA_DIR="${OPTARG}"
            ;;
        :)
            echo "Option -$OPTARG requires an argument."
            exit 2
            ;;
    esac
done

if [ -z "${DATA_DIR}" ]; then
    echo "Error! DATA_DIR is not set! use -d option"
    exit 1
fi

DATA_FILE="$DATA_DIR"/data.json

if [ ! -e "$DATA_FILE" ] ; then
    touch "$DATA_FILE"
fi

if [ ! -w "$DATA_FILE" ] ; then
    echo cannot write to $DATA_FILE
    exit 1
fi

echo -n "[" > $DATA_FILE

first=1
for entry in "$DATA_DIR"/*
do
    if [ -f "$entry" ];then
        filename=$(basename "$entry")
        extension="${filename##*.}"
        filename="${filename%.*}"

        if [ "${extension}" != "json" ]; then
            continue
        fi

        if [ "${filename}" = "data" ]; then
            continue
        fi
        if [ $first -ne 1 ]; then
            echo "," >> $DATA_FILE
        else
            first=0
        fi
        cat ${entry} >> $DATA_FILE
    fi
done

echo -n "]" >> $DATA_FILE