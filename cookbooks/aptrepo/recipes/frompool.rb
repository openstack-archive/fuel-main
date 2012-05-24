package "apt-utils" do
  action :install
end


repodirs = [node["aptrepo"]["repoconf.d"],
            node["aptrepo"]["repoindices"],
            node["aptrepo"]["repocache"]]
node["aptrepo"]["sections"].each do |s|
  node["aptrepo"]["architectures"].each do |a|
    repodirs.push("#{node["aptrepo"]["reporoot"]}/dists/#{node["aptrepo"]["release"]}/#{s}/binary-#{a}")
  end
end

repodirs.each do |d|
  directory d do
    owner "root"
    group "root"
    mode "0755"
    recursive true
    action :create
  end
end


template "#{node["aptrepo"]["repoconf.d"]}/apt-ftparchive.conf" do
  variables(
            :release => node["aptrepo"]["release"],
            :reporoot => node["aptrepo"]["reporoot"],
            :repoindices => node["aptrepo"]["repoindices"],
            :repocache => node["aptrepo"]["repocache"],
            :architectures => node["aptrepo"]["architectures"].join(" "),
            :sections => node["aptrepo"]["sections"].join(" ")
            )
end

