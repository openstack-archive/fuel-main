%define name nailgun
%define version 6.0.0
%define release 1

Summary: Nailgun package
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildRequires:  python-setuptools git
BuildArch: noarch
Requires:    python-alembic >= 0.6.2
Requires:    python-amqplib >= 1.0.2
Requires:    python-anyjson >= 0.3.3
Requires:    python-argparse >= 1.2.1
Requires:    python-babel >= 1.3
Requires:    python-crypto >= 2.6.1
Requires:    python-decorator >= 3.4.0
Requires:    python-fysom >= 1.0.11
Requires:    python-iso8601 >= 0.1.9
Requires:    python-jinja2 >= 2.7
Requires:    python-jsonschema >= 2.3.0
Requires:    python-keystoneclient >= 0.11
Requires:    python-keystonemiddleware >= 1.2.0
Requires:    python-kombu >= 1:3.0.16
Requires:    python-mako >= 0.9.1
Requires:    python-markupsafe >= 0.18
Requires:    python-netaddr >= 0.7.10
Requires:    python-netifaces >= 0.8
Requires:    python-oslo-config >= 1:1.2.1
Requires:    python-oslo-serialization >= 1.0.0
Requires:    python-paste >= 1.7.5.1
Requires:    python-ply >= 3.4
Requires:    python-psycopg2 >= 2.5.1
Requires:    python-requests >= 1.2.3
Requires:    python-simplejson >= 3.3.0
Requires:    python-six >= 1.5.2
Requires:    python-sqlalchemy >= 0.7.9
Requires:    python-stevedore >= 0.14
Requires:    python-urllib3 >= 1.7
Requires:    python-webpy >= 0.37
Requires:    python-wsgilog >= 0.3
Requires:    python-wsgiref >= 0.1.2
Requires:    PyYAML >= 3.10
Requires:    python-novaclient >= 2.17.0
Requires:    python-networkx-core >= 1.8.0
Requires:    python-cinderclient >= 1.0.7
Requires:    pydot-ng >= 1.0.0
Requires:    python-ordereddict >= 1.1
# Workaroud for babel bug
Requires:    pytz
BuildRequires: nodejs

%description
Nailgun package

%prep
%setup -cq -n %{name}-%{version} 
npm install -g inherits@2.0.0
npm install -g grunt-cli
npm install -g grunt

%build
mkdir -p %{_builddir}/%{name}-%{version}/nailgun/npm-cache
cd %{_builddir}/%{name}-%{version}/nailgun && npm --cache %{_builddir}/%{name}-%{version}/nailgun/npm-cache install && grunt build --static-dir=compressed_static
[ -n %{_builddir} ] && rm -rf %{_builddir}/%{name}-%{version}/nailgun/static
mv %{_builddir}/%{name}-%{version}/nailgun/compressed_static %{_builddir}/%{name}-%{version}/nailgun/static
cd %{_builddir}/%{name}-%{version}/nailgun && python setup.py build
cd %{_builddir}/%{name}-%{version}/network_checker && python setup.py build
cd %{_builddir}/%{name}-%{version}/shotgun && python setup.py build
cd %{_builddir}/%{name}-%{version}/fuelmenu && python setup.py build

%install
cd %{_builddir}/%{name}-%{version}/nailgun && python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=%{_builddir}/%{name}-%{version}/nailgun/INSTALLED_FILES
cd %{_builddir}/%{name}-%{version}/network_checker && python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=%{_builddir}/%{name}-%{version}/network_checker/INSTALLED_FILES
cd %{_builddir}/%{name}-%{version}/shotgun && python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=%{_builddir}/%{name}-%{version}/shotgun/INSTALLED_FILES
cd %{_builddir}/%{name}-%{version}/fuelmenu && python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=%{_builddir}/%{name}-%{version}/fuelmenu/INSTALLED_FILES
mkdir -p %{buildroot}/opt/nailgun/bin
mkdir -p %{buildroot}/etc/cron.d
mkdir -p %{buildroot}/etc/fuel
install -d -m 755 %{buildroot}/etc/fuel
install -m 600 %{_builddir}/%{name}-%{version}/fuelmenu/fuelmenu/settings.yaml %{buildroot}/etc/fuel/astute.yaml
install -m 755 %{_builddir}/%{name}-%{version}/bin/agent %{buildroot}/opt/nailgun/bin/agent
install -m 644 %{_builddir}/%{name}-%{version}/bin/nailgun-agent.cron %{buildroot}/etc/cron.d/nailgun-agent

%clean
rm -rf $RPM_BUILD_ROOT

%files -f %{_builddir}/%{name}-%{version}/nailgun/INSTALLED_FILES
%defattr(0755,root,root)


%package -n nailgun-agent

Summary:   Nailgun startup agent
Version:   6.0.0
Release:   1
License:   GPLv2
BuildRoot: %{_tmppath}/%{name}-%{version}
URL:       http://mirantis.com
Requires:  rubygem-rethtool
Requires:  rubygem-ohai
Requires:  rubygem-httpclient
Requires:  rubygem-ipaddress
Requires:  rubygem-json
Requires:  rubygems

%description -n nailgun-agent
Nailgun startup agent that register node at Nailgun and make a little setup
of other services.

%files -n nailgun-agent
/etc/cron.d/nailgun-agent
/opt/nailgun/bin/agent

%package -n nailgun-net-check

Summary:   Network checking package for CentOS6.x
Version:   %{version}
Release:   %{release}
License:   GPLv2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
URL:       http://github.com/Mirantis
Requires:  vconfig
Requires:  scapy
Requires:  python-argparse
Requires:  python-pypcap
Requires:  python-cliff-tablib
Requires:  python-stevedore
Requires:  python-daemonize
Requires:  python-yaml
Requires:  tcpdump


%description -n nailgun-net-check
This is a network tool that helps to verify networks connectivity
between hosts in network.

%files -n nailgun-net-check -f %{_builddir}/%{name}-%{version}/network_checker/INSTALLED_FILES
%defattr(-,root,root)

%package -n shotgun

Summary: Shotgun package
Version: %{version}
Release: %{release}
URL:     http://mirantis.com
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Requires:    postgresql
Requires:    python-fabric >= 1.10.0
Requires:    python-argparse
Requires:    tar
Requires:    gzip
Requires:    bzip2
Requires:    openssh-clients
Requires:    xz

%description -n shotgun
Shotgun package. 

%files -n shotgun -f  %{_builddir}/%{name}-%{version}/shotgun/INSTALLED_FILES
%defattr(-,root,root)

%package -n fuelmenu

Summary: Console utility for pre-configuration of Fuel server
Version: %{version}
Release: %{release}
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Matthew Mosesohn <mmosesohn@mirantis.com>
BuildRequires:  python-setuptools
Requires: bind-utils
Requires: nailgun-net-check
Requires: ntp
Requires: python-setuptools
Requires: python-netaddr
Requires: python-netifaces
Requires: python-urwid >= 1.1.0
Requires: PyYAML
Requires: python-ordereddict

%description -n fuelmenu
Summary: Console utility for pre-configuration of Fuel server

%files -n fuelmenu -f %{_builddir}/%{name}-%{version}/fuelmenu/INSTALLED_FILES
%defattr(-,root,root)
%config(noreplace) /etc/fuel/astute.yaml



