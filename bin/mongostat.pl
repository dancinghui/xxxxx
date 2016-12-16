#!/usr/bin/env perl
use strict;
use warnings;

sub get_cmdline
{
	my $pid= shift;
	my $fd;
	open($fd, "/proc/$pid/cmdline") || return "";
	return "$pid" if (!$fd);
	my $cmdline='';
	sysread($fd, $cmdline, 9999);
	close($fd);
	$cmdline=~s/\0/ /sg;
	return $cmdline;
}

sub main
{
	my @all = `netstat -anp 2>/dev/null`;
	my $stat = {};
	foreach (@all)
	{
		chomp;
		my @line = split(/\s+/, $_, 7);
		if (@line == 7 && $line[4]=~/:27017/ &&
			$line[5] eq 'ESTABLISHED')
		{
			$stat->{$line[6]} += 1;
		}
	}
	my @st2;
	foreach (sort keys(%$stat))
	{
		my $name = $_;
		my $cnt = $stat->{$_};
		$name=~s/\s+$//s;
		if ($name=~/^(\d+)/)
		{
			my $pid = int($1);
			my $cmdline = get_cmdline($pid) || $name;
			my $s = sprintf "[%3d] %5d %s\n", $cnt, $pid, $cmdline;
			push @st2, [$cnt, $s];
		}
		else
		{
			my $s = sprintf "[%3d] $name\n", $cnt;
			push @st2, [$cnt, $s];
		}
	}
	foreach (sort {$b->[0] <=> $a->[0]} @st2)
	{
		print $_->[1];
	}
}

&main;
