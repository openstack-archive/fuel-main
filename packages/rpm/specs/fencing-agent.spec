Name:      fencing-agent
Summary:   Fencing agent
Version:   0.1.0
Release:   1
License:   GPLv2
BuildRoot: %{_tmppath}/%{name}-%{version}
Source0:   fencing-agent.rb
Source1:   fencing-agent.cron
URL:       http://mirantis.com
%description
Agent for periodic checks for additional fencing criterias (free space, etc)

%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}
cp %{SOURCE0} %{name}-%{version}
cp %{SOURCE1} %{name}-%{version}

%install
cd %{name}-%{version}
mkdir -p %{buildroot}/opt/nailgun/bin
mkdir -p %{buildroot}/etc/cron.d
install -m 755 %{SOURCE0} %{buildroot}/opt/nailgun/bin/fencing-agent.rb
install -m 644 %{SOURCE1} %{buildroot}/etc/cron.d/fencing-agent

%clean
rm -rf %{buildroot}

%files
/etc/cron.d/fencing-agent
/opt/nailgun/bin/fencing-agent.rb
