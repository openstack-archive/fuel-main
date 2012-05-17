{
  'xmlbuilder' => '1.0',
}.each do |package, version|
  python_pip package do
    version version
    action :install
  end
end
