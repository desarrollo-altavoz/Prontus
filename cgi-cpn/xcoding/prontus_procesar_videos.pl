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

use Term::ANSIColor;
use strict;
use glib_hrfec_02;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my $separator_orig = '   ';
my $separator = '';
my $counter = 0;
my $rule = '';

for(my $i = 0 ; $i < 80; $i++) {
    $rule = $rule . '-';
};

my @buscar;
my $FID = '';
my $PRONTUS_ID = '';
my $input = $Bin;

main:{
    $PRONTUS_ID = $ARGV[0];
    $FID = $ARGV[1];
    print join('|', @ARGV);
    if ($ARGV[2] eq '') {
        @buscar = ('multimedia_video1','multimedia_video999');
    } else {
        @buscar = split(',', $ARGV[2]);
    }

    $input = $Bin;
    $input =~ s/\/[^\/]+\/?$//;
    $input =~ s/\/[^\/]+\/?$//;
    $input .= "/$PRONTUS_ID/site/artic/";
    printf color('blue') . $rule . color('reset') . "\n";

    print "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Inicio Proceso\n";

    &procesa_dir($input);
    printf color('blue') . 'Se encontraron ' . $counter .  ' archivos ' . color('reset') . "\n";
    print "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Fin Proceso\n";
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
    if ($filename !~ /(\d+?)\.xml/isg) {
        return;
    }
    $ts = $1;

    if (-f $filepath) {
        my $file = &read_file($filepath);
        if ($FID ne ''  && $file !~ /$FID/is) {
            return;
        }
        my %data;
        my $cmd = '';
        my $result = '';
        my $result2 = '';
        my $video = '';
        foreach my $campo (@buscar) {
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
                printf color('red') . $path . $filename . color('reset') . " Encontrado: ->\t [$titular] \t[$campo] ->\t[$found] \n";
                $video =  "/$PRONTUS_ID/site/mm/". substr($ts ,0, 8) ."/mmedia/$found";
                $cmd = "perl $Bin/prontus_qtfaststart_check.cgi $video $PRONTUS_ID\n";
                $result = `$cmd`;
                #~ print $result;
                if ($result =~ /(RECODE|XCODE|Xcoding)/) {
                    my $versiones = 0;
                    $versiones = 1 if ($result =~ /XCODE/);
                    $cmd = "perl $Bin/prontus_videoxcode.cgi $video $PRONTUS_ID $versiones";
                    #~ print "$cmd\n";
                    print "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Transcodificar $video\n";
                    $result = `$cmd`;
                    #~ print $result;
                    do {
                        sleep(10);
                        $cmd = "perl $Bin/prontus_videoxcodestatus.cgi $video $PRONTUS_ID\n";
                        $result = `$cmd`;
                    } while ($result =~ /busy/);
                    print "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Terminado $video\n";
                } elsif ($result =~ /FIX/) {
                    print "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Corregir $video\n";
                    do {
                        sleep(10);
                        $cmd = "perl $Bin/prontus_qtfaststart_check.cgi $video $PRONTUS_ID\n";
                        $result = `$cmd`;
                    } while ($result =~ /busy/);
                    print "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] Terminado $video\n";
                }
                $counter++;
            }
        }
    };
};

#-----------------------------------------------------------------------#
# Funciones de apoyo, tomadas de la glin_fildir_02.pm
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
