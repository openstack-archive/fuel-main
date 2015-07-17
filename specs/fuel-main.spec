#TEMP fixme
%define repo_name fuel-main

%define name fuel
%{!?version: %define version 7.0.0}
%{!?release: %define release 1}

Name: %{name}
Summary: Fuel for OpenStack
URL:     http://mirantis.com
Version: %{version}
Release: %{release}
License: Apache
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Requires: fuel-bootstrap-image >= %{version}
Requires: fuel-dockerctl >= 7.0
Requires: fuel-docker-images >= %{version}
Requires: fuel-library7.0
Requires: fuelmenu >= %{version}
Requires: fuel-package-updates >= %{version}
Requires: fuel-provisioning-scripts >= %{version}
Requires: fuel-target-centos-images >= %{version}
Requires: nailgun-net-check >= %{version}
Requires: python-fuelclient >= %{version}
Requires: yum

%description
Fuel for OpenStack is a lifecycle management utility for
managing OpenStack.

%files
%defattr(-,root,root)
