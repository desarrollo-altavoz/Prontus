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
use utf8;
use prontus_varglb; &prontus_varglb::init();
use JSON;
use glib_fildir_02;
use glib_html_02;
use glib_cgi_04;
use lib_prontus;
use lib_xcoding;

#~ use Data::Dumper;

my %FORM;        # Contenido del formulario de invocacion.

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    &glib_cgi_04::set_formvar('prontus_id', \%FORM);
    &glib_cgi_04::set_formvar('formatos', \%FORM);

    #~ print STDERR Dumper(\%FORM);

    # Valida datos de entrada
    my $msg_err;
    $msg_err = "Parámetro [prontus_id] no es válido" if (! &lib_prontus::valida_prontus($FORM{'prontus_id'}));
    $msg_err = "Parámetro [prontus_id] no es válido" if (!-d "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}");

    # imprimimos las cabeceras de la respuesta
    print "Cache-Control: no-cache, must-revalidate\r\n";
    print "Content-type: application/json\n\n";

    &glib_html_02::print_json_result(0, "Error: $msg_err", 'exit=1,ctype=0') if ($msg_err);

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

    # User check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=0');
    };

    # los datos se obtienen en json, se descodifican y dejan como hash
    my $data;
    if($JSON::VERSION =~ /^1\./) {
        my $json = new JSON;
        $data = $json->jsonToObj($FORM{'formatos'});
    } else {
        $data = decode_json($FORM{'formatos'});
    }

    # se arma el string de los formatos para guardarlos
    my $formatos = '';
    foreach my $marca (sort keys(%{$data})) {
        foreach my $param (sort keys(%{$data->{$marca}})) {
            # si no viene valor en el parametro, no se guarda
            if ($data->{$marca}->{$param} eq '') {
                next;
            }
            $formatos .= uc("$marca\.$param")." = '".$data->{$marca}->{$param}."'\n";
        }
        $formatos .= "\n";
    }
    print STDERR "[$formatos]\n";

    my $dir_formatos = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID$lib_xcoding::XCODING_DATA_PATH";

    # guardamos los formatos para ser usados posteriormente
    if (&glib_fildir_02::check_dir($dir_formatos)) {
        &glib_fildir_02::write_file($dir_formatos . $lib_xcoding::FORMATS_FILE, $formatos);
        &glib_html_02::print_json_result(1, "Guardado correcto", 'exit=1,ctype=0');
    } else {
        &glib_html_02::print_json_result(0, "Error: Ha ocurrido un error al guardar los formatos de video", 'exit=1,ctype=0');
    }
}
# -------------------------------------------------------------------#
