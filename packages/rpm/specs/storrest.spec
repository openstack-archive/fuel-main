%define name storrest
%define version 0.0.1
%define unmangled_version 0.0.1
%define release 1

Summary: RESTful storcli wrapper
Name: %{name}
Version: %{version}
Release: %{release}
URL:     http://mirantis.com
Source0: %{name}-%{unmangled_version}.tar.gz
License: Apache
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Source1: storrest
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Alexei Sheplyakov <asheplyakov@mirantis.com>
BuildRequires: git
Requires:    python-webpy

%description
LSI Storrest package

%prep
%setup -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

mkdir -p $RPM_BUILD_ROOT/etc/init.d/
install -p -D -m 755 %{SOURCE1} %{buildroot}/etc/init.d/storrest

%post
if [ -x /sbin/chkconfig ] ; then
    /sbin/chkconfig --add storrest
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
/etc/init.d/storrest
