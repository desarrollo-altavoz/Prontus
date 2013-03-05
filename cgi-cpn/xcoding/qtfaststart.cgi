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

use strict;

use File::Copy;
use File::Temp qw/tempfile/;

my $VERSION = "1.0";
my $CHUNK_SIZE = 8192;

my %INDICES;
my %STCOs;
main: {
    my $infile = $ARGV[0];
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
        warn("No existe por lo menos uno de los atoms obligatorios");
        exit;
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
    foreach my $id (sort keys %STCOs) {

        my $atom_type = $STCOs{$id}[0];
        my $atom_pos = $STCOs{$id}[1];
        my $atom_size = $STCOs{$id}[2];
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
            warn("Removing free atom at $pos ($size bytes)");
        }
    }

    # Offset to shift positions
    my $offset = $moov_size - $free_size;

    if( $moov_pos < $mdat_pos) {
        # moov appears to be in the proper place, don't shift by moov size
        $offset -= $moov_size;
        unless($free_size) {
            # No free atoms and moov is correct, we are done!
            die("This file appears to already be setup for streaming!")
        }
    }

    # Open the output file to write on it
    my $outfile;
    open($outfile, ">", $outfilename) or die("No se pudo abrir el archivo: $outfilename");
    binmode $outfile;

    # Write ftype
    if($indices{'ftyp'}) {
        my $pos = $indices{'ftyp'}[0];
        my $size = $indices{'ftyp'}[1];
        seek($datastream, $pos, 0);
        read($datastream, my $buffer, $size);
        print $outfile $buffer;
    } else {
        die('No se encontro el atom: ftyp');
    }

    # Read and fix moov. Also write in to the output file
    seek($datastream, $moov_pos, 0);
    &fix_moov($moov_size, $datastream, $outfile, $offset);

    # Write the rest
    my $written = 0;
    my %atoms;
    foreach my $item (keys %indices) {
        if($item !~ /^(ftyp|moov|free)$/) {
            $atoms{$item} = $indices{$item};
        }
    }
    # Covers the remaining atoms
    foreach my $atom (keys %atoms) {
        my $pos = $atoms{$atom}[0];
        my $size = $atoms{$atom}[1];
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
