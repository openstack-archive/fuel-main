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
  'jsonfield' => '0.9',
  'simplejson' => '2.5.2',
  'paramiko' => '1.7.7.2',
  'pycrypto' => '2.6',
  'ipaddr' => '2.1.10',
  'netaddr' => '0.7.10',
  'eventlet' => '0.9.17',
  'greenlet' => '0.4.0',
  'web.py' => '0.37',
  'SQLAlchemy' => '0.7.8',
  'Paste' => '1.7.5.1',
  'kombu' => '2.1.8',
  'nose' => '1.1.2',
}.each do |package, version|
  local_python_pip package do
    version version
    virtualenv node.nailgun.venv
  end
end


