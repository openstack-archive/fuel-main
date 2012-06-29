# This recipe requires bootstrap kernel and initrd 
# installed into node.cobbler.bootstrap_kernel and
# node.cobbler.bootstrap_initrd correspondently 

link "#{node.cobbler.ks_mirror_dir}/bootstrap" do
  to "#{node["cobbler"]["bootstrap_mnt"]}" 
end

# directory "#{node.cobbler.ks_mirror_dir}/bootstrap" do
#   owner "root"
#   group "root"
#   mode "0755"
#   recursive true
#   action :create
# end

# link "#{node.cobbler.ks_mirror_dir}/bootstrap/linux" do
#   to "#{node.cobbler.bootstrap_kernel}"
#   link_type :hard
# end

# link "#{node.cobbler.ks_mirror_dir}/bootstrap/initrd.gz" do
#   to "#{node.cobbler.bootstrap_initrd}"
#   link_type :hard
# end

cobbler_distro "bootstrap" do
  kernel "#{node.cobbler.ks_mirror_dir}/bootstrap/linux"
  initrd "#{node.cobbler.ks_mirror_dir}/bootstrap/initrd.gz"
  arch "x86_64"
  breed "ubuntu"
  osversion "precise"
end

cobbler_profile "bootstrap" do
  kopts "root=/dev/ram0 rw ramdisk_size=614400"
  distro "bootstrap"
  menu true
end

cobbler_system "default" do
  profile "bootstrap"
  netboot true
end

