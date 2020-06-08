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
# Gatilla el script que reparsea los articulos de este prontus.

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
#

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
}

use strict;
use lib_prontus;
# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_logproc;

use glib_html_02;
use glib_fildir_02;
use glib_cgi_04;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%FORM);

&main();
exit;

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub main {

    &glib_cgi_04::new(); # Rescata parametros del formulario.

    $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');

    $FORM{'fids'} = &glib_cgi_04::param('fids');
    $FORM{'mvs'} = &glib_cgi_04::param('mvs');
    $FORM{'fecha'} = &glib_cgi_04::param('fecha');
    $FORM{'op'} = &glib_cgi_04::param('op');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

    &lib_prontus::load_config($FORM{'path_conf'});

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A') {
        &glib_html_02::print_pag_result('Acceso a Area Restringida',
                                        'La funcionalidad requerida está disponible sólo para el '
                                        . 'administrador del sistema', 1, 'exit=1,ctype=1');
    };

    $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_CPAN/procs/prontus_art_regen_log.html";
    &lib_logproc::log_init('Log de Actualización Masiva de Artículos', 'Esta página muestra el avance del proceso de actualizar los artículos');

    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_art_regen.js";
    my $msg = '{"status":0, "msg": "En proceso"}';
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
    my $result_page = "..$prontus_varglb::DIR_CPAN/core/prontus_loading_art_regen.html";

    my $params = "\"$FORM{'path_conf'}\"";

    # Agregar parametros adicionales.
    if ($FORM{'fecha'} ne '@all') {
        my $op = '';

        if ($FORM{'op'} eq "menor" ){
            $op = '<';
        } elsif ($FORM{'op'} eq "mayor") {
            $op = '>';
        } elsif ($FORM{'op'} eq "fecha") {
            $op = '=';
        } elsif ($FORM{'op'} eq "rango") {
            $op = '~';
        }

        $FORM{'fecha'} = $op . $FORM{'fecha'};
    }

    $FORM{'_seccion1'} = &glib_cgi_04::param('_seccion1');
    $FORM{'_tema1'} = &glib_cgi_04::param('_tema1');
    $FORM{'_subtema1'} = &glib_cgi_04::param('_subtema1');

    $FORM{'_seccion1'} = 0 if ($FORM{'_seccion1'} !~ /^\d+$/);
    $FORM{'_tema1'} = 0 if ($FORM{'_tema1'} !~ /^\d+$/);
    $FORM{'_subtema1'} = 0 if ($FORM{'_subtema1'} !~ /^\d+$/);

    ($FORM{'_tema1'}, $FORM{'_subtema1'}) = (0, 0) if (!$FORM{'_seccion1'});

    $params .= " \"$FORM{'fecha'}\" \"$FORM{'fids'}\" \"$FORM{'mvs'}\" \"$FORM{'_seccion1'}_$FORM{'_tema1'}_$FORM{'_subtema1'}\"";

    &lib_prontus::call_system_and_location($prontus_varglb::DIR_SERVER, 'prontus_art_regen_real', $result_page, $params, 0);
}
