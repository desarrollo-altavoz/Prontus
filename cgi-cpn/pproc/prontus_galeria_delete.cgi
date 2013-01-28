#!/usr/bin/perl
#
# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Eliminar los XML de los Articlos tipo Media
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# -----------------------
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ---------------------------
#
# ---------------------------------------------------------------
# VERSIONES
# ---------------------------
# 1.0 - 21/07/2009 - CVI - Primera version.
#
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

# ###################################################
# Main
# open OUT,">$ROOTDIR/debug.txt";
BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias sueltas
    $pathLibsProntus =~ s/\/pproc$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use glib_cgi_04;

&glib_cgi_04::new();

my $ROOTDIR     = $ENV{'DIR_SERVER'};
my $TS          = &glib_cgi_04::param('ts');
my $PRONTUS_ID  = &glib_cgi_04::param('prontus_id');

my $file = "$ROOTDIR/$PRONTUS_ID/cpan/procs/status_fotorama/$TS.json";

# Para eliminar la paginas de la galeria de fotos
if(-f $file) {
    unlink($file);
};

print STDOUT "Content-Type: text/html\n\n";
print STDOUT "{status: 'ok'}";
