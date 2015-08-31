#!/bin/bash
drives=""
removable_drives=""
for drv in `ls -1 /sys/block | grep "sd\|hd\|vd\|cciss"`; do
    if !(blkid | grep -q "${drv}.*Fuel"); then
      if (grep -q 0 /sys/block/${drv}/removable); then
          drives="${drives} ${drv}"
      else
          removable_drives="${removable_drives} ${drv}"
      fi
    fi
done

echo $drives
