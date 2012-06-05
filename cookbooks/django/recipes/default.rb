include_recipe "apache2"
include_recipe "apache2::#{node[:django][:web_server]}"

local_python_pip 'Django' do
  version node[:django][:version] if node[:django][:version]
  virtualenv node[:django][:venv]
end
