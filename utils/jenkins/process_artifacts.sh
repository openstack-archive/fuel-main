#!/bin/bash

set -x

usage(){
    echo "Usage: `basename $0` <artifact_file_name>"
    exit 1
}

if [ $# -ne 1 ] || [ ! -f "$1" ]
then
    usage
fi

# Defaults

LOCAL_STORAGE="/var/www/fuelweb-iso"

TRACKER_URL='http://seed-qa.msk.mirantis.net:8080/announce'
HOSTNAME=`hostname -f`
HTTP_ROOT="http://${HOSTNAME}/fuelweb-iso"


# Process artifact

ARTIFACT=$1

echo "MD5SUM is:"
md5sum $ARTIFACT

echo "SHA1SUM is:"
sha1sum $ARTIFACT

mkdir -p $LOCAL_STORAGE
mv $ARTIFACT $LOCAL_STORAGE

MAGNET_LINK=`seedclient.py -v -u -f "$LOCAL_STORAGE"/"$ARTIFACT" --tracker-url="${TRACKER_URL}" --http-root="${HTTP_ROOT}" || true`
HTTP_LINK="$HTTP_ROOT/$ARTIFACT"
HTTP_TORRENT="${HTTP_LINK}.torrent"

# Generate txt

echo "
ARTIFACT=$ARTIFACT
HTTP_LINK=$HTTP_LINK
HTTP_TORRENT=$HTTP_TORRENT
MAGNET_LINK=$MAGNET_LINK
" > $ARTIFACT.data.txt

# Generate html

echo "
<h1>$ARTIFACT</h1>
<a href=\"$HTTP_LINK\">HTTP link</a><br>
<a href=\"$HTTP_TORRENT\">Torrent file</a><br>
<a href=\"$MAGNET_LINK\">Magnet link</a><br>
" > $ARTIFACT.data.html
