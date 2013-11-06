Name:      nailgun-net-check
Summary:   Network checking package for CentOS6.2
Version:   0.0.2
Release:   1
License:   GPLv2
Source0:   http://pypcap.googlecode.com/files/pypcap-%{pypcapver}.tar.gz
Source1:   http://www.tcpdump.org/release/libpcap-%{libpcapver}.tar.gz
Patch1:    pypcap.diff
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-build
URL:       http://github.com/Mirantis
Requires:  vconfig
Requires:  scapy
Requires:  python-argparse
Requires: python-pypcap
Requires: libpcap
Requires: libpcap-devel

%define pypcapver 1.1
%define libpcapver 1.3.0

%description
This is a network tool that helps to verify networks connectivity
between hosts in network.

%global _default_patch_fuzz 4

%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}

%install
mkdir -p %{buildroot}/usr/bin
cp %{_sourcedir}/net_probe.py %{buildroot}/usr/bin

%files
%defattr(0755,root,root,-)
/usr/bin/net_probe.py

%clean
rm -rf %{buildroot}
