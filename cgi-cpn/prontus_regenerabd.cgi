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

use strict;




# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM);

main: {

    &glib_cgi_04::new(); # Rescata parametros del formulario.

    $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

    &lib_prontus::load_config($FORM{'path_conf'});

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A') {
        &glib_html_02::print_pag_result('&lib_language::_msg_prontus('_access_restricted_area')',&lib_language::_msg_prontus('_functionality_available_administrator'), 1, 'exit=1,ctype=1');
    };

    $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_CPAN/procs/prontus_art_regenbd_log.html";
    &lib_logproc::log_init(&lib_language::_msg_prontus('_regenerate_log_artic_table'), &lib_language::_msg_prontus('_page_shows_regen_progress_artic_table_db'));

    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_bd_regen.js";
    my $msg = '{"status":0, "msg": "'.&lib_language::_msg_prontus('_inproces_in_process').'"}';
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
    my $result_page = "..$prontus_varglb::DIR_CPAN/core/prontus_loading_bd_regen.html";

    my $params = "\"$FORM{'path_conf'}\"";
    &lib_prontus::call_system_and_location($prontus_varglb::DIR_SERVER,
                                            'prontus_regenerabd_real',
                                            $result_page,
                                            $params);

    exit;

}; # main.
