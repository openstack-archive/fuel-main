{
  'xmlbuilder' => '1.0',
  'PyYAML' => '3.1',
  'lxml' => '2.3.2',
  'ipaddr' => '2.1.10',
}.each do |package, version|
  python_pip package do
    version version
    action :install
  end

  # httpclient is for node agent
  gem_package "httpclient"
end
