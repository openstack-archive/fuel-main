# This provider is in development and not ready for production

Puppet::Type.type(:network_route).provide(:interfaces) do

defaultfor :operatingsystem => [:ubuntu, :debian]
  # There are several ways to implement this
  # We can add a post-up/pre-down rules that call ip route
  # or we can scripts in /etc/network/if-up.d /etc/network/if-down.d
end
