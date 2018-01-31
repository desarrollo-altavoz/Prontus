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
# Chequear / conectar un usuario al sistema.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# 2) Desde la pag. de ingreso al Sistema, via boton 'Ingresar'.
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# No registra.
# ---------------------------------------------------------------

# 1.1 - 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.2 - 16/05/2001 - Revision general de detalles de forma.
# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0

# Prontus 8.0 - 01/08/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
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
use Session;
use glib_fildir_02; # Prontus 6.0

use strict;
use File::Copy;
use lib_multiediting;
use utf8;
# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM, $TIPO_PRONTUS, $AREA_MENU, $AREA_CONT, $PRONTUS_KEY);
my ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_ID, $USERS_EMAIL);

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga var. globales con los datos del arch. conf.
    &lib_prontus::load_config(&lib_prontus::ajusta_pathconf($FORM{'_path_conf'}));   # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    $FORM{'_tipo_recurso'} = &glib_cgi_04::param('_tipo_recurso'); # port | art
    if ($FORM{'_tipo_recurso'} !~ /^(art|port)$/) {
        &glib_html_02::print_json_result(0, 'Tipo de recurso no es válido', 'exit=1,ctype=1');
    };

    $FORM{'_nom_recurso'} = &glib_cgi_04::param('_nom_recurso');
    $FORM{'_nom_recurso'} =~ s/\.\w+$//; # borra ext en caso de venir
    if ($FORM{'_nom_recurso'} !~ /^[\w\-]+$/) {
        &glib_html_02::print_json_result(0, 'Nombre de recurso no es válido', 'exit=1,ctype=1');
    };


    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    my $sess_obj = Session->new(
                    'prontus_id'        => $prontus_varglb::PRONTUS_SSO_MANAGER_ID,
                    'document_root'     => $prontus_varglb::DIR_SERVER)
                    || die("Error inicializando objeto Session: $Session::ERR\n");

    # envia ping
    &lib_multiediting::send_ping($prontus_varglb::DIR_SERVER,
                                 $prontus_varglb::PRONTUS_ID,
                                 $FORM{'_nom_recurso'},
                                 $FORM{'_tipo_recurso'},
                                 $prontus_varglb::USERS_USR,
                                 $sess_obj->{id_session});

    # ve si hay alguien mas editando el recurso
    my $concurrency = &lib_multiediting::get_concurrency( $prontus_varglb::DIR_SERVER,
                                                          $prontus_varglb::PRONTUS_ID,
                                                          $FORM{'_nom_recurso'},
                                                          $FORM{'_tipo_recurso'},
                                                          $prontus_varglb::USERS_USR,
                                                          $sess_obj->{id_session});

    my $lock_recurso = 0;

    if ($prontus_varglb::BLOQUEO_EDICION ne '0') {
        $lock_recurso = &lib_multiediting::lock_recurso($prontus_varglb::DIR_SERVER,
                                                              $prontus_varglb::PRONTUS_ID,
                                                              $FORM{'_nom_recurso'},
                                                              $FORM{'_tipo_recurso'},
                                                              $prontus_varglb::USERS_USR,
                                                              $sess_obj->{id_session}, $prontus_varglb::BLOQUEO_EDICION);
    };
    #~ print STDERR "lock_recurso[$lock_recurso], usuario[$prontus_varglb::USERS_USR], id_session[$sess_obj->{id_session}]\n";

    my $resp;
    $resp->{'status'} = 1;
    $resp->{'msg'} = $concurrency;
    $resp->{'lock'} = $lock_recurso;
    &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=1');
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
# -------------------------------END SCRIPT----------------------
