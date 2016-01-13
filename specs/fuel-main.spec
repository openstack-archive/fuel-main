#TEMP fixme
%define repo_name fuel-main

%define name fuel
%{!?version: %define version 9.0.0}
%{!?fuel_release: %define fuel_release 9.0}
%{!?release: %define release 1}

Name: %{name}
Summary: Fuel for OpenStack
URL:     http://mirantis.com
Source0: bootstrap_admin_node.sh
Version: %{version}
Release: %{release}
License: Apache
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Requires: fuel-bootstrap-image >= %{version}
Requires: fuel-dockerctl >= 9.0
Requires: fuel-docker-images >= %{version}
Requires: fuel-library9.0
Requires: fuelmenu >= %{version}
Requires: fuel-provisioning-scripts >= %{version}
Requires: fuel-release >= %{version}
Requires: network-checker >= %{version}
Requires: python-fuelclient >= %{version}
Requires: fuel-mirror >= %{version}
Requires: shotgun >= %{version}
Requires: yum

%description
Fuel for OpenStack is a lifecycle management utility for
managing OpenStack.

%install
%{__mkdir_p} %{buildroot}%{_sysconfdir}/sysconfig/
echo %{fuel_release} > %{buildroot}%{_sysconfdir}/fuel_release
echo "ENABLED=1" > %{buildroot}%{_sysconfdir}/sysconfig/$(basename %{SOURCE0} | cut -d'.' -f1)
install -p -D -m 755 %{SOURCE0} %{buildroot}%{_sbindir}/$(basename %{SOURCE0})

%files
%defattr(-,root,root)
%{_sysconfdir}/sysconfig/bootstrap_admin_node
%attr(755,root,root) %{_sbindir}/bootstrap_admin_node.sh

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
