#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Indica el estado de una transcodificacion.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cgi, usando metodo GET o POST. Los parametros son:
# video  - Path relativo al video a transcodificar.
#
# Retorna 'None', 'Busy' o 'Ready'
#
# Ejemplo:
#
# /cgi-cpn/prontus_videoxcodestatus.cgi?video=prontus_proto/site/artic/20100531/mmedia/multimedia_video120100531182447.wmv
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------

# 1.0 - 01/06/2010 - ??? - Primera version.
# 1.1 - 13/08/2013 - JOR - Cambia respuesta a formato json.

# -------------------------------BEGIN SCRIPT--------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/xcoding$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use lib_prontus;
use strict;

my %FORM;        # Contenido del formulario de invocacion.
my $RES;

use glib_fildir_02;

main: {

    &glib_cgi_04::new();
    &glib_cgi_04::set_formvar('video', \%FORM);
    &glib_cgi_04::set_formvar('prontus_id', \%FORM);

    # Valida datos de entrada
    my $msg_err;
    my $destfile;
    $destfile = $FORM{'video'};
    $destfile =~ s/\.\w+$/\.mp4/;
    
    $msg_err = "Parámetro [video] no es válido [$FORM{'video'}]" if ( ((!-f "$prontus_varglb::DIR_SERVER$FORM{'video'}") || (!-s "$prontus_varglb::DIR_SERVER$FORM{'video'}"))&& ((!-f "$prontus_varglb::DIR_SERVER$destfile") || (!-s "$prontus_varglb::DIR_SERVER$destfile")));
    $msg_err = "Parámetro [prontus_id] no es válido" if (! &lib_prontus::valida_prontus($FORM{'prontus_id'}));
    $msg_err = "Parámetro [prontus_id] no es válido" if (!-d "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}");
    &glib_html_02::print_json_result(0, "Error: $msg_err", 'exit=1,ctype=1') if ($msg_err);

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);  # Prontus 6.0
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

    # User check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    my ($status, $msg) = &xcode_status();

    &glib_html_02::print_json_result($status, $msg, 'exit=1,ctype=1');
};

# -------------------------------------------------------------------#
# Verifica el estado de la transcodificacion.
sub xcode_status {
    my ($cmd,$destino);
    my $origen = $FORM{'video'};

    if ($origen =~ /^\//) {
        $origen = $prontus_varglb::DIR_SERVER . $origen;
    } else {
        $origen = $prontus_varglb::DIR_SERVER .'/'. $origen;
    };

    # Verifica si el transcoding esta en ejecucion.
    my $res = qx/ps auxww |grep 'prontus_videodoxcode.cgi $origen'|grep -v grep/;

    if ($res ne '') {
        return (1, 'busy');
    };

    # Forma el nombre de la pelicula destino sustituyendo la extension.
    $destino = $origen;
    $destino =~ s/\.\w+$/\.mp4/;

    # Ve si el destino esta en el XML
    my $esta_en_xml = 0;
    my $ts;
    print STDERR  "destino[$destino]\n";
    if ($destino =~ /(.+)\/(.*?)\/(\d{8})\/mmedia\/(multimedia_video.+?(\d{6}))\.(\w+)$/) {
        my $path = $1. $prontus_varglb::DIR_ARTIC . '/'. $3 .'/xml/'. $3 . $5 . '.xml';
        my $filename = $4;
        my $extension = $6;
        $ts = $2 . $4;
        print STDERR "[$path][$filename][$extension]\n";
        my $buffer = &glib_fildir_02::read_file($path);
        if ($buffer =~ /$filename\.mp4/s) {
            $esta_en_xml = 1;
        };
    };

    print STDERR  "esta_en_xml[$esta_en_xml]\n";

    if ((-s $destino > 0) && ($esta_en_xml)) {
        my $file = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/procs/xcoding_status_$ts.txt";
        if (-f $file) {
            my $buffer = &glib_fildir_02::read_file($file);
            if ($buffer ne '') {
                print STDERR "error[$buffer]\n";
                unlink $file;
                return (0, $buffer);
            };
            unlink $file;
        };
        
        return (1, 'ready');
    } else {
        # Si no esta el archivo en disco ni en el xml, se gatillará de nuevo la transcodificación.
        return (1, 'none');
    };
};
