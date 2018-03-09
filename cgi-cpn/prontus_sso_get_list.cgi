#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Listar los Prontus con sso activado pertenecientes a un mismo master
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 20/06/2017 - EAG - Primera version
# -------------------------------BEGIN SCRIPT--------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

use strict;
# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use glib_cgi_04;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;

my %FORM;
main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'path_conf'});
    $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    print "Content-type: application/json; charset=utf-8\n\n";
    if ($prontus_varglb::PRONTUS_SSO eq 'SI') {
        my @prontus_list = &lib_prontus::get_prontus_sso_dirs();
        if (scalar(@prontus_list) > 1) {
            my %hash = ('status' => 1, 'msg' => 'Listado generado', 'prontus_list'=> \@prontus_list);
            &glib_html_02::print_json_result_hash(\%hash, 'exit=1,ctype=0');
        } else {
            &glib_html_02::print_json_result(0, "Error al generar listado", 'exit=1,ctype=0');
        }
    } else {
        &glib_html_02::print_json_result(0, "SSO no habilitado", 'exit=1,ctype=0');
    }
};
