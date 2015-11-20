FUEL
====

This git repository contains Fuel ISO build scripts.

Directory structure:
- ```bootstrap```
  Scripts for building CentOS based bootstrap ramdisk. The Fuel discovery
  agent (nailgun-agent) and Fuel operating system provisioning agent (fuel-agent)
  are installed into this ramdisk.
- ```docker```
  Scripts for building Docker containers are located. The Fuel
  master node is deployed using Docker. Every Fuel major component like Nailgun, Astute,
  Cobbler, Mcollective, etc. is installed as a separate Docker container.
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
- ```virtualbox```
  Scripts that allow a user to try Fuel easily. Being run they start several virtual box
  VMs. One of them is used for the Fuel master node and others are used as slave nodes
  where Fuel installs an operating system and deploys OpenStack.
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
- ```virtualbox.mk```
  The script that is used for preparing tarball archive with virtualbox scripts.
