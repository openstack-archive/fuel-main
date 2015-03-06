%define name fuel-target-centos-images
%define version 6.1.0
%define release 1

Summary: Fuel target centos images package
Name: %{name}
Version: %{version}
Release: %{release}
URL:     http://mirantis.com
Source0: %{name}.tar
License: Apache
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch

%description
Fuel target centos images package

%prep
rm -rf %{name}
mkdir %{name}
tar xf %{SOURCE0} -C %{name}

%build

%install
install -D -m 755 -d %{buildroot}/var/www/nailgun/targetimages
install -p -D -m 644 -t %{buildroot}/var/www/nailgun/targetimages %{name}/*

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/var/www/nailgun/targetimages/*
