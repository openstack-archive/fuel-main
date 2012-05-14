
python_pip 'Django' do
  version node[:django][:version] if node[:django][:version]
  action :install
end

