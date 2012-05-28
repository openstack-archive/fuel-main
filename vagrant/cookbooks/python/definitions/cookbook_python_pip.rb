# Install python package right from cookbook.
#
# Example:
#
#   cookbook_python_pip 'foo' do
#     version '0.1.1'
#   end
#
# The package file should be inside files/ tree and have name:
#   <name>-<version>.tar.gz
# or
#   <name>.tar.gz
# if you do not specify version
#
# E.g.
#   foo-0.1.1.tar.gz
#
define :cookbook_python_pip, :version => nil do
  package_file = params[:name]
  package_file += "-#{params[:version]}" if params[:version]
  package_file += '.tar.gz'

  cookbook_file "/tmp/#{package_file}" do
    source params[:source] if params[:source]
    cookbook params[:cookbook] if params[:cookbook]
  end

  python_pip params[:name] do
    package_name "file:///tmp/#{package_file}"
    version 'latest'
  end
end

