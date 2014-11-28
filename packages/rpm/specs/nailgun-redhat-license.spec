Name:      nailgun-redhat-license
Summary:   Getting redhat licenses
Version:   0.0.1
Release:   3
License:   Apache License 2.0
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-build
URL:       http://github.com/Mirantis
Requires:  subscription-manager
Source0:   get_redhat_licenses

%description
This is python script that can be used to get redhat licenses.

%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}
cp %{SOURCE0} %{name}-%{version}

%install
mkdir -p %{buildroot}/usr/bin
cp %{_sourcedir}/get_redhat_licenses %{buildroot}/usr/bin

%files
%defattr(0755,root,root,-)
/usr/bin/get_redhat_licenses

%clean
rm -rf %{buildroot}
