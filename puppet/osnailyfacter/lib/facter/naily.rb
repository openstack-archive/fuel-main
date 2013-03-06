require 'facter'

#begin
#  Timeout::timeout(60) do
#    until File.exists?("/etc/naily.facts")
#      File.open("/tmp/facter.log", "a") {|f| f.write("#{Time.now} Waiting for facts\n")}
#      sleep(1)
#    end
#  end
#rescue Timeout::Error
#  File.open("/tmp/facter.log", "a") {|f| f.write("#{Time.now} Tired of waiting\n")}
#end

if File.exist?("/etc/naily.facts")
    File.open("/var/log/facter.log", "a") {|f| f.write("#{Time.now} facts exist\n")}
    File.readlines("/etc/naily.facts").each do |line|
        if line =~ /^(.+)=(.+)$/
            var = $1.strip; 
            val = $2.strip

            Facter.add(var) do
                setcode { val }
            end
            File.open("/var/log/facter.log", "a") {|f| f.write("#{Time.now} fact '#{var}' = '#{val}'\n")}
        end
    end
else
    File.open("/var/log/facter.log", "a") {|f| f.write("#{Time.now} facts NOT exist\n")}
end
