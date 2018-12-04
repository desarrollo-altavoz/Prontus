#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# SCRIPT.
# -----------
#

# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/.

# ---------------------------------------------------------------
# PROPOSITO.
# -----------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------

# ---------------------------------------------------------------
# INVOCACIONES REALIZADAS.
# ------------------------

# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------

# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------

# ---------------------------------------------------------------
# Tablas.
# ------------------------
# No utiliza.

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 01 - 23/01/2003 - YCH - Primera Version.
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# 13/08/2007 - ych - problemas con la ruta del cfg (detectado por pedraza)

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();

use glib_html_02;
use glib_fildir_02;
use lib_prontus;

use glib_cgi_04;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my (%FORM);

main: {
  # Rescatar parametros recibidos
  &glib_cgi_04::new();

  $FORM{'Cmb_TPORT'} = &glib_cgi_04::param('Cmb_TPORT');
  $FORM{'port'} = &glib_cgi_04::param('port');

  $FORM{'path_conf'} = &glib_cgi_04::param('path_conf');
  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'path_conf'});
  $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  # Control de usuarios obligatorio chequeando la cookie contra el dbm.
  ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

  if (&lib_prontus::open_dbm_files() ne 'ok') {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),&lib_language::_msg_prontus('_unable_open_dbm_file'));
    exit;
  };

	my $origen = $prontus_varglb::DIR_SERVER .
                     $prontus_varglb::DIR_TEMP .
                     $prontus_varglb::DIR_EDIC .
                     $prontus_varglb::DIR_NROEDIC .
                     $prontus_varglb::DIR_SPARE .
                     "/$FORM{'Cmb_TPORT'}";

	my $destino =  $prontus_varglb::DIR_SERVER .
                   $prontus_varglb::DIR_TEMP .
                   $prontus_varglb::DIR_EDIC .
                   $prontus_varglb::DIR_NROEDIC .
                   $prontus_varglb::DIR_SECC .
                   "/$FORM{'port'}";

  if (!(-f $origen)) {
    print "Content-type: text/html\n\n";
    print &lib_language::_msg_prontus('_error_invalid_source_template').":[$origen]";
    exit;
  };


  if (!(-f $destino)) {
    print "Content-type: text/html\n\n";
    print &lib_language::_msg_prontus('_error_invalid_target_template').":[$destino]";
    exit;
  };

  # Copia template origen a destino
  my $portada = &glib_fildir_02::read_file($origen);

  &glib_fildir_02::write_file($destino, $portada);

  print "Location: ..$prontus_varglb::DIR_CORE/prontus_copy_spare_confirm.html\n\n";
};

# ----------------------------END-SCRIPT-----------------------------------
