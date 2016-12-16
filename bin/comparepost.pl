#!/usr/bin/env perl
use warnings;
use strict;
use JSON::PP;
use Term::ReadLine;

our $g_newonly = '';

sub check_url
{
	my ($sa, $sb) = @_;
	my @allkeys = sub {
		my $o = {};
		foreach (@_)
		{
			foreach (keys(%$_))
			{
				$o->{$_} = 1;
			}
		}
		return sort(keys(%$o));
	}->(@_);
	foreach (@allkeys)
	{
		my $va = $sa->{$_};
		my $vb = $sb->{$_};
		$va='<non_exists>' if not defined($va);
		$vb='<non_exists>' if not defined($vb);
		if ($va ne $vb)
		{
			print "$_=$va\n" if (not $g_newonly);
			print "$_=$vb\n";
		}
	}
	print "\n";
}

sub get_url
{
	my ($to_arr, $multiline, $prompt) = @_;
	my $term = Term::ReadLine->new("compare $prompt");
	my $attr = $term->Attribs;
	$attr->ornaments(0);
	$attr->{completion_entry_function} = $attr->{list_completion_function};
	$attr->{completion_word} = [qw(__readclip__ __quit__ __newonly__)];
	$term->addhistory('__readclip__');

	my $OUT = $term->OUT || \*STDOUT;
	my $r = '';
	for (;;)
	{
		my $v = $term->readline($prompt);
		last if (not defined($v));
		$v=~s/^\s+|\s+$//sg;
		return undef if ($v eq '__quit__');

		if ($v eq '')
		{
			next;
		}
		elsif ($v eq '__readclip__')
		{
			$r = `pbpaste`;
			$r=~s/^\s+|\s+$//sg;
		}
		elsif ($v eq '__newonly__')
		{
			$g_newonly = ! $g_newonly;
			next;
		}
		elsif ($v eq '__quit__')
		{
			return undef;
		}
		elsif ($multiline)
		{
			my $emptylines = 0;
			$r .= $v;
			for (;$emptylines < 2;)
			{
				$v = $term->readline('... ');
				last if not defined($v);
				$v=~s/^\s+|\s+$//sg;
				if ($v ne '')
				{
					$r .= $v;
					$emptylines=0;
				}
				else
				{
					$emptylines ++;
				}
			}
		}
		else
		{
			$r = $v;
		}
		$term->addhistory($r) if ($r=~/\S/);
		return $to_arr->($r);
	}
}

sub post2arr
{
	my $o = {};
	my $x = shift;
	$x=~s/^\s+|\s+$//sg;
	my @lines = split(/\s*&\s*/, $x);
	foreach my $l (@lines)
	{
		my ($k, $v) = split(/=/, $l, 2);
		if (defined($v))
		{
			$v=~s/\+/ /g;
			$v=~s/%([0-9a-f]{2})/chr(hex($1))/ieg;
			$k=~s/%([0-9a-f]{2})/chr(hex($1))/ieg;
			$o->{$k} = $v if $k ne '__VIEWSTATE';
		}
	}
	return $o;
}

sub url2arr
{
	my $u = shift;
	$u=~s/\#.*$//;
	my @a = split(/\?/, $u, 2);
	my $o = post2arr($a[1] or '');
	$o->{__baseurl__} = $a[0];
	return $o;
}

sub cookie2arr
{
	my $o = {};
	my $x = shift;
	$x=~s/^\s+|\s+$//sg;
	my @lines = split(/\s*;\s*/, $x);
	foreach my $l (@lines)
	{
		my ($k, $v) = split(/=/, $l, 2);
		if (defined($v))
		{
			$o->{$k} = $v;
		}
	}
	return $o;
}

sub main
{
	my $exename = $0;
	$exename=~s!^.*[\\/]!!;
	$exename=~s!\..*$!!;

	my $toarr;
	my $multiline = 1;
	my $prompt = '';
	if ($exename eq 'comparecookie')
	{
		$toarr = \&cookie2arr;
		$prompt = 'cookie: ';
	}
	elsif ($exename eq 'comparepost')
	{
		$toarr = \&post2arr;
		$prompt = 'post: ';
	}
	elsif ($exename eq 'compareurl')
	{
		$toarr = \&url2arr;
		$multiline = '';
		$prompt = 'url: ';
	}
	else
	{
		print STDERR "unknown program!\n";
		return 1;
	}

	my $urla = &get_url($toarr, $multiline, $prompt);
	if ($#ARGV>=0)
	{
		if ($ARGV[0] eq 'parse')
		{
			foreach (sort keys(%$urla))
			{
				print "$_ => $urla->{$_}\n";
			}
			return 0;
		}
		elsif ($ARGV[0] eq 'newonly')
		{
			$g_newonly = 1;
		}
	}
	for (;defined($urla);)
	{
		my $urlb = &get_url($toarr, $multiline, $prompt);
		last if (not defined($urlb));
		check_url($urla, $urlb);
		$urla = $urlb;
	}
}

&main;
