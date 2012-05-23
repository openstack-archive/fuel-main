#!/usr/bin/env perl

while (<>) {

    chomp; next if /^ /;
    if (/^$/ && defined($task)) {
	
	print "$package Task $task\n"; undef $package; undef $task;
    } ($key, $value) = split /: /, $_, 2; if ($key eq 'Package') {
	$package = $value;
    } if ($key eq 'Task') {
	$task = $value;
    }
}
