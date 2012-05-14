node['redis2']['instances'].keys.filter { |k| k == "default" }.each do |instance_name|
  unless node['redis2']['instances'][instance_name]['port']
    Chef::Log.warn "Skipping redis instance #{instance_name} because no port is defined for it"
  else
    redis_instance instance_name
  end
end
