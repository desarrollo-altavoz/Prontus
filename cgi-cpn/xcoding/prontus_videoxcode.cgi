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
# Transcodificar un video de avi, wmv, mp4, mpeg, rm y otros a mp4.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# LLama a prontus_videodoxcode.cgi para que haga realmente la pega.
# prontus_videodoxcode.cgi al terminar elimina el video original y sustituye el nombre en el xml del articulo Prontus.
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cgi, usando metodo GET o POST. Los parametros son:
# video  - Path relativo al video a transcodificar.
# w - ancho de la pelicula final.
# h - alto de la pelicula final.
#
# Retorna 'OK' o 'Error: <mensaje de error>';
#
# Ejemplo:
#
# /cgi-cpn/prontus_videoxcode.cgi?video=/prontus_proto/site/artic/20100531/mmedia/multimedia_video120100531182139.wmv&w=320&h=240
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------

# 1.0.0 - 31/05/2010 - ??? - Primera version.
# 1.1.0 - 07/09/2012 - ??? - Se pone un limite de tamaño de origen a 50MB para transcodificar.
# 1.1.1 - 07/09/2012 - ??? - Limite de tamaño de origen para transcodificar se hace configurable.
# 1.2.0 - 13/08/2013 - JOR - La ejecucion del script que hace la transcodificacion se hace en segundo plano.

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

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use lib_prontus;
use strict;
use lib_lock;

my %FORM;        # Contenido del formulario de invocacion.

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    &glib_cgi_04::set_formvar('video', \%FORM);
    &glib_cgi_04::set_formvar('prontus_id', \%FORM);
    &glib_cgi_04::set_formvar('generar_versiones', \%FORM);


    # Valida datos de entrada
    my $msg_err;
    $msg_err = "Parámetro [video] no es válido [$FORM{'video'}]" if ((!-f "$prontus_varglb::DIR_SERVER$FORM{'video'}") || (!-s "$prontus_varglb::DIR_SERVER$FORM{'video'}"));
    $msg_err = "Parámetro [prontus_id] no es válido" if ($FORM{'prontus_id'} !~ /^[\w\-]+$/);
    $msg_err = "Parámetro [prontus_id] no es válido" if (!-d "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}");

    &glib_html_02::print_json_result(0, "Error: $msg_err", 'exit=1,ctype=1') if ($msg_err);

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);  # Prontus 6.0
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

    # chequeo de tamaño de archivo
    # no se procesa si es mas grande de 50 MB 52428800 por defecto
    $msg_err = "Tamaño de archivo es muy grande para ser transcodificado, límite: [$prontus_varglb::MAX_XCODING MB]" if ( (-s "$prontus_varglb::DIR_SERVER$FORM{'video'}") > ($prontus_varglb::MAX_XCODING*1048576));
    &glib_html_02::print_json_result(0, "Error: $msg_err", 'exit=1,ctype=1') if ($msg_err);

    # User check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };


    # Startea transcodificacion y devuelve respuesta json
    my ($status, $msg) = &start_xcode();
    &glib_html_02::print_json_result($status, $msg, 'exit=1,ctype=1');
};

# -------------------------------------------------------------------#
# Inicia la transcodificacion.
sub start_xcode {
    my $prontus_id = $FORM{'prontus_id'};
    my $origen = "$prontus_varglb::DIR_SERVER$FORM{'video'}";
    # use FindBin '$Bin';
    my $pathnice = &lib_prontus::get_path_nice();
    my $cmd = "$pathnice /usr/bin/perl $Bin/prontus_videodoxcode.cgi $origen $prontus_id";

    if ($FORM{'generar_versiones'} eq '1') {
        print STDERR "gatillando[$cmd 1] generar versiones.\n";
        system("$cmd 1 >/dev/null 2>&1 &");
        return (1, 'Transcodificación en proceso...');
    };

    # No transcodifica peliculas que ya son mp4.
    if ($origen =~ /\.mp4$/i) {
        return (0, "Error: El video ya es mp4, no es necesario transcodificarlo.");
    };

    # Verifica que no haya otro transcoding identico en ejecucion.
    # my $res = qx/ps auxww |grep ffmpeg|grep $origen|grep -v grep/;
    my $res = qx/ps auxww |grep 'prontus_videodoxcode.cgi $origen $prontus_id'|grep -v grep/;

    # print STDERR "Execution test = [$res][ps auxww |grep 'prontus_videodoxcode.cgi $origen $prontus_id'|grep -v grep]\n";

    if ($res ne '') {
        return (0, 'Error: Se detectó un proceso activo de transcodificación para el video indicado.');
    };


    # Gatilla la transcodificacion en background.

    print STDERR "gatillando[$cmd 0]\n";
    system("$cmd 0 >/dev/null 2>&1 &");

    return (1, 'Transcodificación en proceso...');
};

