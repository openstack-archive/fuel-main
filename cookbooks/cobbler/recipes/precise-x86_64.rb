# This recipe requires ubuntu netinst image installed 
# into node["cobbler"]["precise-x86_64_iso"]
# it requires also ssh key generated in /root/.ssh


template "#{node.cobbler.preseed_dir}/precise-x86_64.seed" do
  source "precise-x86_64.seed"
  owner "root"
  group "root"
  mode "0644"
  variables(
            :late_authorized_keys => LateFile.new("/root/.ssh/id_rsa.pub"),
            :late_deploy => LateFile.new("/opt/nailgun/bin/deploy")
            )
end

directory "#{node["cobbler"]["precise-x86_64_mnt"]}" do
  recursive true
  owner "root"
  group "root"
  mode "0755"
  not_if "test -d #{node["cobbler"]["precise-x86_64_mnt"]}"
end

mount "#{node["cobbler"]["precise-x86_64_mnt"]}" do
  options "loop"
  device "#{node["cobbler"]["precise-x86_64_iso"]}"
end

link "#{node.cobbler.ks_mirror_dir}/precise-x86_64" do
  to "#{node["cobbler"]["precise-x86_64_mnt"]}"
end

cobbler_distro "precise-x86_64" do
  kernel "#{node.cobbler.ks_mirror_dir}/precise-x86_64/linux"
  initrd "#{node.cobbler.ks_mirror_dir}/precise-x86_64/initrd.gz"
  arch "x86_64"
  breed "ubuntu"
  osversion "precise"
end

cobbler_profile "precise-x86_64" do
  kickstart "#{node.cobbler.preseed_dir}/precise-x86_64.seed"
  kopts "priority=critical locale=en_US netcfg/choose_interface=auto"
  distro "precise-x86_64"
  menu true
end

