#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

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
