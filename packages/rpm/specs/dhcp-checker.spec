%define name dhcp_checker
%define version 0.1
%define release 1

Summary:        Networking tool for finding dhcp servers in network
Name:           %{name}
Version:        %{version}
Release:        %{release}
Source0:        %{name}-%{version}.tar.gz
License:        GPLv2
Group:          Development/Packages
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix:         %{_prefix}
Vendor:         Dmitry Shulyak <yashulyak@gmail.com>
Url:            http://github.com/Mirantis/

Requires: python-cliff-tablib
Requires: scapy
Requires: python-pypcap

%description
CLI tool for finding dhcp servers in network.
dhcpcheck discover --ifaces eth0 eth1 eth2 --timeout=10

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
