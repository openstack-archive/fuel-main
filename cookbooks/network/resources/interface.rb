require 'chef/mixin/language_include_recipe'

include Chef::Mixin::LanguageIncludeRecipe

actions :create, :delete, :up, :down

attribute :device, :name_attribute => true, :kind_of => String, :required => true
attribute :vlan, :kind_of => Integer

attribute :address, :kind_of => String
attribute :netmask

attribute :mtu, :kind_of => Integer
attribute :metric, :kind_of => Integer

attribute :onboot, :default => true


attr_accessor :state

def initialize(*args)
  super
  @action = [:create, :up]
end

def up?
  state == :up
end

def down?
  state == :down
end

def device(arg=nil)
  return @device if arg == nil && instance_variable_defined?(:@device)

  # parse device from name
  arg = $1 if /(.+)\.\d+/ =~ name

  @device = validate({:device => (arg || name)}, :device => {:required => true, :kind_of => String})[:device]
end

def vlan(arg=nil)
  return @vlan if arg == nil && instance_variable_defined?(:@vlan)

  # parse vlan from name
  arg ||= $1.to_i if /.+\.(\d+)/ =~ name

  @vlan = validate({:vlan => (arg)}, :vlan => {:kind_of => Integer})[:vlan]
end

def after_created
  include_recipe 'network::vlan_support' if vlan
end

