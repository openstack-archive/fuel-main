require 'pathname'
require Pathname.new(__FILE__).dirname.dirname.expand_path + 'corosync'

Puppet::Type.type(:cs_commit).provide(:crm, :parent => Puppet::Provider::Corosync) do
  commands :crm => 'crm'
  commands :crm_attribute => 'crm_attribute'
  commands :crm_shadow => 'crm_shadow'
  def self.instances
    block_until_ready
    []
  end

  def sync(cib)
    self.class.block_until_ready
    begin
      crm_shadow '--force', '--commit', cib
    rescue Puppet::ExecutionFailure => e
      #FIXME(aglarendil): reckless retry to commit shadow again
      #lp/bug1283062
      debug("shadow commit failed. trying one more time")
      if e =~ /Application of an update diff failed/
        crm_shadow '--force', '--commit', cib
      end
    end
  end
end
