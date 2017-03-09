#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

#
# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Elimina el archivod e datos de respaldo de un formulario Prontus.
#
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# El archivo de datos a eliminar se encuentra en:
# /<prontus>/cpan/procs/form/<ts>/backup.csv
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cgi, usando metodo POST. Los parametros son:
# prontus  - Nombre del directorio Prontus.
# ts       - Timestamp del articulo tipo formulario cuyos datos hay que eliminar.
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# /<prontu>/cpan/fid/msg.html - Plantilla de mensajes de resultado de operaciones.
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 16/05/2007 - Primera version.
#
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

# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

use strict;
use prontus_varglb; &prontus_varglb::init();

use glib_fildir_02;
use glib_html_02;

use lib_prontus;
use lib_form;

main: {
    my $hashref = &lib_form::getFormData(); # Lee formulario de invocacion y valida las variables.
    my %FORM = %$hashref;

    my $ROOT    = $ENV{'DOCUMENT_ROOT'};
    my $PRONTUS = $FORM{'_prontus_id'}; # Nombre del publicador Prontus donde se aloja el formulario.
    my $TS      = $FORM{'_ts'};      # Nombre del publicador Prontus donde se aloja el formulario.

    if ($PRONTUS eq '') { # Muestra pagina en blanco.
        &glib_html_02::print_json_result(0, 'Directorio Prontus no especificado', 'exit=1,ctype=1');
    };
    my $PATH_CONF = "/$PRONTUS/cpan/$PRONTUS.cfg";

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $PATH_CONF = &lib_prontus::ajusta_pathconf($PATH_CONF);

    # Carga variables de configuracion.
    &lib_prontus::load_config($PATH_CONF);  # Prontus 6.0
    $PATH_CONF =~ s/^$prontus_varglb::DIR_SERVER//;

    # Se chequean los permisos
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    if ($prontus_varglb::USERS_ID eq '' || $prontus_varglb::USERS_PERFIL ne 'A') {
        &glib_html_02::print_json_result(0, 'No tiene permisos para realizar esta accion', 'exit=1,ctype=1');
    }

    if ($TS eq '') { # Muestra pagina en blanco.
        &glib_html_02::print_json_result(0, 'Formulario no especificado', 'exit=1,ctype=1');
    };

    &lib_prontus::write_log('Borrar Datos', 'Prontus Form', "TS[$TS]", $prontus_varglb::USERS_USR);

    my $dirForm = "$ROOT/$PRONTUS/cpan/procs/form/$TS";
    if(-d $dirForm) {
        &glib_fildir_02::borra_dir($dirForm);
    } else {
        &glib_html_02::print_json_result(0, 'No se pudo eliminar el directorio con los datos', 'exit=1,ctype=1');
    };

    &glib_html_02::print_json_result(1, 'El archivo de datos de respaldo ha sido eliminado', 'exit=1,ctype=1');
};
# ###################################################
# Funciones
