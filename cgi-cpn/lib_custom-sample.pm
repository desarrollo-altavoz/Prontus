#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

package lib_custom;

use strict;

#---------------------------------------------------------------#
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub fechapEngLong {
  # aaaamm  -> Mon, 24 Apr 2006
  use Time::Local qw(timelocal_nocheck);
  my $aaaammdd = $_[0]; # fechap
  return '' if ($aaaammdd =~ /^9999/);
  return '' if ($aaaammdd !~ /^\d{8}$/);

   my (@dias) = ('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday');
   my (@meses) = ('January','February','March','April','May','June','July',
                    'August','September','October','November','December');
   $aaaammdd =~ /(\d\d\d\d)(\d\d)(\d\d)/;
   my ($dia,$mes,$ano) = ($3,$2,$1);

   my ($tiempo) = &Time::Local::timelocal_nocheck(0,0,12,$dia,($mes - 1),($ano - 1900)) || return '';

   my($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($tiempo);
   $dia = $dia + 0; # Para extraer los ceros de adelante.

   return $dias[$wday] . ", " . $meses[($mes - 1)] . ' ' . $dia  . " $ano";
};

# ---------------------------------------------------------------
return 1;
# -------------------------------END LIBRERIA--------------------
