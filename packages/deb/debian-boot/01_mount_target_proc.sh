#!/bin/sh
# Work around the kernel (linux-image-3.13.0) installation failure.
# The pre-install script tries to check if the CPU can actually run
# a 64-bit kernel. That script checks for CPU features via /proc/cpuinfo
# without checking if /proc is mounted.
# As a work around put this script into /usr/lib/post-base-installer.d
# directory so that debian-installer calls it before attempting to install
# the kernel package.
if [ ! -d /target/proc/1 ]; then
    mkdir -p /target/proc
    mount -t proc proc /target/proc
fi
