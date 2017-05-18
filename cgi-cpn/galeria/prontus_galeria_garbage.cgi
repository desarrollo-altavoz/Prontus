#!/usr/bin/perl
#
# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Eliminar los XML de los Articulos tipo Media
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
# 1.1 - 11/05/2017 - EAG - Se integra a Prontus
#
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

# ###################################################
BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias sueltas
    $pathLibsProntus =~ s/\/[^\/]+$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use glib_cgi_04;
use glib_fildir_02;

main: {
    my $ROOTDIR = $ENV{'DOCUMENT_ROOT'};
    if ($ROOTDIR eq '') {
        print "Esta cgi se debe invocar vía web\n";
        exit;
    }

    &glib_cgi_04::new();
    my $TS          = &glib_cgi_04::param('ts');
    my $PRONTUS_ID  = &glib_cgi_04::param('prontus_id');
    my $file = "$ROOTDIR/$PRONTUS_ID/cpan/procs/status_fotorama/$TS.json";

    # Para eliminar la semaforo de la galeria de fotos
    if(-f $file) {
        unlink($file);
    };

    # Para eliminar la carpeta con las fotos temporales
    my $dir = "$ROOTDIR/$PRONTUS_ID/cpan/procs/status_fotorama/$TS";
    if(-d $dir) {
        &glib_fildir_02::borra_dir($dir);
    };

    print "Cache-Control: no-cache, must-revalidate\r\n";
    print "Content-type: application/json\n\n";
    print '{"status": "ok"}';
}
