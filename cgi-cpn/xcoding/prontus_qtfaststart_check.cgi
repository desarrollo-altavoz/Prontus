#!/usr/bin/perl

# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Chequear archivos mp4 para que esten listos para ser vistos via web.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Llama a qtfaststart.cgi para que haga el ajuste.
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cgi, usando metodo GET o POST. Los parametros son:
# video  - Path relativo al video a transcodificar.
#
# Retorna 'OK' o 'NOK;
#
# Ejemplo:
#
# /cgi-cpn/xcoding/prontus_qtfaststart_check.cgi?video=/prontus_proto/site/artic/20100531/mmedia/multimedia_video120100531182139.mp4
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# Basado en qtfaststart.cgi portado a perl por CVI
# ---------------------------------------------------------------
#    Quicktime/MP4 Fast Start
#    ------------------------
#    Enable streaming and pseudo-streaming of Quicktime and MP4 files by
#    moving metadata and offset information to the front of the file.
#
#    This program is based on qt-faststart.c from the ffmpeg project, which is
#    released into the public domain, as well as ISO 14496-12:2005 (the official
#    spec for MP4), which can be obtained from the ISO or found online.
#
#    The goals of this project are to run anywhere without compilation (in
#    particular, many Windows and Mac OS X users have trouble getting
#    qt-faststart.c compiled), to run about as fast as the C version, to be more
#    user friendly, and to use less actual lines of code doing so.
#
#    Features
#    --------
#
#        * Works everywhere Python can be installed
#        * Handles both 32-bit (stco) and 64-bit (co64) atoms
#        * Handles any file where the mdat atom is before the moov atom
#        * Preserves the order of other atoms
#        * Replace the original file (if given no output file)
#
#    Usage
#    -----
#    Execute:
#        qtfaststart.pl 'the_file'
#
#    History
#    -------
#    1.0.0 - 2011-12-06 - CVI - Primera version
# ---------------------------------------------------------------
# 1.0.0 - 08/01/2013 - EAG - Primera version.
# 1.0.1 - 19/02/2013 - EAG - Se corrige bug al buscar atom, atom size == 0, provocaba bucle infinito.
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

use strict;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use lib_prontus;

my %INDICES;
my %STCOs;
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

    # User check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    my $infile = $FORM{'video'};
    if ($infile !~ /\.mp4$/i) {
        &glib_html_02::print_json_result(0, "Error: El video no es mp4.", 'exit=1,ctype=1');
    };
    if ($infile =~ /^\//) {
        $infile = $prontus_varglb::DIR_SERVER . $infile;
    } else {
        $infile = $prontus_varglb::DIR_SERVER .'/'. $infile;
    };

    if($infile eq '' || !(-f $infile)) {
        &glib_html_02::print_json_result(0, 'Debe especificar el archivo a procesar', 'exit=1,ctype=1');
    };

    &checkStatus($infile);

    my $result = &checkMp4($infile);
    if ($result) {
        print STDERR "[$infile] no necesita correccion\n";
        &glib_html_02::print_json_result(1, 'OK', 'exit=1,ctype=1');
    } else {
        print STDERR "[$infile] necesita correccion\n";
        &startFix($infile);
    }
}
# -------------------------------------------------------------------#
# Inicia qtfaststart.cgi.
sub startFix{
    my ($origen) = @_;
    # Verifica que no haya otro proceso identico en ejecucion.
    my $res = qx/ps auxww |grep 'qtfaststart.cgi $origen'|grep -v grep/;
    print STDERR "Execution test = [$res][ps auxww |grep 'qtfaststart.cgi $origen'|grep -v grep]\n";
    if ($res ne '') {
        &glib_html_02::print_json_result(1, "Busy", 'exit=1,ctype=1');
    };

    use FindBin '$Bin';
    my $pathnice = &lib_prontus::get_path_nice();
    my $cmd = "$pathnice /usr/bin/perl $Bin/qtfaststart.cgi $origen";

    print STDERR "gatillando[$cmd]\n";
    $res = `$cmd 2>/dev/null 1>/dev/null &`;
    &glib_html_02::print_json_result(1, "FIX", 'exit=1,ctype=1');
}; # startFix

