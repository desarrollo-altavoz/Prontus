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
# /cgi-cpn/api/xcoding_getformatos.cgi?prontus_id=prontus_id
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 09/06/2015 - EAG - Primera version.
# -------------------------------BEGIN SCRIPT--------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/api$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
    $pathLibsProntus .= '/xcoding';
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ---------------------------------------------------------------
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use utf8;
use prontus_varglb; &prontus_varglb::init();
use JSON;
use glib_html_02;
use glib_cgi_04;
use lib_prontus;
use lib_xcoding;

binmode STDOUT, ":encoding(utf8)";

use Data::Dumper;

my %FORM; # Contenido del formulario de invocacion.

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    &glib_cgi_04::set_formvar('prontus_id', \%FORM);

    # la salida es tipo json
    print "Cache-Control: no-cache, must-revalidate\r\n";
    print "Content-type: application/json\n\n";

    # Valida datos de entrada
    my $msg_err;
    $msg_err = "Parámetro [prontus_id] no es válido, caracteres incorrectos." if (! &lib_prontus::valida_prontus($FORM{'prontus_id'}));
    $msg_err = "Parámetro [prontus_id] no es válido" if (!-d "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}");

    &glib_html_02::print_json_result(0, "Error: $msg_err", 'exit=1,ctype=0') if ($msg_err);

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

    # carga de los formatos
    my %data = ();
    %{$data{'data'}} = &lib_xcoding::get_all_formatos();
    %{$data{'max_settings'}} = ('MAX_VIDEO_BITRATE' => $prontus_varglb::MAX_VIDEO_BITRATE,
                                'MAX_AUDIO_BITRATE' => $prontus_varglb::MAX_AUDIO_BITRATE,
                                'XCODE_MAX_PIXEL'   => $prontus_varglb::XCODE_MAX_PIXEL
                                );

    if (keys %{$data{'data'}}) {
        $data{'status'} = 1;
        print encode_json(\%data);
    } else {
        print '{}';
    }
}
# -------------------------------------------------------------------#
