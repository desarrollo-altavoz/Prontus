#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

print "Content-Type: text/html\n\n";

foreach $key (keys(%ENV)) {
  print "<br> $key = $ENV{$key} <br>\n";
};

