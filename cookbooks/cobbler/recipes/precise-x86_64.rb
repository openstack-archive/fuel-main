# This recipe requires ubuntu netinst image installed 
# into node.cobbler.precise-x86_64_iso

template "#{node.cobbler.preseed_dir}/precise-x86_64.seed" do
  source "precise-x86_64.seed"
  owner "root"
  group "root"
  mode "0644"
end

directory "#{node.cobbler.precise-x86_64_mnt}" do
  recursive true
  owner "root"
  group "root"
  mode "0755"
end

mount "#{node.cobbler.precise-x86_64_mnt}" do
  options "loop"
  device "#{node.cobbler.precise-x86_64_iso}"
end

link "#{node.cobbler.ks_mirror_dir}/precise-x86_64" do
  to #{node.cobbler.precise-x86_64_mnt}
end

distro "precise-x86_64" do
  kernel "#{node.cobbler.ks_mirror_dir}/precise-x86_64/linux"
  initrd "#{node.cobbler.ks_mirror_dir}/precise-x86_64/initrd.gz"
  arch "x86_64"
  breed "ubuntu"
  osversion "precise"
end

profile "precise-x86_64" do
  kickstart "#{node.cobbler.preseed_dir}/precise-x86_64.seed"
  kopts "priority=critical locale=en_US netcfg/choose_interface=auto"
  distro "precise-x86_64"
  menu true
end

