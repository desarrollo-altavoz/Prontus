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
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);

    # Incluir path de coment/
    use FindBin '$Bin';
    $nuevopath = $Bin . "/coment";
    unshift(@INC, $nuevopath);
};

use glib_cgi_04;
use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;

use lib_search;

use coment_varglb;
use lib_coment;

use strict;

my %FORM;

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');

    # Deduce path conf del referer, en caso de no ser suministrado.
    $FORM{'path_conf'} = &get_path_conf() if ($FORM{'path_conf'} eq '');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'path_conf'});
    $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    print "Content-Type: text/html\n\n";
    
    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        print "0";
    } else {
        print "1";
    };

    exit;
};
