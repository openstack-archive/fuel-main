%define srcname nailgun-mcagents
Name:      ruby21-nailgun-mcagents
Summary:   MCollective Agents
Version:   0.1.0
Release:   1
License:   GPLv2
Source0:   %{srcname}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}
Requires:  ruby21-mcollective >= 2.2
URL:       http://mirantis.com
%description
MCollective agents


%prep
%setup -c -n %{srcname}-%{version}

%install
mkdir -p %{buildroot}/usr/libexec/mcollective/mcollective/agent/
cp * %{buildroot}/usr/libexec/mcollective/mcollective/agent/

%clean
rm -rf %{buildroot}

%files
/usr/libexec/mcollective/mcollective/agent/*

%changelog
* Mon May 6 2013 Mirantis Product <product@mirantis.com> - 0.1.0-1
- Version 0.1.0
