#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# SCRIPT.
# -----------
# prontus_procesar_videos.pl
# ---------------------------------------------------------------
# UBICACION.
# -----------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Ejecuta la transcodificación para todos los videos de un prontus
# de la misma forma que se hace desde un FID
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------
# Usa las cgis de transcodificacion de prontus
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# A traves de linea de comando, ej:
# Parametros:
# 1: nombre del prontus a procesar
# 2: identificador del fid a procesar
# 3: marca o marcas del video, si es mas de una se separan con coma,
#  ej: multimedia_video1,multimedia_video2
#
# Ejemplo de uso:
# perl prontus_procesar_videos.pl mi_prontus_id fid_noticia multimedia_video1,multimedia_video2
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# ---------------------------------------------------------------
# Tablas.
# ------------------------
# No utiliza.
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 06/12/2016 - EAG - Primera Version
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    use FindBin '$Bin';
    unshift(@INC,$Bin); # Para dejar disponibles las librerias
    $pathLibsProntus = $Bin;
    $pathLibsProntus =~ s/\/[^\/]+\/?$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

use strict;
use glib_hrfec_02;
use lib_prontus;
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);
use Data::Dumper;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my $separator_orig = '   ';
my $separator = '';
my $COUNTER = 0;

my @BUSCAR;
my $FID = '';
my $PRONTUS_ID = '';
my $TS = '';
my $input;

main:{
    if (scalar @ARGV < 2) {
        print "Parámetros insuficientes. Modo de uso:\n";
        print "perl prontus_procesar_videos.pl <prontus_id> <fid_id o ts articulo> <multimedia_video1,multimedia_video2,..,multimedia_videoN>\n";
        exit;
    }
    $PRONTUS_ID = $ARGV[0];

    if (! &lib_prontus::valida_prontus($PRONTUS_ID)) {
        print "El parámetro 'prontus_id' no es válido.\n";
        exit;
    }

    if ($ARGV[1] eq '' || ($ARGV[1] !~ /^fid\_/ && $ARGV[1] !~ /^\d{14}$/)) {
        print "El segundo parámetro no es válido.\nDebe ser el nombre de un fid o el ts de un artículo.\n";
        exit;
    }

    if ($ARGV[1] =~ /^\d{14}$/) {
        $TS = $ARGV[1];
    } elsif ($ARGV[1] =~ /^fid\_/) {
        $FID = $ARGV[1];
    }

    if ($ARGV[2] eq '') {
        @BUSCAR = ('multimedia_video1','multimedia_video999');
    } else {
        @BUSCAR = split(',', $ARGV[2]);
    }

    $input = $Bin;
    $input =~ s/\/[^\/]+\/?$//;
    $input =~ s/\/[^\/]+\/?$//;
    $input .= "/$PRONTUS_ID/site/artic/";

    print STDERR "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Inicio Proceso [$PRONTUS_ID][$TS][$FID]\n";

    if ($TS ne '') {
        $input .= substr($TS, 0, 8). "/xml/";
        &procesa_file("$TS.xml", $input);
    } else {
        &procesa_dir($input);
    }
    print STDERR 'Se procesaron ' . $COUNTER .  " videos \n" if $COUNTER;
    print STDERR "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Fin Proceso [$PRONTUS_ID][$TS][$FID]\n";
};

#-----------------------------------------------------------------------#
sub procesa_dir {
    my($input) = $_[0];

    unless(-d $input) {
        die "El directorio $input no existe.";
    };
    $input = $input . '/' unless ($input =~ /\/$/);

    my @entries = &lee_dir($input);
    foreach my $k (@entries) {
        next if($k eq '.' || $k eq '..');
        if(-f $input . $k) {
            &procesa_file($k, $input);

        } elsif(-d $input . $k) {
            $separator = $separator . $separator_orig;
            &procesa_dir($input . $k);
        };
    };
    $separator =~ s/$separator_orig$//;

};

