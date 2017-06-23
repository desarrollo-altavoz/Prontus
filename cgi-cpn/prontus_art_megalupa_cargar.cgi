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

    &lib_prontus::test_servers($ENV{'HTTP_REFERER'}) if ($prontus_varglb::IP_SERVER);

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    my $buffer = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/prontus_art_newadmin.html");
    $buffer = &lib_prontus::set_coreplt_ppal($buffer);

    my $newbuffer;
    if($buffer =~ /<!--content_mis_busquedas-->(.*?)<!--\/content_mis_busquedas-->/is) {
      $newbuffer = $1;

      $newbuffer = &lib_search::parsea_mis_busquedas($newbuffer, $prontus_varglb::USERS_ID);

    } else {
      $newbuffer = 'Error al cargar la plantilla';
    };

    print "Cache-Control: no-cache\n";
    print "Cache-Control: max-age=0\n";
    print "Cache-Control: no-store\n";

    print "Content-type: text/html\n\n";
    print $newbuffer;
}; # main

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
# ---------------------------------------------------------------
# -------------------------------END SCRIPT----------------------
