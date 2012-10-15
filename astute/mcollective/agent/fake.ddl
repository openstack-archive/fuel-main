metadata    :name        => "Fake Agent",
            :description => "Fake Agent",
            :author      => "Mirantis Inc.",
            :license     => "Apache License 2.0",
            :version     => "0.0.1",
            :url         => "http://mirantis.com",
            :timeout     => 20

action "echo", :description => "Echo request message" do
    output :output,
           :description => "Just request message",
           :display_as => "Echo message"
end

