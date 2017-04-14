#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# SCRIPT
# ---------------------------------------------------------------
# prontus_garbage_collector.pl
#
# ---------------------------------------------------------------
# PROPOSITO
# ---------------------------------------------------------------
# Borra los archivos muy antiguos de un directorio
# primero elimina los archivos mas antiguos que el limite indicado
# si aun hay mas archivos que el maximo admitido, se eliminan los
# mas antiguos hasta que el maximo no se sobrepase
#
# ---------------------------------------------------------------
# LLAMADAS A OTROS PROGRAMAS
# ---------------------------------------------------------------
# Ninguno
#
# ---------------------------------------------------------------
# LIBRERIAS NECESARIAS
# ---------------------------------------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS
# ---------------------------------------------------------------
# Como script, requiere como parametros:
# 1: carpeta del cache a revisar
# 2: tiempo de expiracion
# 3: numero maximo de archivos en la carpeta
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA
# ---------------------------------------------------------------
# Ninguno
#
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA
# ---------------------------------------------------------------
# Ninguno
# ---------------------------------------------------------------
# BASES DE DATOS
# ---------------------------------------------------------------
# No utiliza
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES
# ---------------------------------------------------------------
# 1.0.0 - 13/03/2017 - EAG - Primera Version.
#
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION
# ---------------------------------------------------------------
BEGIN {
    use FindBin '$Bin';
    unshift(@INC,$Bin);
    my $pathLibsProntus = $Bin;
};

use strict;
use glib_fildir_02;
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

my $DEBUG = 0;
my $DATADIR = "";
my $NOMODIFY_TIME = 1800; # segundos de antiguedad
my $MAX_FILES = 2000; # maximo de archivos en una carpeta
# ----------------------------------------------------------------------------- #
main: {
    if (&myself_running() > 1) {
        print STDERR " Hay otro proceso corriendo: $0\n" if $DEBUG;
        exit;
    };

    my $mtime;
    my $file = '';
    my @files;
    my @all_files;
    my $time = time;
    my $file_age = 0;
    my $total_files;
    my $erase_files;
    my $counter = 0;

    $DATADIR = $ARGV[0];
    # se valida el directorio
    if (!(-d $DATADIR)) {
        print STDERR "[$DATADIR] no existe\n";
        exit;
    }

    if ($DATADIR =~ /site|plantillas|fid/) {
        print STDERR "[$DATADIR] no es valido para borrar\n";
        exit;
    }
    $NOMODIFY_TIME = $ARGV[1];
    # si no viene vacio usamos el valor
    if ($ARGV[1] =~ /^\d+$/ ) {
        $NOMODIFY_TIME = $ARGV[1];
    }
    # si no viene vacio usamos el valor
    if ($ARGV[2] =~ /^\d+$/ ) {
        $MAX_FILES = $ARGV[2];
    }

    if (opendir(DIR, $DATADIR)) {
        @files = readdir(DIR);
        closedir DIR;
    } else {
        print STDERR "[$DATADIR] no se puede leer\n";
        exit;
    };

    foreach $file (@files) {
        if ($file eq '.' or $file eq '..') { next;};
        # tipos de archivo que no se borraran
        if ($file =~ /\.(cgi|pl|pm|cfg|xml|js|sst)$/) { next;};
        # archivos que no se borran
        if ($file =~ /(robots\.txt|index\.html)$/) { next;};
        $mtime = (stat("$DATADIR/$file"))[9];

        $file_age = 0;
        $file_age = $time - $mtime;
        print localtime($mtime) . "|$file\n" if $DEBUG;
        # se borran todos los archivos que tienen mas de $NOMODIFY_TIME
        # segundos de antiguedad
        if ($file_age > $NOMODIFY_TIME ) {
            unlink("$DATADIR/$file");
            $counter++;
            next;
        }
        # si no se borran se guardan en un arreglo para borrar si se sobrepasa el limite de archivos
        push(@all_files, {mtime => $mtime, file_age => $file_age, filename => $file});
    }

    $total_files = scalar @all_files;

    print STDERR "Total borrado: $counter\n" if $DEBUG;
    print STDERR "Total no borrado: ". $total_files . "\n" if $DEBUG;

    # si hay muchos archivos se borran los mas antiguos
    if ($total_files >= $MAX_FILES) {
        $erase_files = $total_files - $MAX_FILES;
        print STDERR "Borrado adicional $erase_files de $total_files\n" if $DEBUG;
        @all_files = sort { $a->{'mtime'} cmp $b->{'mtime'} } @all_files;

        for (my $i = 0; $i < $erase_files; $i++) {
            # tipos de archivo que no se borraran
            if ($all_files[$i]->{'filename'} =~ /\.(cgi|pl|pm|cfg|xml)$/) { next;};
            print STDERR "borrar: $DATADIR/$all_files[$i]->{'filename'}\n" if $DEBUG;
            unlink("$DATADIR/$all_files[$i]->{'filename'}");
            $counter++;
        }
        print STDERR "Total borrado: $counter\n" if $DEBUG;
        print STDERR "Total no borrado: ". ($total_files - $erase_files) . "\n" if $DEBUG;
    }
};
# ##################################
# Funciones
# ----------------------------------------------------------------------------- #
# Detecta cuantas copias de este script estan corriendo.
sub myself_running {
    my(@result) = qx/ps axww | grep $0 | grep -v ' grep ' | grep -v 'nice' | grep -v 'editor' | grep -v 'sh -c' | grep -v execIfMaster | grep -v 'tail'/; # wc -l
    my($line,$res);
    $res = 0;
    foreach $line (@result) {
        #print "line = [$line] [$0]\n";
        if ($line =~ /$0/) {
            $res++;
        };
    };
    return $res;
}; # myself_running
