#!/usr/bin/perl
# Hace eco de las variables de ambiente en modo text/plain
#
# Desarrollo:
# 1.0.0 - Primera versión.

print "Content-Type: text/html\n\n";


print '<br> <b>$0</b> = ' . $0 . " <br><hr>\n";
use FindBin '$Bin';
print "<br> <b>The script is located in $Bin<br><hr>\n";

  foreach $key (keys(%ENV)) {
             print "<br> <b>$key</b> = $ENV{$key} <br><hr>\n";
         };



