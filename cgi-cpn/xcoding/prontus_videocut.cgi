#!/usr/bin/perl
#
# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Elimina el inicio o el final de un video.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Lee el video lo vuelve a escribir recortado.
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cgi, usando metodo GET o POST. Los parametros son:
# video  - Path relativo al video a recortar.
# cut - Tipo de corte: begin elimina el inicio; end elimina el final.
#
# Retorna 'OK' o 'Error: <mensaje de error>';
#
# Ejemplo:
#
# /cgi-cpn/prontus_videocut.cgi?video=prontus_proto/site/artic/20100531/mmedia/tele1.flv&t=60&cut=begin
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------

# 1.0 - 31/05/2010 - Primera version.

# -------------------------------BEGIN SCRIPT--------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
    $pathLibsProntus =~ s/\/xcoding$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use glib_cgi_04;
use strict;
use FindBin '$Bin';

my %FORM;        # Contenido del formulario de invocacion.

my $RES;

# Para facilitar el uso mediante AJAX.
print "Content-type: text/plain\n\n";

&glib_cgi_04::new();
&glib_cgi_04::set_formvar('video', \%FORM);
&glib_cgi_04::set_formvar('t1', \%FORM);
&glib_cgi_04::set_formvar('t2', \%FORM);
&glib_cgi_04::set_formvar('prontus_id', \%FORM);

# Path conf y load config de prontus
my $path_conf = "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
$path_conf = &lib_prontus::ajusta_pathconf($path_conf);
&lib_prontus::load_config($path_conf);  # Prontus 6.0
$path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

$RES = &cutVideo();

print $RES;

exit;

# -------------------------------------------------------------------#
# Inicia la transcodificacion.
sub cutVideo {
  my ($cmd,$res,$destino);
  my $video = $FORM{'video'};
  my $tiempo1 = $FORM{'t1'};
  my $tiempo2 = $FORM{'t2'};
  my $prontus_id = $FORM{'prontus_id'};
  if ($video =~ /^\//) {
    $video = $prontus_varglb::DIR_SERVER . $video;
  }else{
    $video = $prontus_varglb::DIR_SERVER .'/'. $video;
  };

  $tiempo1 =~ s/[^0-9\.]//g;

  $tiempo2 =~ s/[^0-9\.]//g;

  # print $tiempo ."\n";
  $destino = $video;
  $destino =~ s/(.+)\.(\w+)/$1\.cut\.$2/;
  unlink $destino;

  # $cmd = "ffmpeg -vcodec copy -acodec copy -t $tiempo -i $video $destino";
  my $duracion = $tiempo2 - $tiempo1;
  $cmd = "$prontus_varglb::DIR_FFMPEG/ffmpeg -ss $tiempo1 -t $duracion -i $video -y -vcodec copy -acodec copy $destino";
  print STDERR "******** NUEVO VIDEO CUT\n$cmd \n";
  # print "$cmd \n";
  # return 'OK';

  $res = `$cmd 2>&1`;
  print STDERR "result from ffmpeg realizando video cut\nres[$res][$?][$!]\n";
  my $msg_err_usr = 'Error al realizar corte del video, el archivo resultante no pudo ser generado. Los detalles fueron agregados al error log interno de Prontus.';

  #$cmd = "$prontus_varglb::DIR_SERVER/cgi-cpn/xcoding/qtfaststart.py $destino";
  $cmd = "$Bin/qtfaststart.cgi $destino";
  $res = qx/$cmd 2>&1/;
  # print STDERR "\n\n$res"; # para debug
  print STDERR ("Falló Ajuste de Mp4 [$!][$res].") if ($? != 0);
  # Elimina el archivo de origen si es que el destino se genero ok

  if (-s $destino > 0) {
    unlink $video;
    rename $destino,$video;
    return 'OK';
  }else{
    print STDERR "$msg_err_usr\nError: el archivo resultante [$destino] no pudo ser generado por ffmpeg\n";
    return $msg_err_usr;
  };
}; # cutVideo


