bash "Bash script for release creation #{rls}" do
	code <<-EOH
	#{node[:nailgun][:root]}/bin/create_release -f ""#{node[:nailgun][:root]}/openstack-essex.json""
	EOH
end
