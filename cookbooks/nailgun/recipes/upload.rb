releases = Dir.glob("#{node[:nailgun][:root]}/os-cookbooks/releases/*.json")
releases.each do |rls|
  bash "Bash script for release creation #{rls}" do
    code <<-EOH
    #{node[:nailgun][:root]}/bin/create_release -f "#{rls}"
    EOH
  end
end
