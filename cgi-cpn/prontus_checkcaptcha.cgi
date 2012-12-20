#!/usr/bin/perl

# Chequea captcha

use lib_captcha;
use strict;

my $str = 'm2x4'; # string ingresado por el user
print "Content-Type: text/html\n\n";
if (&lib_captcha::valida_captcha($str, 'captcha_posting')) {
  print "OK";
}
else {
  print "FAIL [$lib_captcha::ERRCODE]"; # code 0 es fail normal
};


#-------------------------------------------------------------------------#