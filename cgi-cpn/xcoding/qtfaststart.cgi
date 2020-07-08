#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
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
#    1.0.1 - 19/02/2013 - EAG - Se corrige bug al buscar atom, atom size == 0, provocaba bucle infinito.
#    1.0.2 - 30/04/2013 - CVI - Se captura excepción al intentar hacer un unpack Q, ya que se caía.
#    1.1.0 - 16/05/2013 - EAG - Se corrige bug al buscar atoms, si habian atoms duplicados se tomaba en cuenta solo el ultimo, lo que provocaba videos corruptos.
#    1.2.0 - 22/05/2014 - EAG - Se corrige bug en find_atoms, si el atom tenia tamaño 0 el script se pegaba
#    1.3.0 - 04/03/2015 - EAG - Se corrige "endianness" al hacer unpack Q

use strict;

use File::Copy;
use File::Temp qw/tempfile/;

my $VERSION = "1.0";
my $CHUNK_SIZE = 8192;

my @INDICES;
my @STCOs;
my $FILE;
main: {
    my $infile = $ARGV[0];
    $FILE = $infile;
    # my $infile = '/var/www/prontus_development/web/cgi-cpn/xcoding/multimedia_video120111130160451_a.mp4';
    if($infile eq '' || !(-f $infile)) {
        die('Debe especificar el archivo a procesar');
    };

    my ($fh, $outfile) = tempfile();
    close($fh);
    # my $outfile = '/var/www/prontus_development/web/cgi-cpn/xcoding/new-by-perl.mp4';

    &process($infile, $outfile);

    # Move temp file to replace original
    unlink($infile) if(-f $infile);
    move($outfile, $infile);

    # Fixing: En algunos servers queda como 600
    chmod 0644, "$infile";

    warn("Proceso terminado ok.");
}

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
    my %index;
    my $last_pos = 0;
    while(!eof($datastream)) {
        $last_pos = tell($datastream);
        my $skip = 8;
        my ($atom_size, $atom_type) = &read_atom($datastream);
        if($atom_size == 1){
            read($datastream, my $data, 8);
            $atom_size = unpack("Q>", $data);
            $skip = 16;
        }
        my $atom_pos = tell($datastream) - $skip;
        if($toplevel) {
            $index{$atom_type} =  1;
            push(@INDICES, [$atom_type, $atom_pos, $atom_size]);
        }

        if($atom_size == 0){
            last;
        }
        if (!(-s $FILE)) {
            warn("Archivo eliminado durante ejecucion: $FILE");
            exit;
        }
        seek $datastream, ($atom_pos + $atom_size), 0;
        if ($last_pos == tell($datastream)){
            #~ warn("Get_index: el cursor del archivo dejo de avanzar, hay que terminar el ciclo.");
            last;
        }
    }

    # Make sure the atoms we need exist
    if($toplevel && ( !($index{"moov"}) || !($index{"mdat"}))) {
        warn("No existe por lo menos uno de los atoms obligatorios");
        exit;
    }
}
# ------------------------------------------------
sub find_atoms {
#    Return an index of srco o co64 atoms
#
#    The tuple elements will be in the order that they appear in the file.
    my ($size, $datastream) = @_;
    my $stop = tell($datastream) + $size;
    my $last_pos = 0;
    while (tell($datastream) < $stop) {
        $last_pos = tell($datastream);
        if (!(-s $FILE)) {
            warn("Archivo eliminado durante ejecucion: $FILE");
            exit;
        }
        my ($atom_size, $atom_type) = &read_atom($datastream);
        my $atom_pos = tell($datastream) - 8;

        # The stco|co64 atoms may be inside this atoms
        if($atom_type =~ /(trak|mdia|minf|stbl)/) {
            &find_atoms($atom_size, $datastream);
        } elsif ($atom_type =~ /(stco|co64)/) {
            push(@STCOs, [$atom_type, $atom_pos, $atom_size]);
            seek $datastream, ($atom_size - 8), 1;
        } else {
            seek $datastream, ($atom_size - 8), 1;
        }
        #~ print STDERR "ini: $last_pos - fin: ".tell($datastream)." < $stop\n";
        if ($last_pos == tell($datastream)){
            #~ warn("Find_atoms: el cursor del archivo dejo de avanzar, hay que terminar el ciclo.");
            last;
        }
        if ($atom_size == 0) {
            last;
        }
    }
}

