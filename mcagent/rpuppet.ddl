metadata    :name        => "rpuppet",
            :description => "Run puppet apply from Ruby code as Ruby code",
            :author      => "Mirantis Inc.",
            :license     => "Apache License 2.0",
            :version     => "0.1",
            :url         => "http://mirantis.com",
            :timeout     => 3600

action "run", :description => "Invoke a puppet run" do
	input :data,
		:prompt		=> "data",
		:description	=> "Data encoded in JSON to pass into puppet run",
		:type		=> :string,
		:validation	=> '.*',
		:optional	=> false,
		:maxlength	=> 0

    output :output,
           :description => "Output from puppet agent",
           :display_as => "Output"
end
