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
# PROPOSITO .
# -----------

# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
#
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
#
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.1 - 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.2 - 16/05/2001 - Revision general de detalles de forma.
# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0
# Revision Prontus 8.0 - ych - 23/05/2002
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# ---------------------------------------------------------------


# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

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



# ---------------------------------------------------------------
# MAIN.
# -------------

my (%COOKIES, %FORM);
my ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL);

main: {
    my ($lnk, $campo, @campos, $cod, $key);




    # print "Content-Type: text/html\n\n"; # debug
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    @campos = &glib_cgi_04::param();


    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;


    # user check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A') {
        &glib_html_02::print_json_result(0, 'La funcionalidad requerida está disponible sólo para el administrador del sistema', 'exit=1,ctype=1');
    };



    # Abrir dbm files
    if (&lib_prontus::open_dbm_files() ne 'ok') {
        &glib_html_02::print_json_result(0, 'No fue posible abrir archivos de usuario', 'exit=1,ctype=1');
    };


    $FORM{'_id'}= &glib_cgi_04::param('_id');
    if (($FORM{'_id'} !~ /^[0-9]+$/) || (!$FORM{'_id'})) {
        &glib_html_02::print_json_result(0, 'Id no válido', 'exit=1,ctype=1');
    };

    delete $prontus_varglb::USERS{$FORM{'_id'}};

    foreach $key  (keys %prontus_varglb::ARTUSERS) {
        my ($idtipo, $idusr) = split /\|/, $key;
        if ($idusr eq $FORM{'_id'}) {
            delete $prontus_varglb::ARTUSERS{$key};
        };
    };

    foreach $key  (keys %prontus_varglb::PORTUSERS) {
        my ($port, $idusr) = split /\|/, $key;
        if ($idusr eq $FORM{'_id'}) {
            delete $prontus_varglb::PORTUSERS{$key};
        };
    };

    &lib_prontus::close_dbm_files();

    &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');


};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

# ------------------------------END SCRIPT----------------------

