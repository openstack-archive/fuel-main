# This recipe requires ubuntu netinst image installed 
# into node["cobbler"]["precise-x86_64_iso"]
# it requires also ssh key generated in /root/.ssh


template "#{node.cobbler.preseed_dir}/centos-6.2-x86_64.ks" do
  source "centos-6.2-x86_64.ks"
  owner "root"
  group "root"
  mode "0644"
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

