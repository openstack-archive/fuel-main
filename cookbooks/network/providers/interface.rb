require 'chef/shell_out'

def load_current_resource
  cmd = run_command("ifconfig | awk '/^#{full_device_name} /,/^$/'")

  config = cmd.stdout.strip

  return if config.empty?

  
  interface = Chef::Resource::NetworkInterface.new(new_resource.name)
  interface.vlan @new_resource.vlan
  # interface.hwaddress = $1 if /HWaddr (\S+)/ =~ config
  interface.address $1 if /inet addr:(\S+)/ =~ config
  interface.netmask $1 if /Mask:(\S+)/ =~ config
  interface.mtu $1.to_i if /MTU:(\d+)/ =~ config
  interface.metric $1.to_i if /Metric:(\d+)/ =~ config

  interface.state = (/ UP / =~ config) ? :up : :down

  @current_resource = interface
end

action :create do
  if !current_resource && new_resource.vlan
    Chef::Log.debug("Creating VLAN subinterface #{full_device_name}")
    run_command("vconfig add #{new_resource.device} #{new_resource.vlan}")
  end

  if current_resource == new_resource
    Chef::Log.debug("Skipping configuration of network interface as current configuration matches target one")
    next
  end

  Chef::Log.info("Configuring network interface #{full_device_name}")

  command =  "ifconfig #{full_device_name} #{new_resource.address}"
  command << " netmask #{new_resource.netmask}" if new_resource.netmask
  command << " metric #{new_resource.metric}" if new_resource.metric
  command << " mtu #{new_resource.mtu}" if new_resource.mtu

  Chef::Log.debug("Running command: #{command}")

  run_command(command)

  new_resource.state = current_resource ? current_resource.state : :down
  new_resource.updated_by_last_action(true)

  create_config
end

action :delete do
  if current_resource && current_resource.state != :down
    Chef::Log.info("Disabling network interface #{full_device_name}")

    run_command("ifconfig #{full_device_name} down")

    new_resource.state = :down
    new_resource.updated_by_last_action(true)
  end

  if current_resource && current_resource.vlan
    Chef::Log.debug("Removing networking interface #{full_device_name}")

    run_command("vconfig rem #{full_device_name}")
  end

  delete_config
end

action :up do
  if current_resource && current_resource.state == :up
    Chef::Log.debug("Network interface #{full_device_name} is already up")
    next
  end

  Chef::Log.info("Enabling network interface #{full_device_name}")

  run_command("ifconfig #{full_device_name} up")

  new_resource.state = :up
  new_resource.updated_by_last_action(true)
end

action :down do
  if current_resource && current_resource.state == :down
    Chef::Log.debug("Network interface #{full_device_name} is already down")
    next
  end

  Chef::Log.info("Disabling network interface #{full_device_name}")

  run_command("ifconfig #{full_device_name} down")

  new_resource.state = :down
  new_resource.updated_by_last_action(true)
end

private

def full_device_name
  name = new_resource.device
  name += ".#{new_resource.vlan}" if new_resource.vlan
  name
end

def create_config
  template "/etc/sysconfig/network-scripts/ifcfg-#{full_device_name}" do
    source 'ifcfg.erb'
    owner 'root'
    group 'root'
    mode 0644

    variables({
      :device => new_resource.device,
      :vlan => new_resource.vlan,
      :address => new_resource.address,
      :netmask => new_resource.netmask,
      :onboot => new_resource.onboot,
    })

    action :create
  end
end

def delete_config
  template "/etc/sysconfig/network-scripts/ifcfg-#{full_device_name}" do
    source 'ifcfg.erb'

    action :delete
  end
end

def run_command(command, options={})
  cmd = Chef::ShellOut.new(command, options)
  cmd.run_command
  cmd.error!
  cmd
end

