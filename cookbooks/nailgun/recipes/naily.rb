include_recipe "puppet::master"

# Chef's link resource doesn't process directory link, so we end up with bash script
bash "Link Puppet test module" do
  code <<-EOH
  ln -sfT `readlink -f "#{node[:nailgun][:root]}/orchestrator/puppet/modules/nailytest"` /etc/puppet/modules/nailytest
  EOH
end

link "#{node[:nailgun][:root]}/orchestrator/puppet/manifests/site.pp" do
  to "/etc/puppet/manifests/site.pp"
end
