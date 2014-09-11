require 'pathname'
require Pathname.new(__FILE__).dirname.dirname.expand_path + 'corosync_service'
require 'rexml/document'
require 'open3'

include REXML

Puppet::Type.type(:service).provide :pacemaker, :parent => Puppet::Provider::Corosync_service do

  commands :crm => 'crm'
  commands :cibadmin => 'cibadmin'
  commands :crm_attribute => 'crm_attribute'
  commands :crm_resource => 'crm_resource'

  desc "Pacemaker service management."

  has_feature :refreshable
  has_feature :enableable
  has_feature :ensurable
  def self.get_cib
    raw, _status = dump_cib
    @@cib=REXML::Document.new(raw)
  end

  # List all services of this type.
  def self.instances
    get_services
  end

  #Return list of pacemaker resources
  def self.get_resources
    @@resources = @@cib.root.elements['configuration'].elements['resources']
  end

  #Get services list
  def self.get_services
    get_cib
    get_resources
    instances = []
    XPath.match(@@resources, '//primitive').each do |element|
      if !element.nil?
        instances << new(:name => element.attributes['id'], :hasstatus => true, :hasrestart => false)
      end
    end
    instances
  end

  def get_service_hash
    self.class.get_cib
    self.class.get_resources
    @service={}
    default_start_timeout = 30
    default_stop_timeout = 30
    cib_resource =  XPath.match(@@resources, "//primitive[@id=\'#{@resource[:name]}\']").first
    raise(Puppet::Error,"resource #{@resource[:name]} not found") unless cib_resource
    @service[:msname] = ['master','clone'].include?(cib_resource.parent.name) ? cib_resource.parent.attributes['id'] : nil
    @service[:name] = @resource[:name]
    @service[:class] = cib_resource.attributes['class']
    @service[:provider] = cib_resource.attributes['provider']
    @service[:type] = cib_resource.attributes['type']
    @service[:metadata] = {}
    if !cib_resource.elements['meta_attributes'].nil?
      cib_resource.elements['meta_attributes'].each_element do |m|
        @service[:metadata][m.attributes['name'].to_sym] = m.attributes['value']
      end
    end
    if @service[:class] == 'ocf'
      stdout = Open3.popen3("/bin/bash -c 'OCF_ROOT=/usr/lib/ocf /usr/lib/ocf/resource.d/#{@service[:provider]}/#{@service[:type]} meta-data'")[1].read
      metadata = REXML::Document.new(stdout)
      default_start_timeout = XPath.match(metadata, "//actions/action[@name=\'start\']").first.attributes['timeout'].to_i
      default_stop_timeout = XPath.match(metadata, "//actions/action[@name=\'stop\']").first.attributes['timeout'].to_i
    end
    op_start=XPath.match(REXML::Document.new(cib_resource.to_s),"//operations/op[@name='start']").first
    op_stop=XPath.match(REXML::Document.new(cib_resource.to_s),"//operations/op[@name='stop']").first
    @service[:start_timeout] =  default_start_timeout
    @service[:stop_timeout] =  default_stop_timeout
    if !op_start.nil?
      @service[:start_timeout] = op_start.attributes['timeout'].to_i
    end
    if !op_stop.nil?
      @service[:stop_timeout] = op_stop.attributes['timeout'].to_i
    end
  end

  def get_service_name
    get_service_hash
    service_name = @service[:msname] ? @service[:msname] : @service[:name]
  end

  def self.get_stonith
    get_cib
    stonith = XPath.first(@@cib,"crm_config/nvpair[@name='stonith-enabled']")
    @@stonith = stonith == "true"
  end

  def self.get_node_state_stonith(ha_state,in_ccm,crmd,join,expected,shutdown)
    if (in_ccm == "true") && (ha_state == 'active') && (crmd == 'online')
      case join
      when 'member'
        state = :online
      when 'expected'
        state = :offline
      when 'pending'
        state = :pending
      when 'banned'
        state = :standby
      else
        state = :unclean
      end
    elsif !(in_ccm == "true") && (ha_state =='dead') && (crmd == 'offline') && !(shutdown == 0)
      state = :offline
    elsif shutdown == 0
      state = :unclean
    else
      state = :offline
    end
    state
  end

  def self.get_node_state_no_stonith(ha_state,in_ccm,crmd,join,expected,shutdown)
    state = :unclean
    if !(in_ccm == "true") || (ha_state == 'dead')
      state = :offline
    elsif crmd == 'online'
      if join == 'member'
        state = :online
      else
        state = :offline
      end
    elsif !(shutdown == "0")
      state = :offline
    else
      state = :unclean
    end
    state
  end

  def self.get_node_state(*args)
    get_stonith
    if @@stonith
      return get_node_state_stonith(*args)
    else
      return get_node_state_no_stonith(*args)
    end
  end

  def self.get_nodes
    @@nodes = []
    get_cib
    nodes = XPath.match(@@cib,'cib/configuration/nodes/node')
    nodes.each do |node|
      state = :unclean
      uname = node.attributes['uname']
      node_state = XPath.first(@@cib,"cib/status/node_state[@uname='#{uname}']")
      if node_state
        ha_state = node_state.attributes['ha'] == 'dead' ? 'dead' : 'active'
        in_ccm  = node_state.attributes['in_ccm']
        crmd = node_state.attributes['crmd']
        join = node_state.attributes['join']
        expected = node_state.attributes['expected']
        shutdown = node_state.attributes['shutdown'].nil? ? 0 : node_state.attributes['shutdown']
        state = get_node_state(ha_state,in_ccm,crmd,join,expected,shutdown)
        if state == :online
          standby = node.elements["instance_attributes/nvpair[@name='standby']"]
          if standby && ['true', 'yes', '1', 'on'].include?(standby.attributes['value'])
            state = :standby
          end
        end
      end
      @@nodes << {:uname => uname, :state => state}
    end
  end

  def get_last_successful_operations
    debug("getting last operations")
    self.class.get_cib
    self.class.get_nodes
    @last_successful_operations = []
    begin
      @@nodes.each do |node|
        next unless node[:state] == :online
        debug("getting last ops on #{node[:uname]} for #{@resource[:name]}")
        all_operations =  XPath.match(@@cib,"cib/status/node_state[@uname='#{node[:uname]}']/lrm/lrm_resources/lrm_resource/lrm_rsc_op[starts-with(@id,'#{@resource[:name]}')]")
        debug("ALL OPERATIONS:\n\n #{all_operations.inspect}")
        next if all_operations.nil?
        completed_ops = all_operations.select{|op| op.attributes['op-status'].to_i != -1 }
        debug("COMPLETED OPERATIONS:\n\n #{completed_ops.inspect}")
        next if completed_ops.nil?
        start_stop_ops = completed_ops.select{|op| ["start","stop","monitor","promote"].include? op.attributes['operation']}
        debug("START/STOP OPERATIONS:\n\n #{start_stop_ops.inspect}")
        next if start_stop_ops.nil?
        sorted_operations = start_stop_ops.sort do
          |a,b| a.attributes['call-id'].to_i <=> b.attributes['call-id'].to_i
        end
        good_operations = sorted_operations.select do |op|
          op.attributes['rc-code'] == '0' or
          op.attributes['operation'] == 'monitor'
        end
        debug("GOOD OPERATIONS :\n\n #{good_operations.inspect}")
        next if good_operations.nil?
        last_op = good_operations.last
        debug("LAST GOOD OPERATION :\n\n '#{last_op.inspect}' '#{last_op.nil?}' '#{last_op}'")
        next if last_op.nil?
        last_successful_op = nil
        if ['promote','start','stop'].include?(last_op.attributes['operation'])
          debug("last operations: #{last_op.attributes['operation']}")
          last_successful_op = last_op.attributes['operation']
        else
          if last_op.attributes['rc-code'].to_i == 0
            last_successful_op = 'start'
          elsif  last_op.attributes['rc-code'].to_i == 8
            last_successful_op = 'start'
          else
            last_successful_op = 'stop'
            if last_op.attributes['rc-code'].to_i == 5 and node[:uname] == Facter.value(:pacemaker_hostname)
              crm_resource('--cleanup','--resource',get_service_name,'--node',Facter.value(:pacemaker_hostname))
              sleep 15
              self.class.get_cib
              raise "repeat"
            end
          end
        end
        debug("LAST SUCCESSFUL OP :\n\n #{last_successful_op.inspect}")
        @last_successful_operations << last_successful_op if !last_successful_op.nil?
      end
    rescue  => e
      retry if e.message == 'repeat'
      raise
    end
    @last_successful_operations
  end

  #  def get_operations
  #     XPath.match(@@operations,"lrm_rsc_op")
  #  end

  def enable
    crm('resource','manage', get_service_name)
  end

  def enabled?
    get_service_hash
    @service[:metadata][:'is-managed'] != 'false'
  end

  def disable
    crm('resource','unmanage',get_service_name)
  end

  #TODO: think about per-node start/stop/restart of services

  def start
    get_service_hash
    debug("START PCMK SERVICE: #{get_service_name}")
    crm('resource', 'cleanup', get_service_name)
    enable
    crm('resource', 'start', get_service_name)
    debug("Starting countdown for resource start")
    debug("Start timeout is #{@service[:start_timeout]}")
    Timeout::timeout(5*@service[:start_timeout],Puppet::Error) do
      loop do
        break if status == :running
        sleep 5
      end
    end
    sleep 3
  end

  def stop
    get_service_hash
    debug("STOP PCMK SERVICE: #{get_service_name}")
    crm('resource', 'cleanup', get_service_name)
    enable
    crm('resource', 'stop', get_service_name)
    debug("Starting countdown for resource stop")
    debug("Stop timeout is #{@service[:stop_timeout]}")
    Timeout::timeout(5*@service[:stop_timeout],Puppet::Error) do
      loop do
        break if status == :stopped
        sleep 5
      end
    end
  end

  def restart
    stop
    start
  end

  def status
    #debug(crm('status'))
    get_last_successful_operations
    debug("STATUS PCMK SERVICE: #{get_service_name}")
    crm('resource', 'cleanup', get_service_name)
    if @last_successful_operations.any? {|op| ['start','promote'].include?(op)}
      return :running
    elsif @last_successful_operations.all? {|op| op == 'stop'} or @last_successful_operations.empty?
      return :stopped
    else
      raise(Puppet::Error,"resource #{@resource[:name]} in unknown state")
    end
  end

end

