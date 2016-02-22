FUEL
====

This git repository contains Fuel ISO build scripts.

Directory structure:
- ```fuel-bootstrap-image```
  Scripts which allow us to build Ubuntu based bootstrap ramdisk on the
  Fuel master node in runtime. The status of this ramdisk is experimental.
- ```iso```
  Scripts that are used for building Fuel ISO.
- ```mirror```
  Scripts to build local mirrors that are used for building chroot environments, bootstrap and
  target images, etc.
- ```packages```
  Scripts that are used for building Fuel RPM and DEB packages.
- ```specs```
  RPM spec for fuel and fuel-release packages.
- ```utils```
  Auxiliary scripts. (being deprecated)
- ```Makefile```
  It is the main GNU Make file which includes all other necessary GNU Make files.
- ```config.mk```
  The file where the whole build process is parametrized.
- ```prepare-build-env.sh```
  The script installs all necessary packages that are needed for the build process. Currently
  only Ubuntu 14.04 is supported.
- ```repos.mk```
  The script which downloads git repositories that are needed for the build process.
- ```requirements-rpm.txt```
  This file is used when building local RPM mirror. All RPM packages that are needed for Fuel
  are listed here.
- ```sandbox.mk```
  The script that is used for building chroot environments.
