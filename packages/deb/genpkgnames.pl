use Parse::DebControl;

$parser = new Parse::DebControl;

%options = (
    type => 'debian/control',
    stripComments => 'true',
    );

 $data = $parser->parse_file($ARGV[0], \%options);
 foreach my $a (@$data) {
     next if exists $a->{"Source"};
     print ${a}->{"Package"}."\n";
 }
