node.set[:django][:venv] = node.nailgun.venv
include_recipe 'django'

# FIXME
# it is nice to encapsulate all these components into os package
# installing deps, creating system user, installing nailgun files

include_recipe 'nailgun::deps'

group node.nailgun.group do
  action :create
end

user node.nailgun.user do
  home node.nailgun.root
  gid node.nailgun.group
  system true
end

group 'www-data' do
  members [node.nailgun.user]
  append true
  system true
end

directory node.nailgun.root do
  user node.nailgun.user
  group node.nailgun.group
  mode '755'
end

directory '/var/www' do
  group 'www-data'
  mode '775'
end

directory "/var/log/nailgun" do
  owner node.nailgun.user
  group node.nailgun.group
  mode '755'
  recursive true
end

# FIXME
# cobbler parameters needed to be defined via attributes

template "#{node.nailgun.root}/nailgun/extrasettings.py" do
  source 'extrasettings.py.erb'
  owner node.nailgun.user
  group node.nailgun.group
  mode '644'
  variables(
            :level => "DEBUG",
            :filename => "/var/log/nailgun/nailgun.log",
            :sshkey => "#{node.nailgun.root}/.ssh/id_rsa",
            :bootstrap_sshkey => "#{node.nailgun.root}/.ssh/bootstrap.rsa",
            :cobbler_address => "localhost",
            :cobbler_user => "cobbler",
            :cobbler_password => "cobbler",
            :cobbler_profile => "centos-6.2-x86_64"
            )
end

ssh_keygen "Nailgun ssh-keygen" do
  homedir node.nailgun.root
  username node.nailgun.user
  groupname node.nailgun.group
  keytype 'rsa'
end

ssh_keygen "Root ssh-keygen" do
  homedir "/root"
  username "root"
  groupname "root"
  keytype 'rsa'
end

# FIXME
file "#{node.nailgun.root}/.ssh/bootstrap.rsa" do
  mode 0600
  owner node.nailgun.user
  group node.nailgun.group
end

file "#{node[:nailgun][:root]}/nailgun/venv.py" do
  content "VENV = '#{node[:nailgun][:venv]}/local/lib/python2.7/site-packages'
"
  owner node.nailgun.user
  group node.nailgun.group
  mode '644'
end

# it is assumed that nailgun files already installed into nailgun.root
execute 'chown nailgun root' do
  command "chown -R #{node[:nailgun][:user]}:#{node[:nailgun][:group]} #{node[:nailgun][:root]}"
end

execute 'chmod nailgun root' do
  command "chmod -R u+w #{node[:nailgun][:root]}"
end

# execute 'Preseed Nailgun database' do
#   command "#{node[:nailgun][:python]} manage.py loaddata nailgun/fixtures/default_env.json"
#   cwd node.nailgun.root
#   user node.nailgun.user
#   action :nothing
# end

execute 'Sync Nailgun database' do
  command "#{node[:nailgun][:python]} manage.py syncdb --noinput"
  cwd node.nailgun.root
  user node.nailgun.user
  # notifies :run, resources('execute[Preseed Nailgun database]')
  not_if "test -e #{node[:nailgun][:root]}/nailgun.sqlite"
end

redis_instance 'nailgun'

celery_instance 'nailgun-jobserver' do
  command "#{node[:nailgun][:python]} manage.py celeryd_multi start Worker -E"
  cwd node.nailgun.root
  events true
  user node.nailgun.user
  virtualenv node.nailgun.venv
end

web_app 'nailgun' do
  template 'apache2-site.conf.erb'
end

