require 'puppet/util/package'
require 'yaml'
require File.join(File.dirname(__FILE__), 'rpmvercmp.rb')

Puppet::Type.type(:package).provide :yum, :parent => :rpm, :source => :rpm do
  desc "Support via `yum`.

  Using this provider's `uninstallable` feature will not remove dependent packages. To
  remove dependent packages with this provider use the `purgeable` feature, but note this
  feature is destructive and should be used with the utmost care."

  has_feature :versionable

  commands :yum => "yum", :rpm => "rpm", :python => "python"

  self::YUMHELPER = File::join(File::dirname(__FILE__), "yumhelper.py")

  attr_accessor :latest_info

  if command('rpm')
    confine :true => begin
      rpm('--version')
      rescue Puppet::ExecutionFailure
        false
      else
        true
      end
  end

  defaultfor :operatingsystem => [:fedora, :centos, :redhat]

  def self.prefetch(packages)
    raise Puppet::Error, "The yum provider can only be used as root" if Process.euid != 0
    super
    return unless packages.detect { |name, package| package.should(:ensure) == :latest }

    # collect our 'latest' info
    updates = {}
    python(self::YUMHELPER).each_line do |l|
      l.chomp!
      next if l.empty?
      if l[0,4] == "_pkg"
        hash = nevra_to_hash(l[5..-1])
        [hash[:name], "#{hash[:name]}.#{hash[:arch]}"].each  do |n|
          updates[n] ||= []
          updates[n] << hash
        end
      end
    end

    # Add our 'latest' info to the providers.
    packages.each do |name, package|
      if info = updates[package[:name]]
        package.provider.latest_info = info[0]
      end
    end
  end

  def pkg_list
    raw_pkgs = rpm [ '-q', '-a', '--queryformat', '%{NAME}|%{VERSION}-%{RELEASE}\n' ]
    pkgs = {}
    raw_pkgs.split("\n").each do |l|
      line = l.split '|'
      name = line[0]
      version = line[1]
      next if !name || !version
      pkgs.store name, version
    end
    pkgs
  end

  # Substract packages in hash b from packages in hash a
  # in noval is true only package name matters and version is ignored
  # @param a <Hash[String]>
  # @param b <Hash[String]>
  # @param ignore_versions <TrueClass,FalseClass>
  def package_diff(a, b, ignore_versions = false)
    result = a.dup
    b.each_pair do |k, v|
      if a.key? k
        if a[k] == v or ignore_versions
          result.delete k
        end
      end
    end
    result
  end

  # find package names in both a and b hashes
  # values are taken from a
  # @param a <Hash[String]>
  # @param b <Hash[String]>
  def package_updates(a, b)
    common_keys = a.keys & b.keys
    common_keys = a.keys & b.keys
    common_keys.inject({}) { |result, p| result.merge({p => a[p]}) }
  end

  def install
    should = @resource.should(:ensure)
    self.debug "Ensuring => #{should}"
    wanted = @resource[:name]
    operation = :install
    yum_options = %w(-d 0 -e 0 -y)

    @file_dir = '/var/lib/puppet/rollback'

    from = @property_hash[:ensure]
    to = should
    name = @resource[:name]

    Puppet.notice "Installing package #{name} from #{from} to #{to}"

    case should
    when true, false, Symbol
      # pass
      should = nil
    else
      # Add the package version
      wanted += "-#{should}"
      is = self.query
      if is && Rpmvercmp.compare_labels(should, is[:ensure]) < 0
        self.debug "Downgrading package #{@resource[:name]} from version #{is[:ensure]} to #{should}"
        operation = :downgrade
      end
    end

    rollback_file = File.join @file_dir, "#{name}_#{to}_#{from}.yaml"
    diff = read_diff rollback_file

    if diff.is_a?(Hash) && diff.key?('installed') && diff.key?('removed')
      # rollback
      # reverse the update process instead of usuall install
      Puppet.debug "Found rollback file at #{rollback_file}"
      installed = diff['installed']
      removed = diff['removed']
      # calculate package sets
      to_update = package_updates removed, installed
      to_install = package_diff removed, installed
      to_remove = package_diff installed, removed, true
      Puppet.debug "Install: #{to_install.map {|p| "#{p[0]}-#{p[1]}" }. join ' '}" if to_install.any?
      Puppet.debug "Remove: #{to_remove.map {|p| "#{p[0]}-#{p[1]}" }. join ' '}" if to_remove.any?
      Puppet.debug "Update: #{to_update.map {|p| "#{p[0]}-#{p[1]}" }. join ' '}" if to_update.any?
      to_install = to_install.merge to_update
      yum_shell yum_options, operation, to_install, to_remove
    elsif from.is_a?(String) && to.is_a?(String)
      # update form one version to another
      before, after = yum_with_changes yum_options, operation, wanted
      diff = make_package_diff before, after
      file_path = File.join @file_dir, "#{name}_#{from}_#{to}.yaml"
      save_diff file_path, diff
      Puppet.debug "Saving diff file to #{file_path}"
    else
      # just a simple install
      output = yum "-d", "0", "-e", "0", "-y", operation, wanted
    end

    is = check_query
    raise Puppet::Error, "Could not find package #{self.name}" unless is

    # FIXME: Should we raise an exception even if should == :latest
    # and yum updated us to a version other than @param_hash[:ensure] ?
    raise Puppet::Error, "Failed to update to version #{should}, got version #{is[:ensure]} instead" if should && should != is[:ensure]
  end

  # run the yum shell to install and remove packages
  # @param options <Array[String]>
  # @param operation <String,Symbol>
  # @param to_install <Hash>
  # @param to_remove <Hash>
  def yum_shell(options, operation, to_install, to_remove)
    tmp_file = '/tmp/yum.shell'
    yum_shell = ''
    yum_shell += "#{operation} #{to_install.map {|p| "#{p[0]}-#{p[1]}" }. join ' '}\n" if to_install.any?
    yum_shell += "remove #{to_remove.map {|p| "#{p[0]}-#{p[1]}" }. join ' '}\n" if to_remove.any?
    yum_shell += "run\n"
    File.open(tmp_file, 'w') { |file| file.write yum_shell }
    output = yum "--setopt", "obsoletes=0", options, 'shell', tmp_file
    File.delete tmp_file
  end

  # package state query executed after the install to check its success
  # separate method is made because it can be stubbed by the spec
  # @return Hash
  def check_query
    self.query
  end

  # combine before and after lists into a diff
  # @param before <Hash[String]>
  # @param after <Hash[String]>
  def make_package_diff(before, after)
    installed = package_diff after, before
    removed = package_diff before, after
    { 'installed' => installed, 'removed'   => removed }
  end

  # run yum operation and get package
  # lists before and after of it
  # @param options <Array[String]>
  # @param operation <String,Symbol>
  # @param wanted <String>
  def yum_with_changes(options, operation, wanted)
    before = pkg_list
    yum options, operation, wanted
    after = pkg_list
    [ before, after ]
  end

  # saves diff hash into a file
  # @param file_path <String>
  # @param diff <Hash[String]>
  def save_diff(file_path, diff)
    Dir.mkdir @file_dir unless File.directory? @file_dir
    File.open(file_path, 'w') { |file| file.write YAML.dump(diff) + "\n" }
  end

  # reads diff hash from a file
  # @param file_path <String>
  # @returns <Hash[String]>
  def read_diff(file_path)
    return unless File.readable? file_path
    diff = YAML.load_file file_path
    return unless diff.is_a? Hash
    diff
  end

  # What's the latest package version available?
  def latest
    upd = latest_info
    unless upd.nil?
      # FIXME: there could be more than one update for a package
      # because of multiarch
      return "#{upd[:epoch]}:#{upd[:version]}-#{upd[:release]}"
    else
      # Yum didn't find updates, pretend the current
      # version is the latest
      raise Puppet::DevError, "Tried to get latest on a missing package" if properties[:ensure] == :absent
      return properties[:ensure]
    end
  end

  def update
    # Install in yum can be used for update, too
    self.install
  end

  def purge
    yum "-y", :erase, @resource[:name]
  end
end
