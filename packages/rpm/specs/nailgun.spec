%define name nailgun
%define version 0.1.0
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
BuildRequires:  python-setuptools
BuildArch: noarch

Requires:    python-alembic == 0.6.2
Requires:    python-amqplib == 1.0.2
Requires:    python-anyjson == 0.3.3
Requires:    python-argparse == 1.2.1
Requires:    python-babel == 1.3
Requires:    python-crypto == 2.6.1
Requires:    python-decorator == 3.4.0
Requires:    python-fysom == 1.0.11
Requires:    python-iso8601 == 0.1.9
Requires:    python-jinja2 == 2.7
Requires:    python-jsonschema == 2.3.0
Requires:    python-kombu == 2.5.14
Requires:    python-mako == 0.9.1
Requires:    python-markupsafe == 0.18
Requires:    python-netaddr == 0.7.10
Requires:    python-netifaces == 0.8
Requires:    python-oslo-config == 1:1.2.1
Requires:    python-paste == 1.7.5.1
Requires:    python-psycopg2 == 2.5.1
Requires:    python-simplejson == 3.3.0
Requires:    python-sqlalchemy == 0.7.9
Requires:    python-webpy == 0.37
Requires:    python-wsgilog == 0.3
Requires:    python-wsgiref == 0.1.2
Requires:    PyYAML == 3.10
Requires:    Shotgun == 0.1.0
# Workaroud for babel bug
Requires:    pytz

%description
Nailgun package

%prep
%setup -n %{name}-%{version} -n %{name}-%{version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)


