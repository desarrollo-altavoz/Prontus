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
# Genera el HLS de las versiones de videos, despues de ser cortados
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Usa ffmpeg
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Por linea de comandos.
# Los parametros son:
# 0- Path absoluto al video.
# 1- prontus id
#
# /usr/bin/perl prontus_videoxcodeparallel.cgi /sites/prontus_lab/web/prontus_proto/site/artic/20100531/mmedia/multimedia_video120100531182139.avi prontus_proto
# my $cmd = "$pathnice /usr/bin/perl $Bin/prontus_videoxcodeparallel.cgi $origen $prontus_id";
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------
# 1.0.0 - 03/06/2015 - EAG - Primera version.
# ---------------------------------------------------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/xcoding$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};
# ---------------------------------------------
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use lib_prontus;
use prontus_varglb; &prontus_varglb::init();
use lib_xcoding;
use strict;
use utf8;
#~ use Data::Dumper;

my $ORIGEN = $ARGV[0];
my $PRONTUS_ID = $ARGV[1];
my $ARTIC_dirfecha;
my $ARTIC_ts_articulo;
my $ARTIC_path_xml;
my $ARTIC_filename;
my $ARTIC_extension;
my %FORMATOS_VERSIONES; # hash que guarda los formatos de las versiones del video
my $MARCA; # nombre de la marca prontus del video

# ---------------------------------------------------------------
main: {
    &die_stderr("El parámetro 'origen' no es válido.", "", 1) if ((!-f "$ORIGEN") || (!-s "$ORIGEN"));
    &die_stderr("El parámetro 'prontus_id' no es válido.", "", 1) if (! &lib_prontus::valida_prontus($PRONTUS_ID));
    &die_stderr("El parámetro 'prontus_id' no es válido.", "", 1) if (!-d "$prontus_varglb::DIR_SERVER/$PRONTUS_ID");

    my ($start, $total, $segundos);
    $start = time; # tiempo inicial para medir la duracion del proceso

    if (!&load_artic_info()) {
        &die_stderr("No se obtener la información del artículo asociado al video.", "", 1);
    };

    $ORIGEN =~ /\/mmedia\/(multimedia_video\d+)\d{14}\.(\w+)$/i;
    $MARCA = $1;

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$PRONTUS_ID/cpan/$PRONTUS_ID.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);  # Prontus 6.0

    print STDERR "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] [$ARTIC_filename] Inicio Proceso de Corte\n";

    # inicializamos los valores de la libreria
    $lib_xcoding::PATHNICE = &lib_prontus::get_path_nice();

    # regeneramos hls para el video principal
    &lib_xcoding::generar_HLS($ORIGEN);

    # cargamos los formatos para esta marca
    my %formatos_versiones = &lib_xcoding::get_formatos($MARCA);

    foreach my $key (sort keys(%formatos_versiones)) {
        #~ print STDERR "Generando HLS para [$key] [$ARTIC_ts_articulo]\n";
        my $new_name = $key;
        $new_name =~ s/\./$ARTIC_ts_articulo/sg;
        $new_name = lc $new_name;
        my $new_origen = $ORIGEN;
        $new_origen =~ s/\/multimedia_video\d+\d{14}\.(\w+)$/\/$new_name\.mp4/is;
        &lib_xcoding::generar_HLS($new_origen);
    }

    $total = time - $start;
    $segundos = $total % 60;
    $segundos = $segundos < 10? '0'.$segundos : $segundos;
    print STDERR "[$ARTIC_filename] Tiempo Total Transcodificacion de Corte [".int($total/60) .":". $segundos ."]\n";

    # Dropbox.
    &call_dropbox_backup($ARTIC_ts_articulo);
};

# ---------------------------------------------------------------
sub call_dropbox_backup {
    my $ts = $_[0];

    if ($prontus_varglb::DROPBOX eq 'SI') {
        &lib_prontus::dropbox_backup("art;$ts");
    };
};
# ---------------------------------------------------------------
sub load_artic_info {
    # Deduce ubicacion del xml del articulo.
    if ($ORIGEN =~ /(.+)\/(.*?)\/(\d{8})\/mmedia\/(multimedia_video.+?(\d{6}))\.(\w+)$/) {
        $ARTIC_dirfecha = $3;
        $ARTIC_ts_articulo = $3 . $5;
        $ARTIC_path_xml = $1 . $prontus_varglb::DIR_ARTIC . '/'. $3 .'/xml/'. $ARTIC_ts_articulo . '.xml';
        $ARTIC_filename = $4;
        $ARTIC_extension = $6;

        return 1;
    } else {
        return 0;
    };
};
# ---------------------------------------------------------------
sub die_stderr {
    my $msg = $_[0];
    my $detalle = $_[1];
    my $write = $_[2];
    &write_status($msg) if ($write);
    print STDERR "[ERROR] $msg - $detalle";
    exit 1;
};
# ---------------------------------------------------------------
sub write_status {
    my $msg = $_[0];
    $msg =~ s/\n//sg;
    my $file = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/procs/xcoding_status_$ARTIC_ts_articulo.txt";

    &glib_fildir_02::write_file($file, $msg);
};
