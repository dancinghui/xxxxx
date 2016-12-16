#!/usr/bin/env perl
use warnings;
use strict;
#use URI::Escape;
use JSON::PP;
use Encode;

sub readall
{
	my $fd = shift;
	my $all = '';
	while (<$fd>)
	{
		s/^\s+|\s+$//sg;
		$all .= $_;
	}
	return $all;
}

my $tbl = {};

my $ins = &readall(*STDIN);
foreach (split(/&/, $ins))
{
	my ($k, $v) = split(/=/, $_, 2);
	$v=~s/\+/ /g;
	$v=~s/%([0-9a-f]{2})/chr(hex($1))/ieg;
	$tbl->{$k} = decode('utf-8', $v);
}

print "\n\n";
print JSON::PP->new->utf8(1)->pretty(1)->encode($tbl) . "\n";
