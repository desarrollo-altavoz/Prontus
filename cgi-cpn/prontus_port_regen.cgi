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
# Gatilla el script que reparsea los portadas de este prontus.

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
#
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};
use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use lib_logproc;

#~ use glib_html_02;
#~ use glib_fildir_02;
use glib_cgi_04;

use strict;


# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%FORM);

main: {

    &glib_cgi_04::new(); # Rescata parametros del formulario.

    $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');

    $FORM{'check_pp'} = &glib_cgi_04::param('check_pp');
    $FORM{'operador'} = &glib_cgi_04::param('operador');
    $FORM{'cmb_edic'} = &glib_cgi_04::param('cmb_edic');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

    &lib_prontus::load_config($FORM{'path_conf'});

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A') {
        &glib_html_02::print_pag_result('Acceso a Area Restringida',
                'La funcionalidad requerida est� disponible s�lo para el administrador del sistema', 1, 'exit=1,ctype=1');
    };

    $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_CPAN/procs/prontus_port_regen_log.html";
    &lib_logproc::log_init('Log de Actualizaci�n Masiva de Portadas', 'Esta p�gina muestra el avance del proceso de actualizar las portadas');

    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_port_regen.js";
    my $msg = '{"status":0, "msg": "En proceso"}';
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
    my $result_page = "..$prontus_varglb::DIR_CPAN/core/prontus_loading_port_regen.html";

    my $params = "\"$FORM{'path_conf'}\"";

    # Agregar parametros adicionales.
    if($FORM{'cmb_edic'} eq '') {
        $FORM{'operador'} = '';

    } else {
        if($FORM{'operador'} eq '') {
            $FORM{'operador'} = 'igual';
        };
    };
    if($FORM{'check_pp'} ne 'si') {
        $FORM{'check_pp'} = '';
    };

    $params .= " \"$FORM{'check_pp'}\" \"$FORM{'operador'}\" \"$FORM{'cmb_edic'}\"";

    &lib_prontus::call_system_and_location($prontus_varglb::DIR_SERVER,
                                           'prontus_port_regen_real',
                                           $result_page,
                                           $params);
};



# ---------------------END SCRIPT-----------------------
