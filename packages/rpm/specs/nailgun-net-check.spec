Name:      nailgun-net-check
Summary:   Network checking package for CentOS6.2
Version:   0.0.2
Release:   1
License:   GPLv2
Source0:   net_probe.py
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-build
URL:       http://github.com/Mirantis
Requires:  vconfig
Requires:  scapy
Requires:  python-argparse
Requires: python-pypcap

%description
This is a network tool that helps to verify networks connectivity
between hosts in network.

%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}

%install
mkdir -p %{buildroot}/usr/bin
cp %{SOURCE0} %{buildroot}/usr/bin

%files
%defattr(0755,root,root,-)
/usr/bin/net_probe.py

%clean
rm -rf %{buildroot}
