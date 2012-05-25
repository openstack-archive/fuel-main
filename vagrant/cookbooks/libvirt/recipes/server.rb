
package 'libvirt-bin'
package 'sasl2-bin'

service 'libvirt-bin' do
  action :start
end

service 'saslauthd' do
  action :start
end

group 'libvirtd' do
  members ['vagrant']
  action :modify
end

template '/etc/libvirt/libvirtd.conf' do
  source 'libvirtd.conf.erb'
  mode 0644

  notifies :restart, resources('service[libvirt-bin]')
end

execute 'set vagrant sasl2 password' do
  command "echo vagrant | saslpasswd2 -a libvirt vagrant"
end

package 'qemu'

