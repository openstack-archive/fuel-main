{
  'xmlbuilder' => '1.0',
  'PyYAML' => '3.1',
  'lxml' => '2.3.2',
  'mock' => '0.8.0',
}.each do |package, version|
  python_pip package do
    version version
    action :install
  end

  cookbook_python_pip 'ipaddr' do
    version '2.1.10'
  end
  # httpclient is for node agent
  gem_package "httpclient"
end
