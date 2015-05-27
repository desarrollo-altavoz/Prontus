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
# Obtiene una imagen (snapshot) de un video.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Lee el video y extrae el snapshot de el. El archivo de destino se llama igual que el video, pero con extension .jpg
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cgi, usando metodo GET o POST. Los parametros son:
# video  - Path relativo al video a transcodificar.
# t - Tiempo en segundos (con decimales) de donde sacar el snapshot.
# w - ancho de la pelicula final.
# h - alto de la pelicula final.
#
# Retorna 'OK' o 'Error: <mensaje de error>';
#
# Ejemplo:
#
# /cgi-cpn/prontus_videogetsnapshot.cgi?video=prontus_proto/site/artic/20100531/mmedia/tele1.flv&w=320&h=240&t=5.2
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------

# 1.0.0 - 31/05/2010 - Primera version.
# 1.0.1 - 03/10/2014 - EAG - Se agrega use utf8
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
# ------------------------
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_cgi_04;
use lib_prontus;
use glib_html_02;
use strict;
use lib_xcoding;
use utf8;

my %FORM;        # Contenido del formulario de invocacion.

main: {
    &glib_cgi_04::new();
    &glib_cgi_04::set_formvar('video', \%FORM);
    &glib_cgi_04::set_formvar('t', \%FORM);
    &glib_cgi_04::set_formvar('prontus_id', \%FORM);


    # Valida datos de entrada
    my $msg_err;
    $msg_err = "Parámetro [video] no es válido [$FORM{'video'}]" if ((!-f "$prontus_varglb::DIR_SERVER$FORM{'video'}") || (!-s "$prontus_varglb::DIR_SERVER$FORM{'video'}"));
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

    my $res = &do_snapshots();

    # Falta convertir JS para que recepcione json.
    # &glib_html_02::print_json_result($status, $msg, 'exit=1,ctype=1');

    # Para facilitar el uso mediante AJAX.
    print "Content-type: text/plain\n\n";
    print $res;

    exit;
};

# -------------------------------------------------------------------#
# Inicia la transcodificacion.
sub do_snapshots {
  my $res;
  my $video = $FORM{'video'};
  my $tiempo = $FORM{'t'};
  my $prontus_id = $FORM{'prontus_id'};

  if ($video =~ /^\//) {
    $video = $prontus_varglb::DIR_SERVER . $video;
  } else {
    $video = $prontus_varglb::DIR_SERVER .'/'. $video;
  };

  $res = &make_snapshot($video, $tiempo, $prontus_id);

  return $res if ($res ne 'OK');

  my $path_search = $video;
  $path_search =~ s/(\.\w+)$/*$1/is;
  my @files_multimedia = glob("$path_search");
  foreach my $mediafile (@files_multimedia) {
      next if ($video eq $mediafile);
      my $resp = &make_snapshot($mediafile, $tiempo, $prontus_id, 1);
      return $resp if ($res ne 'OK');
  };

  return 'OK';

}; # getSnapshot


sub make_snapshot {
  my $video = $_[0];
  my $tiempo = $_[1];
  my $prontus_id = $_[2];
  my $no_copy = $_[3];
  my ($cmd, $res);
  my $destino = $video;

  $tiempo =~ s/\,/\./;
  $tiempo =~ s/[^0-9\.]//g;

  $destino =~ s/(.+)\.\w+/$1\.jpg/;
  $cmd = "$prontus_varglb::DIR_FFMPEG/ffmpeg -ss $tiempo -i $video -y -vframes 1 -f image2 $destino";
  print STDERR "Snapshot cmd[$cmd]\n";
  $res = `$cmd 2>&1`;

  my $msg_err_usr = 'Error al generar Snapshot, no se pudo generar la imagen. Los detalles fueron agregados al error log interno de Prontus.';

  if (-f $destino) {
    my $nom_img;
    if ($destino =~ /\/([^\/]+\.jpg)$/) {
        $nom_img = $1;
        if (!$no_copy) {
          print STDERR "copy[$destino][$prontus_varglb::DIR_SERVER/$prontus_id/cpan/procs/imgedit/$nom_img] \n";
          &File::Copy::copy($destino, "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/procs/imgedit/$nom_img");
        };
        return 'OK';
    } else {
        print STDERR "$msg_err_usr\nError: la imagen resultante de ffmpeg [$destino] no es .jpg\n";
        return $msg_err_usr;
    };
  } else {
      print STDERR "$msg_err_usr\nError: la imagen resultante [$destino] no pudo ser generada por ffmpeg\n";
      return $msg_err_usr;
  };
};
