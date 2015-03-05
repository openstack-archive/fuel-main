%define name fuel-download-debian-installer
%define version 6.1.0
%define release 1

Summary: %{name} package
Name: %{name}
Version: %{version}
Release: %{release}
URL:     http://mirantis.com
Source0: download-debian-installer
License: Apache
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch

Requires:    wget

%description
This package provides a script which is to download debian-installer kernel and initrd

%prep

%build

%install
install -p -D -m 755 %{SOURCE0} %{buildroot}%{_bindir}/download-debian-installer

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_bindir}/download-debian-installer
