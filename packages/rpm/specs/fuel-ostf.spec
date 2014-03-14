%define name fuel-ostf
%define version 0.1
%define unmangled_version 0.1
%define unmangled_version 0.1
%define release 1

Summary: cloud computing testing
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildRequires:  python-setuptools
BuildArch: noarch

# fuel_health_reqs
Requires:    python-oslo-config >= 1.1.1
Requires:    python-cinderclient >= 1.0.6
Requires:    python-keystoneclient >= 1:0.4.1
Requires:    python-novaclient >= 1:2.15.0
Requires:    python-heatclient >= 0.2.5
Requires:    python-muranoclient >= 0.2.11
Requires:    python-savannaclient >= 0.3
Requires:    python-paramiko >= 1.10.1
Requires:    python-requests >= 1.1
Requires:    python-requests < 1.2.3 
Requires:    python-unittest2 >= 0.5.1
Requires:    PyYAML >= 3.10
Requires:    python-testresources >= 0.2.7

# fuel_ostf_reqs
Requires:    python-nose >= 1.3.0
Requires:    python-sqlalchemy >= 0.8.2
Requires:    python-alembic >= 0.5.0
Requires:    python-gevent >= 0.13.8
Requires:    python-pecan >= 0.3.0
Requires:    python-psycopg2 >= 2.5.1
Requires:    python-stevedore >= 0.10

# test_requires
#mock >= 1.0.1
#pep8 >= 1.4.6
#py >= 1.4.15
#Requires:    python-six >= 1.4.1
#tox >= 1.5.0

#Requires:    python-mako >= 0.8.1
#Requires:    python-markupsafe >= 0.18
#Requires:    python-webob >= 1.2.3
#Requires:    python-webtest >= 2.0.6
#Requires:    python-argparse >= 1.2.1
#Requires:    python-beautifulsoup4 >= 4.2.1
#Requires:    python-cliff >= 1.4
#Requires:    python-cmd2 >= 0.6.5.1
#Requires:    python-d2to1 >= 0.2.10
#Requires:    python-distribute >= 0.7.3
#Requires:    python-extras >= 0.0.3
#Requires:    python-greenlet >= 0.4.1
#Requires:    python-httplib2 >= 0.8
#Requires:    python-iso8601 >= 0.1.4
#Requires:    python-jsonpatch >= 1.1
#Requires:    python-jsonpointer >= 1.0
#Requires:    python-jsonschema >= 2.0.0
#Requires:    python-logutils >= 0.3.3
#Requires:    python-netaddr >= 0.7.10
#Requires:    python-ordereddict >= 1.1
#Requires:    python-pbr >= 0.5.21
#Requires:    python-prettytable >= 0.7.2
#Requires:    python-psycogreen >= 1.0
#Requires:    python-pyopenssl >= 0.13
#Requires:    python-crypto >= 2.6
#Requires:    pyparsing >= 1.5.6
#Requires:    python-mimeparse >= 0.1.4
#Requires:    python-setuptools-git >= 1.0
#Requires:    python-simplegeneric >= 0.8.1
#Requires:    python-simplejson >= 3.3.0
#Requires:    python-testtools >= 0.9.32
#Requires:    python-waitress >= 0.8.5
#Requires:    python-warlock >= 1.0.1
#Requires:    python-wsgiref >= 0.1.2


%description
fuel-ostf-tests

%prep
%setup -n %{name}-%{unmangled_version} -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)


