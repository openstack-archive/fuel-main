package "rsyslog" do
  action :install
end

service "rsyslog" do
  supports :restart => true, :reload => true
  action [:enable, :start]
end

directory "/etc/rsyslog.d" do
  owner "root"
  group "root"
  mode 0755
end

directory "/var/log/remote" do
  owner "syslog"
  group "adm"
  mode 0755
end

template "/etc/default/rsyslog" do
  source "default-rsyslog.erb"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[rsyslog]"
end

template "/etc/rsyslog.d/30-remote-log.conf" do
  source "30-remote-log.conf.erb"
  owner "root"
  group "root"
  mode 0644
  notifies :restart, "service[rsyslog]", :immediately
end

