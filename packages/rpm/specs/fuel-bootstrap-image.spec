%define name fuel-bootstrap-image
%{!?version: %define version 6.1.0}
%{!?release: %define release 1}

Summary: Fuel bootstrap image package
Name: %{name}
Version: %{version}
Release: %{release}
URL:     http://mirantis.com
Source0: linux
Source1: initramfs.img
Source2: bootstrap.rsa
License: Apache
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Requires: fuel-admin-user

%description
Fuel bootstrap image package

%prep

%build

%install
install -p -D -m 644 %{SOURCE0} %{buildroot}/var/www/nailgun/bootstrap/linux
install -p -D -m 644 %{SOURCE1} %{buildroot}/var/www/nailgun/bootstrap/initramfs.img
install -D -m 700 -d %{buildroot}/home/fueladmin/.ssh
install -p -m 600 %{SOURCE2} %{buildroot}/home/fueladmin/.ssh/bootstrap.rsa
#TODO dnikishov: remove once library part is merged
install -D -m 700 -g root -o root -d %{buildroot}/root/.ssh
install -p -m 600 -g root -o root %{SOURCE2} %{buildroot}/root/.ssh/bootstrap.rsa

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,fueladmin,fueladmin)
/var/www/nailgun/bootstrap/linux
/var/www/nailgun/bootstrap/initramfs.img
/root/.ssh/bootstrap.rsa
/home/fueladmin/.ssh/bootstrap.rsa
