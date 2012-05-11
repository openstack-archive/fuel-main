require 'json'

module NodeAgent
  def send_ohai()
    url = node["admin"]["URL"]
    Chef::Log.debug("Sending ohai data to REST service at #{url}...")

    data = {"key" => "value"}

    cli = HTTPClient.new
    begin
      cli.post(url, data.to_json)
    rescue Exception => e
      Chef::Log.error("Error in sending ohai data: #{e.message}")
    end
  end
end
