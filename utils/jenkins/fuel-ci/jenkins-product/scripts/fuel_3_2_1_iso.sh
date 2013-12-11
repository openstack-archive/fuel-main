cd $WORKSPACE

export PATH=/bin:/usr/bin:/sbin:/usr/sbin:$PATH

export ISO_NAME=fuel-3.2.1-$BUILD_NUMBER-$BUILD_ID

export BUILD_DIR=../tmp/$(basename $(pwd))/build
export LOCAL_MIRROR=../tmp/$(basename $(pwd))/local_mirror

make deep_clean

make $make_args img

md5sum $BUILD_DIR/iso/fuel-3.2.1-$BUILD_NUMBER-$BUILD_ID.iso $BUILD_DIR/iso/fuel-3.2.1-$BUILD_NUMBER-$BUILD_ID.img

seedclient.py -v -u -f $BUILD_DIR/iso/fuel-3.2.1-$BUILD_NUMBER-$BUILD_ID.iso --seed-host=172.18.23.22 --seed-port=17333 || true

mv $BUILD_DIR/iso/fuel-3.2.1-$BUILD_NUMBER-$BUILD_ID.iso /var/www/fuelweb-iso/
mv $BUILD_DIR/iso/fuel-3.2.1-$BUILD_NUMBER-$BUILD_ID.img /var/www/fuelweb-iso/

# dpyzhov comment: let's use less space for our jobs
make deep_clean

echo "<a href="http://`hostname -f`/fuelweb-iso/fuel-3.2.1-$BUILD_NUMBER-$BUILD_ID.iso">ISO download link</a>"
echo "<a href="http://`hostname -f`/fuelweb-iso/fuel-3.2.1-$BUILD_NUMBER-$BUILD_ID.img">IMG download link</a>"
