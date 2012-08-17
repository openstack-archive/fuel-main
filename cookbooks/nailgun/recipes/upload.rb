cooks = Dir.glob("#{node[:nailgun][:root]}/os-cookbooks/cookbooks/*").select {|f| File.directory? f}
cooks.each do |cook|
  bash "Bash script for cookbook installation #{cook}" do
    code <<-EOH
    #{node[:nailgun][:root]}/bin/install_cookbook "#{cook}"
    EOH
  end
end

releases = Dir.glob("#{node[:nailgun][:root]}/os-cookbooks/releases/*.json")
releases.each do |rls|
  bash "Bash script for release creation #{rls}" do
    code <<-EOH
    #{node[:nailgun][:root]}/bin/create_release -f "#{rls}"
    EOH
  end
end

