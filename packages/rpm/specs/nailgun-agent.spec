Name:      nailgun-agent
Summary:   Nailgun starup agent
Version:   0.1.0
Release:   3
License:   GPLv2
BuildRoot: %{_tmppath}/%{name}-%{version}
Source0:   agent
Source1:   nailgun-agent.cron
URL:       http://mirantis.com
Requires:  rubygem-rethtool
Requires:  rubygem-ohai
Requires:  rubygem-httpclient
Requires:  rubygem-ipaddress
Requires:  rubygem-json
Requires:  rubygems
%description
Nailgun starup agent that register node at Nailgun and make a little setup
of other services.


%prep
rm -rf %{name}-%{version}
mkdir %{name}-%{version}
cp %{SOURCE0} %{name}-%{version}
cp %{SOURCE1} %{name}-%{version}

%install
cd %{name}-%{version}
mkdir -p %{buildroot}/opt/nailgun/bin
mkdir -p %{buildroot}/etc/cron.d
install -m 755 %{SOURCE0} %{buildroot}/opt/nailgun/bin/agent
install -m 644 %{SOURCE1} %{buildroot}/etc/cron.d/nailgun-agent

%clean
rm -rf %{buildroot}

%files
/etc/cron.d/nailgun-agent
/opt/nailgun/bin/agent
