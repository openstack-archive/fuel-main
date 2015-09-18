#TEMP fixme
%define repo_name fuel-main

%define name fuel
%{!?version: %define version 1.0.0}
%{!?fuel_release: %define fuel_release 1.0}
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
Requires: fuel-dockerctl >= %{fuel_release}
Requires: fuel-docker-images >= %{version}
Requires: fuel-library%{fuel_release}
Requires: fuelmenu >= %{version}
Requires: fuel-package-updates >= %{version}
Requires: fuel-provisioning-scripts >= %{version}
Requires: fuel-release >= %{version}
Requires: fuel-target-centos-images6.6 >= %{version}
Requires: nailgun-net-check >= %{version}
Requires: python-fuelclient >= %{version}
Requires: yum

%description
Fuel for OpenStack is a lifecycle management utility for
managing OpenStack.

%install
mkdir -p %{buildroot}/etc
echo %{fuel_release} > %{buildroot}%{_sysconfdir}/fuel_release

%files
%defattr(-,root,root)

%package -n fuel-release

Summary:   Fuel release package
Version:   %{version}
Release:   %{release}
License:   GPLv2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
URL:       http://github.com/Mirantis

%description -n fuel-release
This packages provides /etc/fuel_release file.

%files -n fuel-release
%defattr(-,root,root)
%{_sysconfdir}/fuel_release
