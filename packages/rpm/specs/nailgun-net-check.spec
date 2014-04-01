%define name nailgun-net-check
%define version 0.2
%define release 1

Name:      %{name}
Summary:   Network checking package for CentOS6.2
Version:   %{version}
Release:   %{release}
License:   GPLv2
Source0:   %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
URL:       http://github.com/Mirantis

BuildRequires:  python-setuptools

Requires:  vconfig
Requires:  scapy
Requires:  python-argparse
Requires:  python-pypcap
Requires: python-cliff-tablib

%description
This is a network tool that helps to verify networks connectivity
between hosts in network.

%prep
%setup -n %{name}-%{version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
