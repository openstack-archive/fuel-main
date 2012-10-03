Dir.glob("#{node[:nailgun][:root]}/naily/agent/*").each do |agent|
  link agent do
    to "/usr/share/mcollective/plugins/mcollective/agent/" + File.basename(agent)
  end
end

link "#{node[:nailgun][:root]}/naily/puppet/modules/nailytest" do
  to "/etc/puppet/modules/nailytest"
end

link "#{node[:nailgun][:root]}/naily/puppet/manifests/site.pp" do
  to "/etc/puppet/manifests/site.pp"
end
