%define name fuel-bootstrap-image
%define version 6.1.0
%define release 1

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

%description
Fuel bootstrap image package

%prep

%build

%install
install -p -D -m 644 %{SOURCE0} %{buildroot}/var/www/nailgun/bootstrap/linux
install -p -D -m 644 %{SOURCE1} %{buildroot}/var/www/nailgun/bootstrap/initramfs.img
install -D -m 700 -d %{buildroot}/root/.ssh
install -p -m 600 %{SOURCE2} %{buildroot}/root/.ssh/bootstrap.rsa

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/var/www/nailgun/bootstrap/linux
/var/www/nailgun/bootstrap/initramfs.img
