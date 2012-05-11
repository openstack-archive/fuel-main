require 'httpclient'
require 'json'

module NodeAgent
  def send_ohai()
    url = node["admin"]["URL"]
    Chef::Log.debug("Sending ohai data to REST service at #{url}...")

    data = {"key" => "value"}

    cli = HTTPClient.new
    cli.post(url, data.to_json)
  end
end
