#!/usr/bin/perl

# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Carga los formatos guardados de xcoding
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cgi, usando metodo GET o POST. Los parametros son:
# prontus_id  - Identificador del prontus
#
# Retorna los formatos en un objeto json
#
# Ejemplo:
#
# /cgi-cpn/xcoding/prontus_xcoding_getformatos.cgi?prontus_id=prontus_id
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 27/04/2015 - EAG - Primera version.
# -------------------------------BEGIN SCRIPT--------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/xcoding$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ---------------------------------------------------------------
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use prontus_varglb; &prontus_varglb::init();
use JSON;
use glib_html_02;
use glib_cgi_04;
use lib_prontus;
use lib_xcoding;
use utf8;
#~ use Data::Dumper;

my %FORM;        # Contenido del formulario de invocacion.

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    &glib_cgi_04::set_formvar('prontus_id', \%FORM);

    # Valida datos de entrada
    my $msg_err;
    $msg_err = "Parámetro [prontus_id] no es válido" if (! &lib_prontus::valida_prontus($FORM{'prontus_id'}));
    $msg_err = "Parámetro [prontus_id] no es válido" if (!-d "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}");

    &glib_html_02::print_json_result(0, "Error: $msg_err", 'exit=1,ctype=1') if ($msg_err);

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

    # User check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    # carga de los formatos
    my %data = ();
    %{$data{'data'}} = &lib_xcoding::get_all_formatos();

    print "Cache-Control: no-cache, must-revalidate\r\n";
    print "Content-type: application/json\n\n";

    if (keys %{$data{'data'}}) {
        $data{'status'} = 1;
        if ($JSON::VERSION =~ /^1\./) {
            my $json = new JSON;
            print $json->objToJson(\%data);
        } else {
            print encode_json(\%data);
        }
    } else {
        print '{}';
        #~ &glib_html_02::print_json_result(0, "Ha ocurrido un error al cargar los formatos de video", 'exit=1,ctype=0')
    }
}
# -------------------------------------------------------------------#
