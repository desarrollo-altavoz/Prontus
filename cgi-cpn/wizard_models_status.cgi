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
# PROPOSITO.
# -----------
# CGI encargada de obtener el status de la descarga/actualizacion
# de un modelo.
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 14/08/2014 - JOR - Primera Version.
#
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200, 'wizard_error_log');

use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use strict;
use lib_prontus;
use wizard_lib;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%PRONTUS);
my ($INF_DIR) = "$prontus_varglb::DIR_SERVER/wizard_prontus/_data";
my ($INF_FILE) = "$INF_DIR/inf.txt";
my ($STATUS_FILE) = "$INF_DIR/progress.txt";

main:{
    &glib_cgi_04::new();

    my $modelid = &glib_cgi_04::param('modelid');

    my $res = qx/ps auxww |grep 'wizard_models_download_real.cgi '|grep -v grep/;
    my $resp;

    if ($res ne '') {
        $resp->{'status'} = 1; # ocupado.
        $resp->{'msg'} = '';

        if (-s $STATUS_FILE) {
            my $progress = &glib_fildir_02::read_file($STATUS_FILE);
            if ($progress eq '100') {
                $resp->{'msg'} = "Instalando";
            } elsif ($progress =~ /(\d+)/) {
                $resp->{'msg'} = "Descargando ($1%)";
            } else {
                $resp->{'status'} = 0; # error.
                $resp->{'msg'} = $progress;
            };
        };

    } else {
        $resp->{'status'} = 2; # disponible.
        $resp->{'msg'} = '';

        if (-f $STATUS_FILE) {
            my $progress = &glib_fildir_02::read_file($STATUS_FILE);
            if ($progress !~ /(\d+)/) {
                $resp->{'status'} = 0; # error.
                $resp->{'msg'} = $progress;
            };

            unlink $STATUS_FILE;
        };

        ## revisar si se descargo el modelo.
    };

    print "Content-Type: application/json\n\n";
    &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=0');
};
