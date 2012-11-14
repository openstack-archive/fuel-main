require 'puppet'

module Puppet

  Puppet::Type.newtype(:network_route) do
    @doc = "The route configuration type"

    ensurable

    newparam(:exclusive) do
      d = "Enforces that no route configuration exists besides what puppet defines.\n"
      d << "Enabled by default, set it to false in any resource to disable globally."
      desc(d)

      newvalues(:true, :false)
      # this behaviorally defaults to true (see network_scripts.rb exists?()/initialize())
      # using defaultto(:true) would prevent users from setting this to false
    end

    newparam(:device) do
      isnamevar
      desc "The network device for which route will be configured"
    end

    newparam(:routes) do
      desc "The routes to be configured"
    end
  end
end
