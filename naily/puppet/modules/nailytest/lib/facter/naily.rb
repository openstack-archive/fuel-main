require 'facter'

if File.exist?("/etc/naily.facts")
    File.readlines("/etc/naily.facts").each do |line|
        if line =~ /^(.+)=(.+)$/
            var = $1.strip; 
            val = $2.strip

            Facter.add(var) do
                setcode { val }
            end
        end
    end
end
