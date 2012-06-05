package "python#{node.python.version}" do
  action :install
end

package "python-pip" do
  action :install
end

package "python-virtualenv" do
  action :install
end
