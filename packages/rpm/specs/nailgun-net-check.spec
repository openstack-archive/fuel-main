%define __python /usr/bin/python2.6
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pyver: %define pyver %(%{__python} -c "import sys ; print sys.version[:3]")}

%define name nailgun_net_check
%define package_name net_check
%define version 0.1
%define release 1

Name:      %{name}
Summary:   Network checking package for CentOS6.2
Version:   %{version}
Release:   %{release}
License:   GPLv2
Source0:   http://pypcap.googlecode.com/files/pypcap-%{pypcapver}.tar.gz
Source1:   http://www.tcpdump.org/release/libpcap-%{libpcapver}.tar.gz
Patch1:    pypcap.diff
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-build
URL:       http://github.com/Mirantis
Requires:  vconfig
Requires:  scapy
Requires:  python-argparse

%define pypcapver 1.1
%define libpcapver 1.3.0

%description
This is a network tool that helps to verify networks connectivity
between hosts in network.

%global _default_patch_fuzz 4

%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}
tar zxf %{_sourcedir}/pypcap-%{pypcapver}.tar.gz
tar zxf %{_sourcedir}/libpcap-%{libpcapver}.tar.gz
cp -r %{_sourcedir}/* %{name}-%{version}
%patch1 -p1

%build
cd libpcap-%{libpcapver}
%configure
make
cd ../pypcap-%{pypcapver}
make all
cd ../%{name}-%{version}
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
cd %{name}-%{version}
%{__python} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT
cd ../pypcap-%{pypcapver}
%{__python} setup.py install --root=%{buildroot}

%files
%defattr(0755,root,root,-)
/usr/bin/net_probe.py
/usr/lib/python2.6/site-packages/%{package_name}
/usr/lib/python2.6/site-packages/%{name}-%{version}-py2.6.egg-info
%defattr(0644,root,root,-)
/usr/lib64/python2.6/site-packages/pcap*

%clean
rm -rf $RPM_BUILD_ROOT