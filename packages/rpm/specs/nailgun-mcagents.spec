Name:      nailgun-mcagents
Summary:   MCollective Agents
Version:   0.1.0
Release:   1
License:   GPLv2
BuildRoot: %{_tmppath}/%{name}-%{version}
Requires:  mcollective >= 2.2
URL:       http://mirantis.com
%description
MCollective agents


%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}
cp %{_sourcedir}/%{name}/* %{name}-%{version}

%install
cd %{name}-%{version}
mkdir -p %{buildroot}/usr/libexec/mcollective/mcollective/agent/
cp * %{buildroot}/usr/libexec/mcollective/mcollective/agent/

%clean
rm -rf %{buildroot}

%files
/usr/libexec/mcollective/mcollective/agent/*