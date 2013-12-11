cd $WORKSPACE

export PATH=/bin:/usr/bin:/sbin:/usr/sbin:$PATH

export ISO_NAME=fuel-$BUILD_NUMBER-$BUILD_ID

make deep_clean

make $make_args img

md5sum build/iso/fuel-$BUILD_NUMBER-$BUILD_ID.iso build/iso/fuel-$BUILD_NUMBER-$BUILD_ID.img
mv build/iso/fuel-$BUILD_NUMBER-$BUILD_ID.iso /var/www/fuelweb-iso/
mv build/iso/fuel-$BUILD_NUMBER-$BUILD_ID.img /var/www/fuelweb-iso/

# dpyzhov comment:
# we need to clean up build because jenkins cannot wipe out workspace if it contains superuser files
# and we need to wipe out workspace because jenkins does not ever update origin url after checkout
# and we want to allow users to build from their own repos
make deep_clean

echo "<a href="http://`hostname -f`/fuelweb-iso/fuel-$BUILD_NUMBER-$BUILD_ID.iso">ISO download link</a>"
echo "<a href="http://`hostname -f`/fuelweb-iso/fuel-$BUILD_NUMBER-$BUILD_ID.img">IMG download link</a>"
