#TEMP fixme
%define repo_name fuel-main

#FIXME workaround for building in perestroika
%define _unpackaged_files_terminate_build 0

%define name fuel
%{!?version: %define version 9.0.0}
%{!?fuel_release: %define fuel_release 9.0}
%{!?release: %define release 1}

Name: %{name}
Summary: Fuel for OpenStack
URL:     http://mirantis.com
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
License: Apache
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
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

%prep
%setup -cq -n %{name}-%{version}

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/etc
echo %{fuel_release} > %{buildroot}%{_sysconfdir}/fuel_release
install -D -m 700 -d %{buildroot}/root/.ssh
install -p -m 600 %{_builddir}/%{name}-%{version}/bootstrap/ssh/id_rsa %{buildroot}/root/.ssh/bootstrap.rsa
install -D -m 755 -d %{buildroot}%{_sbindir}
install -D -m 755 -d %{buildroot}%{_sysconfdir}/sysconfig/
echo "ENABLED=1" > %{buildroot}%{_sysconfdir}/sysconfig/bootstrap_admin_node
install -p -m 755 %{_builddir}/%{name}-%{version}/iso/bootstrap_admin_node.sh %{buildroot}%{_sbindir}/bootstrap_admin_node.sh

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
/root/.ssh/bootstrap.rsa

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

%package -n fuel-setup

Summary:   Fuel deployment script package
Version:   %{version}
Release:   %{release}
License:   GPLv2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
URL:       http://github.com/Mirantis

%description -n fuel-setup
This packages provides script to deploy Fuel components.

%files -n fuel-setup
%defattr(-,root,root)
%{_sysconfdir}/sysconfig/bootstrap_admin_node
%{_sbindir}/bootstrap_admin_node.sh