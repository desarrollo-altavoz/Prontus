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
# Dispara importacion de Taxonomia Prontus.
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt

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
use lib_prontus;
use lib_logproc;

use glib_html_02;
use glib_fildir_02;
use glib_cgi_04;
use File::Copy;
use strict;

# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM);

main: {

  &glib_cgi_04::new(); # Rescata parametros del formulario.

  $FORM{'path_conf'} = &glib_cgi_04::param('path_conf');
  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

  &lib_prontus::load_config($FORM{'path_conf'});

    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # user no valido
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin o editor
    if ($prontus_varglb::USERS_PERFIL eq 'P') {
      &glib_html_02::print_pag_result('Acceso a Area Restringida','La funcionalidad requerida no est� disponible para perfil Redactor',1,'exit=1,ctype=1');
    };

  $FORM{'Sbm_ACCION'} = &glib_cgi_04::param('Sbm_ACCION');
  $FORM{'FILE1'} = &glib_cgi_04::param('FILE1');


  if ($FORM{'Sbm_ACCION'} =~ /^Importar/i) {

    if ($FORM{'FILE1'} eq '') {
      print "Content-Type: text/html\n\n";
      &glib_html_02::print_pag_result("ERROR","Debe especificar archivo a subir.");
      exit;
    };

    &File::Copy::copy($FORM{'FILE1'}, "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/tax_import.xml");

    if ((! -f "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/tax_import.xml") or (! -s "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/tax_import.xml")) {
      print "Content-Type: text/html\n\n";
      &glib_html_02::print_pag_result("ERROR","No fue posible subir el archivo especificado al servidor.");
      exit;
    };

    $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_CPAN/procs/prontus_tax_import_log.html";
    &lib_logproc::log_init('Log de Importaci�n', 'Esta p�gina muestra el avance del proceso de Importaci�n de Secciones, Temas y Subtemas Prontus');

    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_tax_import.js";
    my $msg = '{"status":0, "msg": "En proceso"}';
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
    my $result_page = "..$prontus_varglb::DIR_CPAN/core/prontus_loading_tax_import.html";

    my $params = "\"$prontus_varglb::DIR_SERVER\" \"$FORM{'path_conf'}\"";
    &lib_prontus::call_system_and_location($prontus_varglb::DIR_SERVER, 'prontus_tax_import_real', $result_page, $params);

  }
  else {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("ERROR","Solicitud de ejecuci�n no v�lida.");

  };
}
