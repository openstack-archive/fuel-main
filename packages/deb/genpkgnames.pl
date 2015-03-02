use Parse::DebControl;

$parser = new Parse::DebControl;
 $data = $parser->parse_file($ARGV[0]);
 foreach my $a (@$data) {
     next if exists $a->{"Source"};
     print ${a}->{"Package"}."\n";
 }
