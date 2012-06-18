# Here are packages cobbler needs to have to work correctly

package "cobbler" do
  action :install
  response_file "cobbler.seed"
end

package "cobbler-web" do
  action :install
end

package "tftpd-hpa" do
  action :install
end

package "dnsmasq" do
  action :install
end

service "cobbler" do
  supports :restart => true 
  action :start
end

service "dnsmasq" do
  supports :restart => true 
  action :start
end

template "/etc/cobbler/modules.conf" do
  source "modules.conf.erb"
  mode 0644
  notifies :restart, ["service[cobbler]", "service[dnsmasq]"]
end

template "/etc/cobbler/settings" do
  source "settings.erb"
  mode 0644
  variables(
            :next_server => node["cobbler"]["next_server"],
            :server => node["cobbler"]["server"]
  )
  notifies :restart, "service[cobbler]"
end

execute "cobbler_sync" do
  command "cobbler sync"
  returns [0,155]
  action :nothing
end

template "/etc/cobbler/dnsmasq.template" do
  source "dnsmasq.template.erb"
  mode 0644
  variables(
            :dhcp_range => node["cobbler"]["dhcp_range"],
            :gateway => node["cobbler"]["gateway"]
            )
  notifies :run, "execute[cobbler_sync]"
end

template "/etc/cobbler/pxe/pxedefault.template" do
  source "pxedefault.template.erb"
  mode 0644
  variables(
            :pxetimeout => node["cobbler"]["pxetimeout"]
            )
  notifies :run, "execute[cobbler_sync]" 
end

directory node["cobbler"]["bootstrap_images_dir"] do
  owner "root"
  group "root"
  mode "0755"
  recursive true
  action :create
end

directory node["cobbler"]["bootstrap_ks_mirror_dir"] do
  owner "root"
  group "root"
  mode "0755"
  recursive true
  action :create
end



# FIXME
# maybe separate recipe only needed for development to resolv mirantis private names

# file "/etc/dnsmasq.d/mirantis.net.conf" do
#   action :create
#   content "server=/mirantis.net/#{node["cobbler"]["updns"]}"
#   mode 0644
#   notifies :restart, "service[dnsmasq]"
# end

link "#{node["cobbler"]["bootstrap_ks_mirror_dir"]}/linux" do
  to "#{node["cobbler"]["bootstrap_kernel"]}"
  link_type :hard
end

link "#{node["cobbler"]["bootstrap_ks_mirror_dir"]}/initrd.gz" do
  to "#{node["cobbler"]["bootstrap_initrd"]}"
  link_type :hard
end

# FIXME 

execute "add_bootstrap_distro" do 
  command "cobbler distro add \
--name=bootstrap \
--kernel=#{node["cobbler"]["bootstrap_ks_mirror_dir"]}/linux \
--initrd=#{node["cobbler"]["bootstrap_ks_mirror_dir"]}/initrd.gz \
--arch=x86_64 \
--breed=ubuntu \
--os-version=precise"
  action :run
  only_if "test -z `cobbler distro find --name bootstrap`"
end

execute "edit_bootstrap_distro" do 
  command "cobbler distro edit \
--name=bootstrap \
--kernel=#{node["cobbler"]["bootstrap_ks_mirror_dir"]}/linux \
--initrd=#{node["cobbler"]["bootstrap_ks_mirror_dir"]}/initrd.gz \
--arch=x86_64 \
--breed=ubuntu \
--os-version=precise"
  action :run
  only_if "test ! -z `cobbler distro find --name bootstrap`"
end


# FIXME

execute "add_bootstrap_profile" do
  command "cobbler profile add \
--name=bootstrap \
--distro=bootstrap \
--enable-menu=True \
--kopts=\"root=/dev/ram0 rw ramdisk_size=614400\""
  action :run
  only_if "test -z `cobbler profile find --name bootstrap`"
end

execute "edit_bootstrap_profile" do
  command "cobbler profile edit \
--name=bootstrap \
--distro=bootstrap \
--enable-menu=True \
--kopts=\"root=/dev/ram0 rw ramdisk_size=614400\""
  action :run
  only_if "test ! -z `cobbler profile find --name bootstrap`"
end

# FIXME

execute "add_bootstrap_system" do
  command "cobbler system add \
--name=default \
--profile=bootstrap \
--netboot-enabled=1"
  action :run
  only_if "test -z `cobbler profile find --name default`"
end

execute "edit_bootstrap_system" do
  command "cobbler system edit \
--name=default \
--profile=bootstrap \
--netboot-enabled=1"
  action :run
  only_if "test ! -z `cobbler profile find --name default`"
end




