
case node.platform
when 'centos', 'redhat', 'fedora'
  package 'vconfig'
when 'ubuntu', 'debian'
  package 'vlan'
end

