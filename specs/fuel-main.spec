#TEMP fixme
%define repo_name fuel-main

%define version 6.1.0
%define release 1

%package -n fuel-release
Summary: Fuel for OpenStack
Version: %{version}
Release: %{release}
License: Apache
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Requires: fuel-bootstrap-image >= %{version}
Requires: fuel-dockerctl >= 6.1
Requires: fuel-docker-images >= %{version}
Requires: fuel-library >= 6.1
Requires: fuelmenu >= %{version}
Requires: fuel-package-updates >= %{version}
Requires: fuel-provisioning-scripts >= %{version}
Requires: fuel-target-centos-images >= %{version}
Requires: nailgun-net-check >= %{version}
Requires: python-fuelclient >= %{version}
Requires: yum

%description -n fuel-release
Fuel for OpenStack is a lifecycle management utility for
managing OpenStack.

%files -n fuel-release
%defattr(-,root,root)
