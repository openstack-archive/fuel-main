require 'pathname'
require Pathname.new(__FILE__).dirname.dirname.expand_path + 'corosync'

Puppet::Type.type(:cs_resource).provide(:crm, :parent => Puppet::Provider::Corosync) do
  desc 'Specific provider for a rather specific type since I currently have no
        plan to abstract corosync/pacemaker vs. keepalived.  Primitives in
        Corosync are the thing we desire to monitor; websites, ipaddresses,
        databases, etc, etc.  Here we manage the creation and deletion of
        these primitives.  We will accept a hash for what Corosync calls
        operations and parameters.  A hash is used instead of constucting a
        better model since these values can be almost anything.'

  # Path to the crm binary for interacting with the cluster configuration.
  commands :crm => 'crm'
  commands :crm_attribute => 'crm_attribute'
  def self.instances

    block_until_ready

    instances = []

    # cmd = [ command(:crm), 'configure', 'show', 'xml' ]
    raw, status = dump_cib
    doc = REXML::Document.new(raw)

    # We are obtaining four different sets of data in this block.  We obtain
    # key/value pairs for basic primitive information (which Corosync stores
    # in the configuration as "resources").  After getting that basic data we
    # descend into parameters, operations (which the config labels as
    # instance_attributes and operations), and metadata then generate embedded
    # hash structures of each entry.
    REXML::XPath.each(doc, '//primitive') do |e|

      primitive = {}
      items = e.attributes
      primitive.merge!({
        items['id'].to_sym => {
        :class    => items['class'],
        :type     => items['type'],
        :provider => items['provider']
        }
      })

      primitive[items['id'].to_sym][:parameters]  = {}
      primitive[items['id'].to_sym][:operations]  = {}
      primitive[items['id'].to_sym][:metadata]    = {}
      primitive[items['id'].to_sym][:ms_metadata] = {}
      primitive[items['id'].to_sym][:multistate_hash]  = {}

      if ! e.elements['instance_attributes'].nil?
        e.elements['instance_attributes'].each_element do |i|
          primitive[items['id'].to_sym][:parameters][(i.attributes['name'])] = i.attributes['value']
        end
      end

      if ! e.elements['meta_attributes'].nil?
        e.elements['meta_attributes'].each_element do |m|
          primitive[items['id'].to_sym][:metadata][(m.attributes['name'])] = m.attributes['value']
        end
      end

      if ! e.elements['operations'].nil?
        e.elements['operations'].each_element do |o|
          valids = o.attributes.reject do |k,v| k == 'id' end
          if valids['role']
            op_name = "#{valids['name']}:#{valids['role']}" #.to_sym()
          else
            op_name = valids['name'] #.to_sym()
          end
          primitive[items['id'].to_sym][:operations][op_name] = {}
          valids.each do |k,v|
            primitive[items['id'].to_sym][:operations][op_name][k] = v if k != 'name'
          end
        end
      end
      if e.parent.name == 'master' or e.parent.name == 'clone'
        primitive[items['id'].to_sym][:multistate_hash][:name] = e.parent.attributes['id']
        primitive[items['id'].to_sym][:multistate_hash][:type] = e.parent.name
        if ! e.parent.elements['meta_attributes'].nil?
          e.parent.elements['meta_attributes'].each_element do |m|
            primitive[items['id'].to_sym][:ms_metadata][(m.attributes['name'])] = m.attributes['value']
          end
        end
      end
      primitive_instance = {
        :name            => primitive.first[0],
        :ensure          => :present,
        :primitive_class => primitive.first[1][:class],
        :provided_by     => primitive.first[1][:provider],
        :primitive_type  => primitive.first[1][:type],
        :parameters      => primitive.first[1][:parameters],
        :operations      => primitive.first[1][:operations],
        :metadata        => primitive.first[1][:metadata],
        :ms_metadata     => primitive.first[1][:ms_metadata],
        :multistate_hash      => primitive.first[1][:multistate_hash],
        :provider        => self.name
      }

      instances << new(primitive_instance)
    end
    instances
  end

  # Create just adds our resource to the property_hash and flush will take care
  # of actually doing the work.
  def create
    @property_hash = {
      :name            => @resource[:name],
      :ensure          => :present,
      :primitive_class => @resource[:primitive_class],
      :provided_by     => @resource[:provided_by],
      :primitive_type  => @resource[:primitive_type],
      :multistate_hash      => @resource[:multistate_hash],
    }
    @property_hash[:parameters] = @resource[:parameters] if ! @resource[:parameters].nil?
    @property_hash[:operations] = @resource[:operations] if ! @resource[:operations].nil?
    @property_hash[:metadata] = @resource[:metadata] if ! @resource[:metadata].nil?
    @property_hash[:ms_metadata] = @resource[:ms_metadata] if ! @resource[:ms_metadata].nil?
    @property_hash[:cib] = @resource[:cib] if ! @resource[:cib].nil?
  end

  # Unlike create we actually immediately delete the item.  Corosync forces us
  # to "stop" the primitive before we are able to remove it.
  def destroy
    debug('Stopping primitive before removing it')
    crm('resource', 'cleanup', @resource[:name])
    crm('resource', 'manage', @resource[:name])
    crm('resource', 'stop', @resource[:name])
    debug('Removing primitive')
    try_command("delete",@resource[:name])
    @property_hash.clear
  end

  # Getters that obtains the parameters and operations defined in our primitive
  # that have been populated by prefetch or instances (depends on if your using
  # puppet resource or not).
  def parameters
    @property_hash[:parameters]
  end

  def operations
    @property_hash[:operations]
  end

  def metadata
    @property_hash[:metadata]
  end

  def ms_metadata
    @property_hash[:ms_metadata]
  end

  def multistate_hash
    @property_hash[:multistate_hash]
  end

  # Our setters for parameters and operations.  Setters are used when the
  # resource already exists so we just update the current value in the
  # property_hash and doing this marks it to be flushed.
  def parameters=(should)
    @property_hash[:parameters] = should
  end

  def operations=(should)
    @property_hash[:operations] = should
  end

  def metadata=(should)
    @property_hash[:metadata] = should
  end

  def ms_metadata=(should)
    @property_hash[:ms_metadata] = should
  end

  def multistate_hash=(should)
    #Check if we use default multistate name
    #if it is empty
    if should[:type] and  should[:name].to_s.empty?
      newname = "#{should[:type]}_#{@property_hash[:name]}"
    else
      newname = should[:name]
    end
    if (should[:type] != @property_hash[:multistate_hash][:type] and @property_hash[:multistate_hash][:type])
      #If the type of resource has changed
      #simply stop and delete it both in live
      #and shadow cib

      crm('resource', 'stop', "#{@property_hash[:multistate_hash][:name]}")
      try_command("delete",@property_hash[:multistate_hash][:name])
      try_command("delete",@property_hash[:multistate_hash][:name],nil,@resource[:cib])
    elsif
    #otherwise, stop it and rename it both
    #in shadow and live cib
    (should[:type] == @property_hash[:multistate_hash][:type] and @property_hash[:multistate_hash][:type]  and
    newname != @property_hash[:multistate_hash][:name])
      crm('resource', 'stop', "#{@property_hash[:multistate_hash][:name]}")
      try_command("rename",@property_hash[:multistate_hash][:name],newname)
      try_command("rename",@property_hash[:multistate_hash][:name],newname,@resource[:cib])
    end
    @property_hash[:multistate_hash][:name] = newname
    @property_hash[:multistate_hash][:type] = should[:type]
  end

  # Flush is triggered on anything that has been detected as being
  # modified in the property_hash.  It generates a temporary file with
  # the updates that need to be made.  The temporary file is then used
  # as stdin for the crm command.  We have to do a bit of munging of our
  # operations and parameters hash to eventually flatten them into a string
  # that can be used by the crm command.
  def flush
    unless @property_hash.empty?
      self.class.block_until_ready
      unless @property_hash[:operations].empty?
        operations = ''
        @property_hash[:operations].each do |o|
          op_namerole = o[0].to_s.split(':')
          if op_namerole[1]
            o[1]['role'] = o[1]['role'] || op_namerole[1]  # Hash['role'] has more priority, than Name
          end
          operations << "op #{op_namerole[0]} "
          o[1].each_pair do |k,v|
            operations << "#{k}=#{v} "
          end
        end
      end
      unless @property_hash[:parameters].empty?
        parameters = 'params '
        @property_hash[:parameters].each_pair do |k,v|
          parameters << "#{k}=#{v} "
        end
      end
      unless @property_hash[:metadata].empty?
        metadatas = 'meta '
        @property_hash[:metadata].each_pair do |k,v|
          metadatas << "#{k}=#{v} "
        end
      end
      updated = "primitive "
      updated << "#{@property_hash[:name]} #{@property_hash[:primitive_class]}:"
      updated << "#{@property_hash[:provided_by]}:" if @property_hash[:provided_by]
      updated << "#{@property_hash[:primitive_type]} "
      updated << "#{operations} " unless operations.nil?
      updated << "#{parameters} " unless parameters.nil?
      updated << "#{metadatas} " unless metadatas.nil?

      if ( @property_hash[:multistate_hash][:type] == "master" or @property_hash[:multistate_hash][:type] == "clone" )
        debug("creating multistate #{@property_hash[:multistate_hash][:type]} resource for #{@property_hash[:multistate_hash][:name]}")
        crm_name =  @property_hash[:multistate_hash][:type] == "master" ? :ms : :clone
        updated << "\n"
        updated << " #{crm_name} #{@property_hash[:multistate_hash][:name]} #{@property_hash[:name]} "
        unless @property_hash[:ms_metadata].empty?
          updated << 'meta '
          @property_hash[:ms_metadata].each_pair do |k,v|
            updated << "#{k}=#{v} "
          end
        end
      end
      debug("will update tmp file with #{updated}")
      Tempfile.open('puppet_crm_update') do |tmpfile|
        tmpfile.write(updated)
        tmpfile.flush
        env = {}
        env["CIB_shadow"] = @resource[:cib].to_s if !@resource[:cib].nil?
        exec_withenv("#{command(:crm)} configure load update #{tmpfile.path.to_s}",env)
      end
    end
  end
end
