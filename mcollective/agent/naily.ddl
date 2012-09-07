metadata \
:name        => "Naily Agent",
:description => "Naily Agent",
:author      => "Mirantis Inc.",
:license     => "Apache License 2.0",
:version     => "0.0.1",
:url         => "http://mirantis.com",
:timeout     => 300

action "runonce", :description => "Runs puppet apply" do
  output \
  :output,
  :description => "Response message",
  :display_as => "Response message"
end

action "echo", :description => "Echo request message" do
  output \
  :output,
  :description => "Just echo request message",
  :display_as => "Echo message"
end

