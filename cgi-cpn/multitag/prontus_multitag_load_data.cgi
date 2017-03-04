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
# Carga los datos de multitags disponibles y los deveulve como json
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
use utf8;

my %FORM;
my $BD;

main: {
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    my $path_conf = $FORM{'_path_conf'};
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();

    if (!ref($BD)) {
        print STDERR "Error conectar BD: $msg_err_bd\n";
        &glib_html_02::print_json_result(0, "Error conectar BD: $msg_err_bd");
        exit;
    };

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    my %resp;

    $resp{'secciones'} = &cargar_secciones();
    $resp{'temas'} = &cargar_temas();
    $resp{'subtemas'} = &cargar_subtemas();

    print "Content-type: application/json; charset=utf-8\n\n";

    &glib_html_02::print_json_result_hash(\%resp, 'exit=1');
};

sub cargar_secciones {
    my ($sql, $salida);
    my ($mtag_s_id, $multitag_s_nombre, $multitag_s_friendly, $multitag_s_estado);
    my @secciones;

    $sql = "SELECT MULTITAG_S_ID, MULTITAG_S_NOMBRE, MULTITAG_S_FRIENDLY, MULTITAG_S_ESTADO FROM MULTITAG_S ORDER BY MULTITAG_S_NOMBRE";
    $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($multitag_s_id, $multitag_s_nombre, $multitag_s_friendly, $multitag_s_estado));

    while ($salida->fetch) {
        utf8::decode($multitag_s_nombre);
        my %data = (
            'MULTITAG_s_id'         => $multitag_s_id,
            'MULTITAG_s_nombre'     => $multitag_s_nombre,
            'MULTITAG_s_friendly'   => $multitag_s_friendly,
            'MULTITAG_s_estado'     => $multitag_s_estado
        );

        push @secciones, \%data
    }

    $salida->finish;
    return \@secciones;
};

sub cargar_temas {
    my ($sql, $salida);
    my ($multitag_t_id, $multitag_t_nombre, $multitag_t_friendly, $multitag_t_estado);
    my @temas;

    $sql = "SELECT MULTITAG_T_ID, MULTITAG_T_NOMBRE, MULTITAG_T_FRIENDLY, MULTITAG_T_ESTADO FROM MULTITAG_T ORDER BY MULTITAG_T_NOMBRE";
    $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($multitag_t_id, $multitag_t_nombre, $multitag_t_friendly, $multitag_t_estado));

    while ($salida->fetch) {
        utf8::decode($multitag_t_nombre);
        my %data = (
            'MULTITAG_t_id'         => $multitag_t_id,
            'MULTITAG_t_nombre'     => $multitag_t_nombre,
            'MULTITAG_t_friendly'   => $multitag_t_friendly,
            'MULTITAG_t_estado'     => $multitag_t_estado
        );
        push @temas, \%data
    }

    $salida->finish;
    return \@temas;
};

sub cargar_subtemas {
    my ($sql, $salida);
    my ($multitag_st_id, $multitag_st_nombre, $multitag_st_friendly, $multitag_st_estado);
    my @subtemas;

    $sql = "SELECT MULTITAG_ST_ID, MULTITAG_ST_NOMBRE, MULTITAG_ST_FRIENDLY, MULTITAG_ST_ESTADO FROM MULTITAG_ST ORDER BY MULTITAG_ST_NOMBRE";
    $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($multitag_st_id, $multitag_st_nombre, $multitag_st_friendly, $multitag_st_estado));

    while ($salida->fetch) {
        utf8::decode($multitag_st_nombre);
        my %data = (
            'MULTITAG_st_id'         => $multitag_st_id,
            'MULTITAG_st_nombre'     => $multitag_st_nombre,
            'MULTITAG_st_friendly'   => $multitag_st_friendly,
            'MULTITAG_st_estado'     => $multitag_st_estado
        );

        push @subtemas, \%data
    }

    $salida->finish;
    return \@subtemas;
};
