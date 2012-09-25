include_recipe "python"
include_recipe "rabbitmq"

['libxml2-dev', 'python-dev', 'python-paramiko', 'ruby-httpclient'].each do |deb|
  package deb do
    action :install
  end
end


{
  'pycrypto' => '2.6',
  'netaddr' => '0.7.10',
  'eventlet' => '0.9.17',
  'greenlet' => '0.4.0',
  'web.py' => '0.37',
  'SQLAlchemy' => '0.7.8',
  'Paste' => '1.7.5.1',
  'kombu' => '2.1.8',
  'wsgilog' => '0.3'
}.each do |package, version|
  python_pip package do
    version version
  end
end


