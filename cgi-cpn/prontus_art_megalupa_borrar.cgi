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
# PROPOSITO.
# -----------
# Carga el listado de Mis Busquedas con Ajax
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# plantilla prontus_art_newadmin.html

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
#

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
use lib_search;

use glib_cgi_04;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%FORM);
main: {
    # Recibe parametros.
    &glib_cgi_04::new();

    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');

    # Deduce path conf del referer, en caso de no ser suministrado.
    $FORM{'_path_conf'} = &get_path_conf() if ($FORM{'_path_conf'} eq '');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Se lee el ID de la busqueda a borrar
    $FORM{'_id_busqueda'} = &glib_cgi_04::param('_id_busqueda');

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);
    if ($prontus_varglb::USERS_ID eq '') {
        my $resp;
        $resp->{'error'} = '1';
        $resp->{'msg'} = "Ud no tiene una sesi&oacute;n iniciada";
        &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=1');
    };

    my $file = &lib_search::get_file_mis_busquedas($prontus_varglb::USERS_ID, $FORM{'_id_busqueda'});
    print STDERR "file[$file]\n";
    if(-f $file) {
        #~ Se elimina la busqueda
        unlink($file);
        if(-f $file) {
            my $resp;
            $resp->{'error'} = '1';
            $resp->{'msg'} = "No se pudo eliminar la b&uacute;squeda.";
            &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=1');
        };
    };

    #~ Todo salió ok, la busqueda fue eliminada
    my $resp;
    $resp->{'error'} = '0';
    $resp->{'msg'} = "B&uacute;squeda eliminada exitosamente.";
    #~ Mensaje para cuando no quedan busquedas
    my $msgextra = $lib_search::MIS_BUSQUEDAS_MSG;
    utf8::encode($msgextra);
    $resp->{'extra'} = $msgextra;

    &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=1');

}; # main


# -------------------------------END SCRIPT----------------------
