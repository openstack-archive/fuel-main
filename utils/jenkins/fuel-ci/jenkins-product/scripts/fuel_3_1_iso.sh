cd $WORKSPACE

# => why do we need this?! #!/bin/bash

export PATH=/bin:/usr/bin:/sbin:/usr/sbin:$PATH

export ISO_NAME=fuelweb-$branch-$BUILD_NUMBER-$BUILD_ID

make deep_clean

make $make_args img

md5sum build/iso/fuelweb-$branch-$BUILD_NUMBER-$BUILD_ID.iso build/iso/fuelweb-$branch-$BUILD_NUMBER-$BUILD_ID.img

mv build/iso/fuelweb-$branch-$BUILD_NUMBER-$BUILD_ID.iso /var/www/fuelweb-iso/
mv build/iso/fuelweb-$branch-$BUILD_NUMBER-$BUILD_ID.img /var/www/fuelweb-iso/

echo "<a href="http://`hostname -f`/fuelweb-iso/fuelweb-$branch-$BUILD_NUMBER-$BUILD_ID.iso">ISO download link</a>"
echo "<a href="http://`hostname -f`/fuelweb-iso/fuelweb-$branch-$BUILD_NUMBER-$BUILD_ID.img">IMG download link</a>"
