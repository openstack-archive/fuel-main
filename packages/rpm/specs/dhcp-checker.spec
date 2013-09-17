%define __python /usr/bin/python2.6
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pyver: %define pyver %(%{__python} -c "import sys ; print sys.version[:3]")}

%define name dhcp_checker
%define version 0.1
%define release 1

Summary:        Networking tool for finding dhcp servers in network
Name:           %{name}
Version:        %{version}
Release:        %{release}
Source0:        %{name}
License:        GPLv2
Group:          Development/Packages
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix:         %{_prefix}
BuildArch:      noarch
Vendor:         Dmitry Shulyak <yashulyak@gmail.com>
Url:            http://github.com/Mirantis/


Requires: python-cliff-tablib
Requires: scapy


%description
CLI tool for finding dhcp servers in network.
dhcpcheck discover --ifaces eth0 eth1 eth2 --timeout=10

%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}
cp -r %{_sourcedir}/* %{name}-%{version}

%build
cd %{name}-%{version}
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
cd %{name}-%{version}
%{__python} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/usr/bin/dhcpcheck
%{python_sitelib}/%{name}
%{python_sitelib}/%{name}-%{version}-py2.6.egg-info