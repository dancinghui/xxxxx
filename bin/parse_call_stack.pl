#!/usr/bin/env perl
use warnings;
use strict;

sub unq
{
        my $q = shift;
        return '"' if ($q eq 'quot');
        return "\'" if ($q eq '#39');
        return '<' if ($q eq 'lt');
        return '>' if ($q eq 'gt');
        return 'amp' if ($q eq '&');
        return "&$q;";
}

sub check
{
        my $fd;
        my ($fn, $cmd) = @_;
        open($fd, $fn) || return '';
        my @st = stat($fn);
        my $sz = $st[7];
        my $xx;
        sysread($fd, $xx, $sz);
        close($fd);
        $xx=~s/<[^<>]*>//g;
        $xx=~s/&(.{1,6});/unq($1)/eg;

        if ($cmd eq 'p')
        {
                print $xx."\n";
                return;
        }

        my @vvv = split(/# ThreadID:/, $xx);
        foreach (@vvv)
        {
                my $a = $_;
                s/.*File://sg;
                s/,.*$//sg;
                next if not $_;
                if ($cmd ne '')
                {
                        print "$a\n" if (m/$cmd/);
                }
                else
                {
                        print "$_\n";
                }
        }
}

&check("res.trace.html", $ARGV[0]||'');
