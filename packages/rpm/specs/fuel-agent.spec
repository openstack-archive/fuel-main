%define name fuel-agent
%define unmangled_name fuel-agent
%define version 0.1.0
%define release 1

Summary: Fuel-agent package
Name: %{name}
Version: %{version}
Release: %{release}
URL:     http://mirantis.com
Source0: %{unmangled_name}-%{version}.tar.gz
Source1: %{unmangled_name}.conf
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildRequires:  python-setuptools
BuildArch: noarch

Requires:    python
Requires:    python-babel
Requires:    python-eventlet
Requires:    python-jsonschema
Requires:    python-oslo-config
Requires:    python-iso8601
Requires:    python-six
Requires:    tar
Requires:    gzip
Requires:    bzip2
Requires:    openssh-clients
Requires:    mdadm
Requires:    util-linux-ng
Requires:    udev
Requires:    lvm2
Requires:    dmidecode
Requires:    parted

%description
Fuel-agent package

%prep
%setup -n %{unmangled_name}-%{version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

# Install config file
install -d -m 755 %{buildroot}%{_sysconfdir}/fuel-agent
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/fuel-agent/fuel-agent.conf

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/fuel-agent/fuel-agent.conf