#-----------------------------------------------------------------------#
sub procesa_file {
    my($filename, $path) = ($_[0], $_[1]);
    my $filepath = $path . $filename;
    my $titular;
    my $ts;
    if ($filename !~ /^(\d{14})\.xml/isg) {
        return;
    }
    $ts = $1;

    if (-f $filepath) {
        my $file = &read_file($filepath);
        if ($FID ne ''  && $file !~ /$FID/is) {
            return;
        }
        # print STDERR "XML valido $filepath\n";
        my %data;
        my $cmd = '';
        my $result = '';
        my $result2 = '';
        my $video = '';
        foreach my $campo (@BUSCAR) {
            my $found = '';
            if ($file =~ /<$campo>.*?<\!\[CDATA\[(.*?)\]\]>.*?<\/$campo>/is) {
                $found = $1;
                $found =~ s/[\n\r]//g;
            };
            if ($file =~ /<$campo>(.*?)<\/$campo>/is) {
                $found = $1;
                $found =~ s/[\n\r]//g;
            };
            if ($file =~ /<_txt_titular>.*?<!\[CDATA\[(.*?)\]\]>.*?<\/_txt_titular>/is) {
                $titular = $1;
            }
            if ($found ne '') {
                print STDERR "Procesar [$ts][$titular][$campo][$found]\n";
                $video =  "/$PRONTUS_ID/site/mm/". substr($ts ,0, 8) ."/mmedia/$found";
                if ($found =~ /\.mp4$/) { # si es mp4 revisamos los atoms
                    $cmd = "perl $Bin/prontus_qtfaststart_check.cgi $video $PRONTUS_ID";
                } else { # si no es mp4 hay que transcodificarlo
                    $cmd = "perl $Bin/prontus_videoxcodestatus.cgi $video $PRONTUS_ID";
                }
                $result = `$cmd`;
                #~ print STDERR  $result;
                if ($result =~ /(RECODE|XCODE|Xcoding|none|busy)/) {
                    my $versiones = 0;
                    # si es XCODE significa que faltan las versiones del video
                    $versiones = 1 if ($result =~ /XCODE/);
                    # si es none, significa que no es mp4, que no hay proceso corriendo y hay que transcodificar
                    $versiones = 0 if ($result =~ /none/);
                    $cmd = "perl $Bin/prontus_videoxcode.cgi $video $PRONTUS_ID $versiones";
                    #~ print STDERR "$cmd\n";
                    print STDERR "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Transcodificar $video\n";

                    # si no se está procesando se lanza uno nuevo
                    $result = `$cmd` if ($result !~ /Xcoding/ && $result !~ /busy/);
                    #~ print STDERR $result;
                    do {
                        sleep(10);
                        $cmd = "perl $Bin/prontus_videoxcodestatus.cgi $video $PRONTUS_ID";
                        $result = `$cmd`;
                    } while ($result =~ /busy/);
                    print STDERR "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Terminado $video\n";
                    $COUNTER++;
                } elsif ($result =~ /FIX/) {
                    print STDERR "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Corregir $video\n";
                    do {
                        sleep(10);
                        $cmd = "perl $Bin/prontus_qtfaststart_check.cgi $video $PRONTUS_ID";
                        $result = `$cmd`;
                        #~ print STDERR $result;
                    } while ($result =~ /busy/);
                    print STDERR "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Terminado $video\n";
                    $COUNTER++;
                }
            }
        }
    };
};

#-----------------------------------------------------------------------#
# Funciones de apoyo, tomadas de la glib_fildir_02.pm
#-----------------------------------------------------------------------#
sub lee_dir {
# Lee un directorio y entrega la lista ordenada de entries en bruto.

# Param. de entrada :
# 0) Path real del directorio.

# Retorna : Arreglo ordenado de entradas en bruto del directorio.

  my($eldir) = $_[0];
  # Abre directorio.
  opendir(DIR, $eldir) || die "Can't opendir" . $eldir . $!;
  my @entries = readdir(DIR);
  closedir DIR;
  # Ordena entries alfabeticamente.
  @entries = sort @entries;
  return @entries;
};
#-------------------------------------------------------------------------#
sub read_file {
# Lee un archivo por completo.

# Param. de entrada :
# 0) Path real del archivo.

# Retorna : El texto leido | '' en caso que el archivo no exista.

  my($archivo) = $_[0];
  my($size) = (-s $archivo);
  my($buffer) = '';

  if (-e $archivo) {
    open (ARCHIVO,"<$archivo")
      || die "Fail Open file $archivo \n $!\n";
    binmode ARCHIVO;
    read ARCHIVO,$buffer,$size;
    close ARCHIVO;
  };

  return $buffer;

};
#------------------------------------------------------------------------#
sub write_file {
# Escribe un archivo.

# Param. de entrada :
# 0) Path real del archivo.
# 1) Texto a escribir.

  my($archivo,$buffer) = ($_[0],$_[1]);

  open (ARCHIVO,">$archivo")
    || die "Content-Type: text/plain\n\n Fail Open file $archivo \n $!\n";
  binmode ARCHIVO;
  print ARCHIVO $buffer; #Escribe buffer completo
  close ARCHIVO;

};
# -------------------------END SCRIPT----------------------
