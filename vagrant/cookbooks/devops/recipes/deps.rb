{
  'xmlbuilder' => '1.0',
  'PyYAML' => '3.1',
  'lxml' => '2.3.2',
}.each do |package, version|
  python_pip package do
    version version
    action :install
  end
end
