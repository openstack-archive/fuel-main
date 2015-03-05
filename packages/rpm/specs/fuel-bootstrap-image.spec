%define name fuel-bootstrap-image
%define version 6.1.0
%define release 1

Summary: Fuel bootstrap image package
Name: %{name}
Version: %{version}
Release: %{release}
URL:     http://mirantis.com
Source0: %{name}-%{version}.tar.gz
License: Apache
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch

%description
Fuel bootstrap image package

%prep

%build

%install
cd $RPM_BUILD_DIR
install -p -D -m 644 linux %{buildroot}/var/www/nailgun/bootstrap/linux
install -p -D -m 644 initramfs.img %{buildroot}/var/www/nailgun/bootstrap/initramfs.img

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/var/www/nailgun/bootstrap/linux
/var/www/nailgun/bootstrap/initramfs.img
