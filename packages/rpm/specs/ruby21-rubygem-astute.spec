# Generated from astute-0.0.1.gem by gem2rpm -*- rpm-spec -*-
%define rbname astute
%define version 0.0.2
%define release 9
%global gemdir %(ruby -rubygems -e 'puts Gem::dir' 2>/dev/null)
%global geminstdir %{gemdir}/gems/%{gemname}-%{version}
%define gembuilddir %{buildroot}%{gemdir}

Summary: Orchestrator for OpenStack deployment
Name: ruby21-rubygem-%{rbname}

Version: %{version}
Release: %{release}
Group: Development/Ruby
License: Distributable
URL: http://fuel.mirantis.com
Source0: %{rbname}-%{version}.gem
# Make sure the spec template is included in the SRPM
Source1: astute.conf
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Requires: ruby >= 2.1
Requires: ruby21-rubygem-activesupport = 3.0.10
Requires: ruby21-rubygem-mcollective-client = 2.4.1
Requires: ruby21-rubygem-symboltable = 1.0.2
Requires: ruby21-rubygem-rest-client = 1.6.7
Requires: ruby21-rubygem-popen4 = 0.1.2
Requires: ruby21-rubygem-amqp = 0.9.10
Requires: ruby21-rubygem-raemon = 0.3.0
Requires: ruby21-rubygem-net-ssh = 2.8.0
Requires: ruby21-rubygem-net-ssh-gateway = 1.2.0
Requires: ruby21-rubygem-net-ssh-multi = 1.2.0
Requires: openssh-clients
BuildRequires: ruby >= 2.1
BuildArch: noarch
Provides: ruby21(Astute) = %{version}


%description
Deployment Orchestrator of Puppet via MCollective. Works as a library or from
CLI.


%prep
%setup -T -c

%build

%install
%{__rm} -rf %{buildroot}
mkdir -p %{gembuilddir}
gem install --local --install-dir %{gembuilddir} --force %{SOURCE0}
mkdir -p %{buildroot}%{_bindir}
mv %{gembuilddir}/bin/* %{buildroot}%{_bindir}
rmdir %{gembuilddir}/bin

install -d -m 750 %{buildroot}%{_sysconfdir}/astute
install -p -D -m 640 %{SOURCE1} %{buildroot}%{_sysconfdir}/astute/astute.conf
cat > %{buildroot}%{_bindir}/astuted <<EOF
#!/bin/bash
ruby -r 'rubygems' -e "gem 'astute', '>= 0'; load Gem.bin_path('astute', 'astuted', '>= 0')" -- \$@
EOF

install -d -m 755 %{buildroot}%{_localstatedir}/log/astute

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root)
# %{_bindir}/astute
# %{gemdir}/gems/astute-0.0.2/bin/astute
%{gemdir}/gems/astute-0.0.2/bin/astuted
%{gemdir}/gems/astute-0.0.2/lib/astute.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/config.rb
# %{gemdir}/gems/astute-0.0.2/lib/astute/rpuppet.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/deployment_engine.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/deployment_engine/nailyfact.rb
# %{gemdir}/gems/astute-0.0.2/lib/astute/deployment_engine/simple_puppet.rb
# %{gemdir}/gems/astute-0.0.2/lib/astute/metadata.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/rsyslogd.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/cobbler_manager.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/dump.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/exceptions.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/ext/deep_copy.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/ext/exception.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/ext/hash.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/post_deploy_actions.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/post_deploy_actions/restart_radosgw.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/post_deploy_actions/update_cluster_hosts_info.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/post_deploy_actions/upload_cirros_image.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/logparser.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/reporter.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/version.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/node.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/puppetd.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/context.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/orchestrator.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/logparser/deployment.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/logparser/provision.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/logparser/parser_patterns.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/cobbler.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/mclient.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/network.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/nodes_remover.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/ssh.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/ssh_actions/ssh_erase_nodes.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/ssh_actions/ssh_hard_reboot.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/ruby_removed_functions.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/server/dispatcher.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/server/producer.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/server/reporter.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/server/server.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/server/task_queue.rb
%{gemdir}/gems/astute-0.0.2/lib/astute/server/worker.rb
%{gemdir}/gems/astute-0.0.2/spec/example-logs/main-menu.log_
%{gemdir}/gems/astute-0.0.2/examples/example_astute_config.yaml
%{gemdir}/gems/astute-0.0.2/spec/integration/mcollective_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/spec_helper.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/rsyslogd_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/deployment_engine_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/dump_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/fixtures/common_attrs.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/fixtures/common_nodes.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/fixtures/ha_deploy.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/fixtures/ha_nodes.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/fixtures/multi_deploy.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/network_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/nodes_remover_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/post_deploy_actions_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/restart_radosgw_hook_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/update_cluster_hosts_info_hook_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/upload_cirros_image_hook_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/nailyfact_deploy_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/orchestrator_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/node_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/puppetd_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/logparser_spec.rb
# %{gemdir}/gems/astute-0.0.2/spec/unit/simplepuppet_deploy_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/reporter_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/mclient_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/unit/cobbler_spec.rb
%{gemdir}/gems/astute-0.0.2/spec/example-logs/puppet-agent.log.ha.contr.2
%{gemdir}/gems/astute-0.0.2/spec/example-logs/puppet-agent.log.ha.contr.3
%{gemdir}/gems/astute-0.0.2/spec/example-logs/puppet-agent.log.ha.contr.1
%{gemdir}/gems/astute-0.0.2/spec/example-logs/puppet-agent.log.ha.compute
%{gemdir}/gems/astute-0.0.2/spec/example-logs/puppet-agent.log.multi.compute
%{gemdir}/gems/astute-0.0.2/spec/example-logs/anaconda.log_
%{gemdir}/gems/astute-0.0.2/spec/example-logs/puppet-agent.log.multi.contr
%{gemdir}/gems/astute-0.0.2/spec/example-logs/puppet-agent.log.singlenode

%dir %attr(0750, naily, naily) %{_sysconfdir}/astute
%config(noreplace) %attr(0640, root, naily) %{_sysconfdir}/astute/astute.conf
%dir %attr(0755, naily, naily) %{_localstatedir}/log/astute
%config(noreplace) %{_bindir}/astuted

%doc %{gemdir}/doc/astute-0.0.2
%{gemdir}/cache/astute-0.0.2.gem
%{gemdir}/specifications/astute-0.0.2.gemspec

%changelog
