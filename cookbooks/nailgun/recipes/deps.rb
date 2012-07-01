include_recipe "python"

virtualenv "#{node[:nailgun][:venv]}" do
  site_packages false
end

['libxml2-dev', 'python-dev', 'python-paramiko', 'ruby-httpclient'].each do |deb|
  package deb do
    action :install
  end
end


{
  'django-piston' => '0.2.3-20120528',
  'django-celery' => '2.5.5',
  'redis' => '2.4.12',
  'jsonfield' => '0.9',
  'django-nose' => '1.0',
  'simplejson' => '2.5.2',
  'paramiko' => '1.7.7.2',
  'pycrypto' => '2.6',
  'ipaddr' => '2.1.20',
}.each do |package, version|
  local_python_pip package do
    version version
    virtualenv node.nailgun.venv
  end
end


