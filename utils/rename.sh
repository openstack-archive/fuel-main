#!/bin/bash

usage(){
    echo "Usage: `basename $0` <project_root_dir> <old_string> <new_string>"
    exit 1
}

if [ $# -ne 3 ]; then
    usage
fi

(
    cd $1
    old=$2
    new=$3
    grep -r $old * 2>/dev/null | awk -F: '{print $1}' | sort | uniq | while read file; do
        echo "sed -i -e \"s/${old}/${new}/g\" $file"
        sed -i -e "s/${old}/${new}/g" $file
    done

    find -name "*${old}*" | sort -r | while read oldfile; do
        d=`dirname $oldfile`
        f=`basename $oldfile`
        newfile=${d}/`echo $f | sed -e "s/${old}/${new}/g"`
        echo "mv $oldfile $newfile"
        mv $oldfile $newfile
    done
)
