use Parse::DebControl;

$parser = new Parse::DebControl;

 open(my $fh, '<:encoding(UTF-8)', $ARGV[0])
  or die "Could not open file '$ARGV[0]' $!";

 $control_data = "";
 while (my $line = <$fh>) {
     if ($line =~ /^#/) { next; }
     $control_data = $control_data . $line;
 }

 $data = $parser->parse_mem($control_data);
 foreach my $a (@$data) {
     next if exists $a->{"Source"};
     print ${a}->{"Package"}."\n";
 }
