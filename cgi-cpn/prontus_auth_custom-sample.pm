#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

package prontus_auth_custom;
use strict;

$prontus_auth::PWS_MAX_LENGTH = 32; # largo máximo de psw en caracteres
$prontus_auth::PWS_MIN_LENGTH = 6;  # largo mínimo de psw en caracteres
$prontus_auth::PWS_TO_REMEMBER = 3; # passwords antiguas a recordar
$prontus_auth::PWS_COMPARE_PREVIOUS = 1; # prevenir la reutilización de claves

return 1;
