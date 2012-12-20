#!/usr/bin/perl
#
#-------------------------------COMENTARIO GLOBAL---------------
#---------------------------------------------------------------
# PROPOSITO.
#-----------
# Funciones de interconexion con PHP::Session

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 1.0 - ycc - 12/2006 - Primera version.
#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package lib_phpsession;
use lib_cookies;
use PHP::Session;
use strict;
use glib_cgi_04;

#----------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
sub get_php_session_var {
  my ($session_var, $session_name, $session_path) = @_;

  # Se Valida que el usuario tenga sessión
  my %cookies = &lib_cookies::get_cookies();

  my $session;
  if ($cookies{$session_name}) {
    return '' if (! -s "$session_path/sess_" . $cookies{$session_name});
    $session = PHP::Session->new($cookies{$session_name}, { save_path => $session_path}) || return '';
    if(!$session->is_registered($session_var)) {
      return '';
    };
  }
  else {
    return '';
  };

  return $session->get($session_var);

};
# ---------------------------------------------------------------
return 1;

# -------------------------------END LIBRERIA--------------------