# ------------------------------------------------
sub fix_moov {
#    Fix the stco or co64 atoms, with the offset variable
#    Besides, writes the new complete moov atom into the outputfile
#    It assume that the input datastream is positioned at beginning of the moov atom

    my ($size, $datastream, $outfile, $offset) = @_;
    my $buffer;
    # Ignore moov identifier and size, start reading children
    my $stop = tell($datastream) + $size;
    foreach my $stco (@STCOs) {
        my $atom_type = @{$stco}[0];
        my $atom_pos = @{$stco}[1];
        my $atom_size = @{$stco}[2];
        # Write between last atom and this atom
        if(tell($datastream) < $atom_pos) {
            my $size = $atom_pos + 12 - tell($datastream);
            read($datastream, $buffer, $size);
            print $outfile $buffer;
        }

        # Patch atom
        # Read either 32-bit or 64-bit offsets
        my ($ctype, $csize);
        if($atom_type eq "stco") {
            ($ctype, $csize) = ("N", 4);
        } else {
            ($ctype, $csize) = ("Q", 8);
        }
        # Get number of entries
        seek($datastream, $atom_pos + 12, 0);
        read($datastream, my $moovtmp, 4);
        print $outfile $moovtmp;
        my ($entry_count) = unpack("N", $moovtmp);

        # Read entries
        read($datastream, my $data_moov2, ($csize * $entry_count));
        my @entries = unpack("".($ctype x $entry_count), $data_moov2);

        # Patch and write entries
        foreach my $entry (@entries){
            print $outfile pack($ctype, $entry + $offset);
        }
    }
    # Write the remaining data to the end of the atom
    if(tell($datastream) < $stop) {
        my $size = $stop - tell($datastream);
        read($datastream, $buffer, $size);
        print $outfile $buffer;
    }
}


# ------------------------------------------------
sub process {
#    Convert a Quicktime/MP4 file for streaming by moving the metadata to
#    the front of the file. This method writes a new file.
    my ($infilename, $outfilename) = @_;

    # Open the inputfile in binary mode
    my $datastream;
    open($datastream, "<", $infilename)  or die("No se pudo abrir el archivo: $infilename");
    binmode $datastream;

    # Get the top level atom index
    eval { &get_index($datastream, 1) };
    if ($@) {
        print STDERR "Error al hacer get_index[$@]";
        return;
    }

    my @indices = @INDICES;
    my $mdat_pos = 999999999;
    my $free_size = 0;

    my ($moov_pos, $moov_size);
    # Make sure moov occurs AFTER mdat, otherwise no need to run!
    foreach my $atom (@indices) {
        my $pos = @{$atom}[1];
        my $size = @{$atom}[2];
        # The atoms are guaranteed to exist from get_index above!
        if (@{$atom}[0] eq "moov") {
            $moov_pos = $pos;
            $moov_size = $size;
        } elsif (@{$atom}[0] eq "mdat") {
            $mdat_pos = $pos;
        } elsif (@{$atom}[0] eq "free" && $pos < $mdat_pos) {
            # This free atom is before the mdat!
            $free_size += $size;
            warn("Free atom at $pos ($size bytes)");
        }
    }

    # Offset to shift positions
    my $offset = $moov_size - $free_size;

    if( $moov_pos < $mdat_pos) {
        # No free atoms and moov is correct, we are done!
        die("This file appears to already be setup for streaming!")
    }

    # Open the output file to write on it
    my $outfile;
    open($outfile, ">", $outfilename) or die("No se pudo abrir el archivo: $outfilename");
    binmode $outfile;

    # Write ftype
    my @ftyp;
    foreach my $atom (@indices) {
        if(@{$atom}[0] eq 'ftyp') {
            @ftyp = @{$atom};
        }
    }

    if(scalar @ftyp > 0 ) {
        my $pos = $ftyp[1];
        my $size = $ftyp[2];
        seek($datastream, $pos, 0);
        read($datastream, my $buffer, $size);
        print $outfile $buffer;
    } else {
        die('No se encontro el atom: ftyp');
    }

    seek($datastream, $moov_pos+8, 0);
    &find_atoms($moov_size - 8, $datastream, 0);

    # Read and fix moov. Also write in to the output file
    seek($datastream, $moov_pos, 0);
    &fix_moov($moov_size, $datastream, $outfile, $offset);

    # Write the rest
    my $written = 0;
    # Covers the remaining atoms
    foreach my $atom (@indices) {
        if(@{$atom}[0] =~ /^(ftyp|moov|free)$/) {
            next;
        }
        my $pos = @{$atom}[1];
        my $size = @{$atom}[2];
        seek($datastream, $pos, 0);

        # Write in chunks to not use too much memory
        my $chunks = $size / $CHUNK_SIZE;
        foreach my $x (1 .. ($chunks)) {
            read($datastream, my $buffer, $CHUNK_SIZE);
            print $outfile $buffer;
            $written += $CHUNK_SIZE;
        }
        if($size % $CHUNK_SIZE) {
            read($datastream, my $buffer, ($size % $CHUNK_SIZE));
            print $outfile $buffer;
            $written += ($size % $CHUNK_SIZE);
        }
    }
    # Close both files
    close($outfile);
    close($datastream);
}
