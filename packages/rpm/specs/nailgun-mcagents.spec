Name:      nailgun-mcagents
Summary:   MCollective Agents
Version:   6.0.1
Release:   1
License:   GPLv2
Source0:   mcagents.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}
Requires:  mcollective >= 2.2
URL:       http://mirantis.com
%description
MCollective agents


%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}
tar -xf %{SOURCE0} -C %{name}-%{version}

%install
cd %{name}-%{version}
mkdir -p %{buildroot}/usr/libexec/mcollective/mcollective/agent/
cp * %{buildroot}/usr/libexec/mcollective/mcollective/agent/

%clean
rm -rf %{buildroot}

%files
/usr/libexec/mcollective/mcollective/agent/*
