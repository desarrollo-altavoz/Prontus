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
# Descarga update de prontus y lo instala.
# ---------------------------------------------------------------

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
use Update;
use lib_logproc;
use lib_loading;
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

    # Carga variables de configuracion.
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});
    &lib_prontus::load_config($FORM{'_path_conf'});


    if ($prontus_varglb::ACTUALIZACIONES ne 'SI') {
        &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_automatic_updates'),&lib_language::_msg_prontus('_required_functionality_disabled_product_configuration'),1,'exit=1,ctype=1');
    };


    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A') {
        &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_access_restricted_area'),&lib_language::_msg_prontus('_functionality_available_administrator'),1,'exit=1,ctype=1');
    };


    # Creacion del objeto Update (todas los params son obligatorios).
    my $upd_obj = Update->new(
                    'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                    'version_prontus'   => $prontus_varglb::VERSION_PRONTUS,
                    'path_conf'         => $FORM{'_path_conf'},
                    'document_root'     => $prontus_varglb::DIR_SERVER,
                    'just_status'       => '1')
                    || &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),&lib_language::_msg_prontus('_error_initializing_object_Update').": $Update::ERR", 1, 'exit=1,ctype=1');

    if (!$upd_obj->{last_version_disponible}) {
        &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),&lib_language::_msg_prontus('_avalaible_updates_undetected'),1,'exit=1,ctype=1');
    };

    $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_CPAN/procs/prontus_update_log.html";
    &lib_logproc::log_init(&lib_language::_msg_prontus('_prontus_update'), &lib_language::_msg_prontus('_advancing_process_upgrading_prontus') . $upd_obj->{last_version_disponible});

    my $params = "\"$prontus_varglb::DIR_SERVER\" \"$FORM{'_path_conf'}\"";

    # Para el nuevo sistema de manejo de procesos batch
    my $ret = &lib_loading::init('result_prontus_update.js');
    unless($ret) {
        &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),&lib_language::_msg_prontus('_unable_write_response_file'),1,'exit=1,ctype=1');
    }
    &lib_loading::update_loading('100', '0');

    my $result_page = "..$prontus_varglb::DIR_CPAN/core/prontus_loading_prontus_update.html";

    &lib_prontus::call_system_and_location($prontus_varglb::DIR_SERVER, 'prontus_update_real', $result_page, $params);

    exit;

}; # main.

# ---------------------END SCRIPT-----------------------
