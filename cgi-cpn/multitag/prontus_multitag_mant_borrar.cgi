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
# Borrar una categoria y su url asociada, si esta en uso no se borra
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# NO
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# solo web
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# Ninguna
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# MULTITAG_ART_S
# MULTITAG_ART_ST
# MULTITAG_ART_T
# MULTITAG_S
# MULTITAG_ST
# MULTITAG_T
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 26/11/2015 - JOR - Primera version.
# 1.1.0 - 23/02/2017 - EAG - Integracion a Prontus
#
# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/[^\/]+$//;
    unshift(@INC,$pathLibsProntus);
};

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use glib_cgi_04;
use glib_fildir_02;
use glib_html_02;
use glib_dbi_02;
use POSIX qw/ceil/;

my %FORM;
my $BD;

main: {
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    my $path_conf = $FORM{'_path_conf'};
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    $FORM{'MTAG_ID'}          = &glib_cgi_04::param('id');
    $FORM{'TYPE'}             = &glib_cgi_04::param('type');

    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();

    if (!ref($BD)) {
        print STDERR "Error conectar BD: $msg_err_bd\n";
        &glib_html_02::print_json_result(0, "Error conectar BD: $msg_err_bd", 'exit=1,ctype=1');
        exit;
    };

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    if (!$FORM{'MTAG_ID'} || !$FORM{'TYPE'}) {
        &glib_html_02::print_json_result(0, 'ID o tipo no ingresados.', 'exit=1,ctype=1');
    } else {
        &elimina_item($FORM{'MTAG_ID'}, $FORM{'TYPE'});
    }


    &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');
};

sub elimina_item {
    my $id = $_[0];
    my $type = $_[1];

    $type = 'S' if ($type eq 'seccion');
    $type = 'T' if ($type eq 'tema');
    $type = 'ST' if ($type eq 'subtema');

    if (!&en_uso($id, $type)) {
        my $sql = "DELETE FROM MTAG_$type WHERE MTAG_$type\_ID = $id";

        &glib_dbi_02::ejecutar_sql($BD, $sql);
    } else {
        &glib_html_02::print_json_result(0, 'No se puede eliminar porque esta en uso.', 'exit=1,ctype=1');
    }
};

sub en_uso {
    my $id = $_[0];
    my $type = $_[1];
    my ($sql, $salida, $count);

    $type = 'S' if ($type eq 'seccion');
    $type = 'T' if ($type eq 'tema');
    $type = 'ST' if ($type eq 'subtema');

    $sql = "SELECT COUNT(*) FROM MTAG_ART_$type WHERE MTAG_ART_$type\_ID = $id";
    $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($count));
    $salida->fetch;
    $salida->finish;

    return $count;
};
