%define name fuel-bootstrap-image
%{!?version: %define version 6.1.0}
%{!?release: %define release 1}

Summary: Fuel bootstrap image generator
Name: %{name}
Version: %{version}
Release: %{release}
URL:     http://github.com/asheplyakov/fuel-bootstrap-image
Source0: fuel-bootstrap-image-%{version}.tar.gz 
License: Apache
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
Requires: debootstrap, wget
BuildArch: noarch

%description
Fuel bootstrap image generator package

%prep
%autosetup -n %{name}

%build
%configure

%install
%make_install
mkdir -p %{buildroot}/var/www/nailgun/bootstrap

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_bindir}/*
%{_datadir}/fuel-bootstrap-image/*
%dir /var/www/nailgun/bootstrap

