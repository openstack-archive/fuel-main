#!/bin/bash
cd /repo
for deb in $(find /var/cache/apt -name \*deb); do 
	reprepro includedeb precise $deb
done
