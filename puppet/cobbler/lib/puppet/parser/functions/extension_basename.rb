module Puppet::Parser::Functions
  newfunction(:extension_basename, :type => :rvalue) do |args|
    if args[1] and /^(true|1)$/i.match(args[1])
      File.basename(args[0]).split(/\./)[0..-2].join(".")
    else
      File.basename(args[0])
    end
  end
end
