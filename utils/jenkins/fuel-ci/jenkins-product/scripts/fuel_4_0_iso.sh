cd $WORKSPACE

export PATH=/bin:/usr/bin:/sbin:/usr/sbin:$PATH

export ISO_NAME=fuel-4.0-$BUILD_NUMBER-$BUILD_ID

export BUILD_DIR=../tmp/$(basename $(pwd))/build
export LOCAL_MIRROR=../tmp/$(basename $(pwd))/local_mirror

make deep_clean

make $make_args img

md5sum $BUILD_DIR/iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.iso $BUILD_DIR/iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.img

echo "MD5SUM is:"
md5sum $BUILD_DIR/iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.iso || true
md5sum $BUILD_DIR/iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.img || true

echo "MD5SUM is:"
sha1sum $BUILD_DIR/iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.iso || true
sha1sum $BUILD_DIR/iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.img || true


mv $BUILD_DIR/iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.iso /var/www/fuelweb-iso/
mv $BUILD_DIR/iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.img /var/www/fuelweb-iso/

export TRACKER_URL='http://seed-qa.msk.mirantis.net:8080/announce'
ISO_MAGNET_LINK=`seedclient.py -v -u -f /var/www/fuelweb-iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.iso || true`
IMG_MAGNET_LINK=`seedclient.py -v -u -f /var/www/fuelweb-iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.img || true`

# dpyzhov comment: let's use less space for our jobs
make deep_clean

echo "<a href="http://`hostname -f`/fuelweb-iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.iso">ISO download link</a> <a href="http://`hostname -f`/fuelweb-iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.iso.torrent">ISO torrent link</a>"
echo "<a href="http://`hostname -f`/fuelweb-iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.img">IMG download link</a> <a href="http://`hostname -f`/fuelweb-iso/fuel-4.0-$BUILD_NUMBER-$BUILD_ID.img.torrent">IMG torrent link</a>"