# -------------------------------------------------------------------#
# Verifica si se esta corrigiendo el archivo mp4
sub checkStatus {
    my ($origen) = @_;
    my $res = qx/ps auxww |grep 'qtfaststart.cgi $origen'|grep -v grep/;
    #print STDERR "Execution test = [$res][ps auxww |grep 'qtfaststart.cgi $origen'|grep -v grep]\n";
    if ($res ne '') {
        &glib_html_02::print_json_result(1, "Busy", 'exit=1,ctype=1');
    };

    # Ve si el destino esta en el XML
    if ($origen =~ /(.+)\/(\d{8})\/mmedia\/(multimedia_video.+?(\d{6}))\.(\w+)$/) {
        my $path = $1 .'/'. $2 .'/xml/'. $2 . $4 . '.xml';
        my $filename = $3;
        my $extension = $5;
        #~ print STDERR "[$path][$filename][$extension]\n";
        my $buffer = &glib_fildir_02::read_file($path);
        if ($buffer =~ /$filename\.mp4/s) {
            return;
        };
    };
    &glib_html_02::print_json_result(0, "Error: Archivo mp4 no se encuentra en XML de articulo", 'exit=1,ctype=1');
}; # checkStatus

# ------------------------------------------------
sub read_atom {
#    Read an atom and return a tuple of (size, type) where size is the size
#    in bytes (including the 8 bytes already read) and type is a "fourcc"
#    like "ftyp" or "moov".

    my ($datastream) = @_;
    read($datastream, my $data, 8);
    return unpack("N a4", $data);
}

# ------------------------------------------------
sub get_index {
#    Return an index of top level atoms, their absolute byte-position in the
#    file and their size in a list:
#
#    %index = {"ftyp" => [0, 24],"moov" => [25, 2658], "free" => [2683, 8],...}
#
#    The tuple elements will be in the order that they appear in the file.

    my ($datastream, $toplevel) = @_;
    while(!eof($datastream)) {
        my $skip = 8;
        my ($atom_size, $atom_type) = &read_atom($datastream);
        if($atom_size == 1){
            read($datastream, my $data, 8);
            $atom_size = unpack("Q", $data);
            $skip = 16;
        }
        if($atom_size == 0){
            last;
        }
        my $atom_pos = tell($datastream) - $skip;
        if($toplevel) {
            $INDICES{$atom_type} = [$atom_pos, $atom_size];
        }
        # The stco|co64 atoms may be inside this atoms
        if($atom_type =~ /(moov|trak|mdia|minf|stbl)/) {
            &get_index($datastream, 0);
            return;
        }
        if($atom_type =~ /(stco|co64)/) {
            $STCOs{$atom_pos} = [$atom_type, $atom_pos, $atom_size];
        }
        seek $datastream, ($atom_pos + $atom_size), 0;
    }

    # Make sure the atoms we need exist
    if($toplevel && ( !($INDICES{"moov"}) || !($INDICES{"mdat"}))) {
        print STDERR "No existe por lo menos uno de los atoms obligatorios";
        exit;
    }
}
# ------------------------------------------------
sub checkMp4 {
#    Convert a Quicktime/MP4 file for streaming by moving the metadata to
#    the front of the file. This method writes a new file.
    my ($infilename) = @_;

    # Open the inputfile in binary mode
    my $datastream;
    open($datastream, "<", $infilename)  or die("No se pudo abrir el archivo: $infilename");
    binmode $datastream;

    # Get the top level atom index
    &get_index($datastream, 1);

    my %indices = %INDICES;
    my $mdat_pos = 999999999;
    my $free_size = 0;

    my ($moov_pos, $moov_size);

    # Make sure moov occurs AFTER mdat, otherwise no need to run!
    foreach my $atom (sort keys %indices) {
        my $pos = $indices{$atom}[0];
        my $size = $indices{$atom}[1];
        # The atoms are guaranteed to exist from get_index above!
        if ($atom eq "moov") {
            $moov_pos = $pos;
            $moov_size = $size;
        } elsif ($atom eq "mdat") {
            $mdat_pos = $pos;
        } elsif ($atom eq "free" && $pos < $mdat_pos) {
            # This free atom is before the mdat!
            $free_size += $size;
            #warn("Removing free atom at $pos ($size bytes)");
        }
    }

    # Offset to shift positions
    my $offset = $moov_size - $free_size;

    if( $moov_pos < $mdat_pos) {
        # moov appears to be in the proper place, don't shift by moov size
        $offset -= $moov_size;
        unless($free_size) {
            # No free atoms and moov is correct, we are done!
            #warn ("This file appears to already be setup for streaming!");
            return 1;
        }
        return 0;
    } else {
        return 0;
    }
}