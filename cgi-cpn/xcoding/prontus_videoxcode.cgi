#!/usr/bin/perl
#
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

# 1.0.0 - 31/05/2010 - Primera version.
# 1.1.0 - 07/09/2012 - Se pone un limite de tamaño de origen a 50MB para transcodificar.
# 1.1.1 - 07/09/2012 - Limite de tamaño de origen para transcodificar se hace configurable.

# -------------------------------BEGIN SCRIPT--------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
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


my %FORM;        # Contenido del formulario de invocacion.

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    &glib_cgi_04::set_formvar('video', \%FORM);
    &glib_cgi_04::set_formvar('prontus_id', \%FORM);

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
    my ($status, $msg) = &startXCode();
    &glib_html_02::print_json_result($status, $msg, 'exit=1,ctype=1');
};

# -------------------------------------------------------------------#
# Inicia la transcodificacion.
sub startXCode {

    my $origen = "$prontus_varglb::DIR_SERVER$FORM{'video'}";

    # No transcodifica peliculas que ya son mp4.
    if ($origen =~ /\.mp4$/i) {
        return (0, "Error: El video ya es mp4, no es necesario transcodificarlo.");
    };

    # Verifica que no haya otro transcoding identico en ejecucion.
    # my $res = qx/ps auxww |grep ffmpeg|grep $origen|grep -v grep/;
    my $prontus_id = $FORM{'prontus_id'};
    my $res = qx/ps auxww |grep 'prontus_videodoxcode.cgi $origen $prontus_id'|grep -v grep/;

    print STDERR "Execution test = [$res][ps auxww |grep 'prontus_videodoxcode.cgi $origen $prontus_id'|grep -v grep]\n";
    if ($res ne '') {
        return (0, 'Error: Se detectó un proceso activo de transcodificación para el video indicado.');
    };
    use FindBin '$Bin';
    my $pathnice = '/usr/bin/nice';
    if (! -f $pathnice) {
      $pathnice = '/usr/local/bin/nice';
      if (! -f $pathnice) {
        $pathnice = '';
      }
    }
    my $cmd = "$pathnice /usr/bin/perl $Bin/prontus_videodoxcode.cgi $origen $prontus_id";
    # Gatilla la transcodificacion en background.
    # print "$cmd \n";
    # $res = `$cmd 2>&1 &`;
    print STDERR "gatillando[$cmd]\n";
    $res = `$cmd 2>&1 &`; # devuelve a $res todo lo que se tirte a STDOUT o a STDERR
    sleep(3);
    print STDERR "result from doxcode\nres[$res][$?][$!]\n"; # LOGUEA TODO LO RESPONDIDO
    if ($res eq '') {
        if ($? != 0) {
            return (0, "Error: Falló la ejecución del proceso de transcodificación. Los detalles fueron agregados al error log interno de Prontus.");
            print STDERR "error al transcodificar[$?][$!]\n";
        };
        return (1, '');
    } else {
        # si $res trae algo, solo considera que es error si trae el token [ERROR] o si se cayo el script invocado, en cuyo caso setea $?,  ya que lo demas es debug
        if (($res =~ /\[ERROR\]/) || ($? != 0)) {
            $res =~ s/[\r\n]/ /sg;
            return (0, "Error: Falló la ejecución del proceso de transcodificación. Los detalles fueron agregados al error log interno de Prontus.");
        };
        return (1, '');
    };
}; # startXCode
