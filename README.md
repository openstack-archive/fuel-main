FUEL
====

This git repository contains Fuel ISO build scripts.

Directory structure:
- ```iso```
  Scripts that are used for building Fuel ISO.
- ```specs```
  RPM spec for fuel and fuel-release packages.
- ```Makefile```
  It is the main GNU Make file which includes all other necessary GNU Make files.
- ```prepare-build-env.sh```
  The script installs all necessary packages that are needed for the build process. Currently
  only Ubuntu 14.04 is supported.
