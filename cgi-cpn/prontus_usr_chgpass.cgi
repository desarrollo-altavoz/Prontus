#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

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
use glib_cgi_04;
use lib_prontus;
use strict;

my (%COOKIES, %FORM);

main: {
  my ($plantilla, $pagina);

  # Rescatar parametros recibidos
  &glib_cgi_04::new();
  $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
  # Ajusta _path_conf para completar path y/o cambiar \ por /
  $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

  $FORM{'USERS_ID'} = &glib_cgi_04::param('USERS_ID');

  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
  $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL eq 'A') {
        &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),&lib_language::_msg_prontus('_functionality_available_editor_writer'), 1, 'exit=1,ctype=1');
    };
    
    if (&lib_prontus::open_dbm_files() ne 'ok') {
        print "Content-Type: text/html\n\n";
        &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),&lib_language::_msg_prontus('_unable_open_dbm_file'));
        exit;
    };
  
    
    $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . '/prontus_usr_chgpass.html';
    
    $pagina = &glib_html_02::rellenar_plantilla(
        3,
        '%%_PRONTUS_ID%%', $prontus_varglb::PRONTUS_ID, '', '',
        '%%_dir_cgi_cpn%%', $prontus_varglb::DIR_CGI_CPAN, '', '',
        '%%_path_conf%%', $FORM{'_path_conf'},'','',
        $plantilla
    );
             
    # Mostrar pagina al browser.
    print "Cache-Control: no-cache\n";
    print "Cache-Control: max-age=0\n";
    print "Cache-Control: no-store\n";
    print "Content-Type: text/html\n\n";
    print $pagina;
  
};

