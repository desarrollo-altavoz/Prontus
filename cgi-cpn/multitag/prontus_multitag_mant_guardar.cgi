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
# Guardar una nueva categoria con su url
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
#
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

use utf8;
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

    # MULTITAG_S_ID, MULTITAG_S_NOMBRE, MULTITAG_S_FRIENDLY, MULTITAG_S_ESTADO
    $FORM{'MULTITAG_ID'}          = &glib_cgi_04::param('id');
    $FORM{'TYPE'}             = &glib_cgi_04::param('type');
    $FORM{'MULTITAG_NOMBRE'}      = &glib_cgi_04::param('nombre');
    $FORM{'MULTITAG_NOMBRE'}      = &lib_prontus::despulga_item_tag($FORM{'MULTITAG_NOMBRE'}); # revisar
    $FORM{'MULTITAG_FRIENDLY'}    = &glib_cgi_04::param('friendly');
    $FORM{'MULTITAG_FRIENDLY'}    = &lib_prontus::despulgar_texto_friendly($FORM{'MULTITAG_FRIENDLY'});
    $FORM{'MULTITAG_ESTADO'}      = &glib_cgi_04::param('estado');
    $FORM{'SOLO_ESTADO'}      = &glib_cgi_04::param('solo_estado');

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

    my %resp;

    if (!$FORM{'MULTITAG_ID'}) {
        # Es nuevo.
        $FORM{'MULTITAG_ID'} = &nuevo_item();

        if (!$FORM{'MULTITAG_ID'}) {
            &glib_html_02::print_json_result(0, 'Error al insertar registro. Inténtalo nuevamente.', 'exit=1,ctype=1');
        }

        utf8::decode($FORM{'MULTITAG_NOMBRE'});

        %resp = (
            'status'    => 1,
            'msg'       => '',
            'id'        => $FORM{'MULTITAG_ID'},
            'nombre'    => $FORM{'MULTITAG_NOMBRE'},
            'friendly'  => $FORM{'MULTITAG_FRIENDLY'},
            'type'      => $FORM{'TYPE'},
            'estado'    => 1
        );
    } else {
        # Modificando.
        &actualiza_item();

        utf8::decode($FORM{'MULTITAG_NOMBRE'});

        %resp = (
            'status'    => 1,
            'msg'       => '',
            'id'        => $FORM{'MULTITAG_ID'},
            'nombre'    => $FORM{'MULTITAG_NOMBRE'},
            'type'      => $FORM{'TYPE'}
        );
    }

    print "Content-type: application/json; charset=utf-8\n\n";
    &glib_html_02::print_json_result_hash(\%resp, 'exit=1');
};

sub nuevo_item {
    my ($sql, $salida);

    # Validacion.
    if (!$FORM{'MULTITAG_NOMBRE'}) {
        &glib_html_02::print_json_result(0, 'El nombre es obligatorio.', 'exit=1,ctype=1');
    } elsif (length $FORM{'MULTITAG_NOMBRE'} > 64) {
        &glib_html_02::print_json_result(0, 'El nombre es muy largo.', 'exit=1,ctype=1');
    }

    if (!$FORM{'MULTITAG_FRIENDLY'}) {
        &glib_html_02::print_json_result(0, 'El nombre friendly obligatorio.', 'exit=1,ctype=1');
    } elsif (length $FORM{'MULTITAG_FRIENDLY'} > 32) {
        &glib_html_02::print_json_result(0, 'El nombre friendly es muy largo.', 'exit=1,ctype=1');
    } elsif ($FORM{'MULTITAG_FRIENDLY'} =~ /[^a-z0-9\-]+/) {
        &glib_html_02::print_json_result(0, 'La Friendly URL tiene caracteres inválidos. Solo se permiten letras, números y "-".', 'exit=1,ctype=1');
    }

    if (&check_name_y_friendly($FORM{'MULTITAG_NOMBRE'}, $FORM{'MULTITAG_FRIENDLY'}, $FORM{'TYPE'})) {
        &glib_html_02::print_json_result(0, 'Nombre o Friendly URL ya existen. Elija otro.', 'exit=1,ctype=1');
    }

    $sql = "INSERT INTO MULTITAG_%%type%% SET MULTITAG_%%type%%_NOMBRE = '$FORM{'MULTITAG_NOMBRE'}', MULTITAG_%%type%%_FRIENDLY = '$FORM{'MULTITAG_FRIENDLY'}'";

    $sql =~ s/%%type%%/S/sg if ($FORM{'TYPE'} eq 'seccion');
    $sql =~ s/%%type%%/T/sg if ($FORM{'TYPE'} eq 'tema');
    $sql =~ s/%%type%%/ST/sg if ($FORM{'TYPE'} eq 'subtema');

    #~ print STDERR "sql[$sql]\n";

    my $id = &glib_dbi_02::insert_dev_id($BD, $sql);

    return $id;
};

sub actualiza_item {
    my ($sql, $salida, $set);

    $sql = "UPDATE MULTITAG_%%type%% %%set%% WHERE MULTITAG_%%type%%_ID = $FORM{'MULTITAG_ID'}";

    # Validacion.
    if (!$FORM{'SOLO_ESTADO'}) {
        if (!$FORM{'MULTITAG_NOMBRE'}) {
            &glib_html_02::print_json_result(0, 'El nombre es obligatorio.', 'exit=1,ctype=1');
        } elsif (length $FORM{'MULTITAG_NOMBRE'} > 64) {
            &glib_html_02::print_json_result(0, 'El nombre es muy largo.', 'exit=1,ctype=1');
        }

        if ($FORM{'MULTITAG_NOMBRE'}) {
            $set .= "SET MULTITAG_%%type%%_NOMBRE = '$FORM{'MULTITAG_NOMBRE'}'";
        }
    }

    if ($FORM{'MULTITAG_ESTADO'}) {
        $set .= ',' if ($set);
        $set .= 'SET ' if (!$set);

        $FORM{'MULTITAG_ESTADO'} = 1 if ($FORM{'MULTITAG_ESTADO'} eq 'on');
        $FORM{'MULTITAG_ESTADO'} = 0 if ($FORM{'MULTITAG_ESTADO'} eq 'off');

        $set .= "MULTITAG_%%type%%_ESTADO = $FORM{'MULTITAG_ESTADO'}";
    }

    $sql =~ s/%%set%%/$set/sg;

    $sql =~ s/%%type%%/S/sg if ($FORM{'TYPE'} eq 'seccion');
    $sql =~ s/%%type%%/T/sg if ($FORM{'TYPE'} eq 'tema');
    $sql =~ s/%%type%%/ST/sg if ($FORM{'TYPE'} eq 'subtema');

    #~ print STDERR "sql[$sql]\n";

    &glib_dbi_02::ejecutar_sql($BD, $sql);
};


sub check_name_y_friendly {
    my $name = $_[0];
    my $friendly = $_[1];
    my $type = $_[2];
    my ($sql, $salida, $count);

    $type = 'S' if ($type eq 'seccion');
    $type = 'T' if ($type eq 'tema');
    $type = 'ST' if ($type eq 'subtema');

    $sql = "SELECT COUNT(*) FROM MULTITAG_$type WHERE MULTITAG_$type\_NOMBRE = '$name' OR MULTITAG_$type\_FRIENDLY = '$friendly'";
    $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($count));
    $salida->fetch;
    $salida->finish;

    return $count;
};
