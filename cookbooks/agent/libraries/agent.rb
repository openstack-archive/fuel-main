require 'json'

module NodeAgent
  def send_ohai()
    url = "#{node['admin']['URL']}/api/environments/1/nodes/#{node['fqdn']}"
    Chef::Log.debug("Sending ohai data to REST service at #{url}...")

    interfaces = node["network"]["interfaces"].inject([]) do |result, elm|
      result << { :name => elm[0], :addresses => elm[1]["addresses"] }
    end

    data = { :fqdn => node["fqdn"],
             :block_device => node["block_device"].to_hash,
             :interfaces => interfaces,
             :cpu => node["cpu"].to_hash,
             :memory => node["memory"].to_hash
           }

    cli = HTTPClient.new
    begin
      cli.put(url, data.to_json)
    rescue Exception => e
      Chef::Log.error("Error in sending ohai data: #{e.message}")
    end
  end
end
