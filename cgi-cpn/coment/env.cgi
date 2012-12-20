#!/usr/bin/perl

print "Content-Type: text/html\n\n";

foreach $key (keys(%ENV)) {
  print "<br> $key = $ENV{$key} <br>\n";
};

