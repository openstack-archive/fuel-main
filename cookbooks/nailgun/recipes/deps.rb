virtualenv "#{node[:nailgun][:venv]}" do
  site_packages false
end

{
  'django-piston' => '0.2.3-20120528',
  'django-celery' => '2.5.5',
  'redis' => '2.4.12',
  'jsonfield' => '0.9',
  'django-nose' => '1.0',
  'simplejson' => '2.5.2'
}.each do |package, version|
  local_python_pip package do
    version version
    virtualenv node.nailgun.venv
  end
end

['python-paramiko'].each do |deb|
  package deb do
    action :install
  end
end

