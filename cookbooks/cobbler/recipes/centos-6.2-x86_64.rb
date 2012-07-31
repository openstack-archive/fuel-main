# This recipe requires ubuntu netinst image installed 
# into node["cobbler"]["precise-x86_64_iso"]
# it requires also ssh key generated in /root/.ssh


template "#{node.cobbler.preseed_dir}/centos-6.2-x86_64.ks" do
  source "centos-6.2-x86_64.ks"
  owner "root"
  group "root"
  mode "0644"
  variables(
            :late_authorized_keys => LateFile.new("#{node.nailgun.root}/.ssh/id_rsa.pub"),
            :late_deploy => LateFile.new("/opt/nailgun/bin/deploy"),
            :late_agent => LateFile.new("/opt/nailgun/bin/agent"),
            :late_agent_config => LateFile.new("
NodeAgentConfig.define do |config|
config.api = \"http://#{node.cobbler.repoaddr}:8000/api\"
end
", :method => :content),
            :late_rclocal => LateFile.new("
#!/bin/sh

flock -w 0 -o /var/lock/agent.lock -c \"/opt/nailgun/bin/agent -c /opt/nailgun/bin/agent_config.rb > /var/log/agent.log 2>&1\" || true
", :method => :content),
            :late_cron => LateFile.new("
*/5 * * * * export PATH=$PATH:/sbin && root /opt/nailgun/bin/agent -c /opt/nailgun/bin/agent_config.rb > /var/log/agent.log 2>&1
", :method => :content)
            )
end

directory "#{node["cobbler"]["centos-6.2-x86_64_mnt"]}" do
  recursive true
  owner "root"
  group "root"
  mode "0755"
  not_if "test -d #{node["cobbler"]["centos-6.2-x86_64_mnt"]}"
end

mount "#{node["cobbler"]["centos-6.2-x86_64_mnt"]}" do
  options "loop"
  device "#{node["cobbler"]["centos-6.2-x86_64_iso"]}"
end

link "#{node.cobbler.ks_mirror_dir}/centos-6.2-x86_64" do
  to "#{node["cobbler"]["centos-6.2-x86_64_mnt"]}"
end

link "/var/lib/mirror/centos/6.2/images" do 
  to "#{node["cobbler"]["centos-6.2-x86_64_mnt"]}/images"
end

cobbler_distro "centos-6.2-x86_64" do
  kernel "#{node.cobbler.ks_mirror_dir}/centos-6.2-x86_64/isolinux/vmlinuz"
  initrd "#{node.cobbler.ks_mirror_dir}/centos-6.2-x86_64/isolinux/initrd.img"
  arch "x86_64"
  breed "redhat"
  osversion "rhel6"
end

cobbler_profile "centos-6.2-x86_64" do
  kickstart "#{node.cobbler.preseed_dir}/centos-6.2-x86_64.ks"
  kopts ""
  distro "centos-6.2-x86_64"
  menu true
end

