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
# 1.1 - 16/05/2001 - Revision general de detalles de forma.
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

use strict;
# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use lib_prontus;
use prontus_auth;

# ---------------------------------------------------------------
# MAIN.
# -------------

my (%COOKIES, %FORM);

my ($USERS_NOM, $USERS_USR, $USERS_PERFIL, $USERS_ID, $USERS_EMAIL, $USERS_PSW);

main: {

    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta _path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;


    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin
    if ($prontus_varglb::USERS_PERFIL ne 'A') {
        &glib_html_02::print_pag_result('Error','La funcionalidad requerida está disponible sólo para el administrador del sistema.', 1, 'exit=1,ctype=1');
    };


    my $pagina = &glib_fildir_02::read_file($prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . '/prontus_usr_admin.html');
    $pagina = &lib_prontus::set_coreplt_ppal($pagina);

    $pagina =~ /<!--item_loop-->(.*)<!--\/item_loop-->/is;
    my $loop = $1;

    my $lista = &make_lista($loop);
    if ($lista ne '') {
        $pagina =~ s/<!--item_loop-->.*<!--\/item_loop-->/$lista/s;
    } else {
        $pagina =~ s/<!--ul-->.*<!--\/ul-->//s;
    };

    $pagina =~ s/%%_path_conf%%/$FORM{'_path_conf'}/ig;
    $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/ig;
    $pagina =~ s/%%_psw_maxlength%%/$prontus_auth::PWS_MAX_LENGTH/ig;
    $pagina =~ s/%%_psw_minlength%%/$prontus_auth::PWS_MIN_LENGTH/ig;

    print "Cache-Control: no-cache\n";
    print "Cache-Control: max-age=0\n";
    print "Cache-Control: no-store\n";
    print "Content-Type: text/html\n\n";
    print $pagina;


}; # main

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub make_lista {
    # Genera y retorna las filas de la tabla.
    my ($key, $val, %sort_user);
    my ($filas);
    my ($loop) = shift;

    # Almacena en un hash los user para poder ordenar por este criterio el hash principal.
    while ( ($key, $val) = each %prontus_varglb::USERS) {
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $val;
        $sort_user{$key} = $USERS_USR;
    };
    ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = ('', '', '', '', '');

    # Genera el cuerpo de la tabla de usuarios ordenada asc. x user.
    foreach $key (sort {$sort_user{$a} cmp $sort_user{$b}} keys %prontus_varglb::USERS) {
        $val = $prontus_varglb::USERS{$key};
        $USERS_ID = $key;
        ($USERS_NOM, $USERS_USR, $USERS_PSW, $USERS_PERFIL, $USERS_EMAIL) = split /\|/, $val;
        if ($USERS_ID ne '1') {
            $filas .= &generar_fila($loop);
        }
    };
    return $filas;
};
# ---------------------------------------------------------------
sub generar_fila {
    # Genera y retorna cada fila de la tabla
    my $loop_row = shift;

    my ($nom_perfil);

    if ($USERS_PERFIL eq 'P') {
        $nom_perfil = 'Redactor';
    }
    elsif ($USERS_PERFIL eq 'E') {
        $nom_perfil = 'Editor';
    };

    $loop_row =~ s/%%_usr%%/$USERS_USR/g;
    $loop_row =~ s/%%_nom%%/$USERS_NOM/g;
    $loop_row =~ s/%%_email%%/$USERS_EMAIL/g;
    $loop_row =~ s/%%_perfil%%/$nom_perfil/g;
    $loop_row =~ s/%%_id%%/$USERS_ID/g;

    return $loop_row;
};
# ---- END SCRIPT ---
