metadata        :name           => "Naily Fact Agent",
		:description    => "Key/values in a text file",
		:author         => "Puppet Master Guy",
		:license        => "GPL",
		:version        => "Version 1",
		:url            => "www.naily.com",
		:timeout        => 10

action "get",	:description => "fetches a value from a file" do
	display :failed

	input :key,
		:prompt		=> "Key",
		:description	=> "Key you want from the file",
		:type		=> :string,
		:validation	=> '^[a-zA-Z0-9_]+$',
		:optional	=> false,
		:maxlength	=> 90
	
	output :value,
		:description	=> "Value",
		:display_as	=> "Value" 
end

action "put", :description => "Value to add to file" do
	display :failed

	input :key,
		:prompt		=> "Key",
		:description	=> "Key you want to set in the file",
		:type 		=> :string,
		:validation	=> '^[a-zA-Z0-9_]+$',
		:optional	=> false,
		:maxlength	=> 90

	input :value,
                :prompt         => "Value",
                :description    => "Value you want to set in the file",
                :type           => :string,
                :validation     => '^[a-zA-Z0-9_]+$',
                :optional       => false,
                :maxlength      => 90

	output :msg,
		:description	=> "Status",
		:display_as	=> "Status"
end

action "delete", :description => "Delete a key/value pair if it exists" do
        display :failed

        input :key,
                :prompt         => "Key",
                :description    => "Key you want to change in the file",
                :type           => :string,
                :validation     => '^[a-zA-Z0-9_]+$',
                :optional       => false,
                :maxlength      => 90

        output :msg,
                :description    => "Status",
                :display_as     => "Status"
end
