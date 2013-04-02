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
# CGI encargada de eliminar un modelo Local
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 01 - 11/2005 - YCH - Primera Version.
#
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

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


main:{

    &glib_cgi_04::new();
    
    my $modelid = &glib_cgi_04::param('modelid');

    # Valida que el modelo exista
    if (! &wizard_lib::backup_model($modelid)) {
        my $resp;
        $resp->{'error'} = 1;
        $resp->{'msg'} = "No se pudo respaldar el modelo antes de eliminar. El modelo no ha sido eliminado";
        &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=1');
    };

    # Chequea modelo online
    my $nodisponible = 0;   
    my $urlCFG = "$wizard_lib::URL_MODELS/$modelid/$modelid.cfg";
    print STDERR "Chequeando el modelo online [$urlCFG]\n";
    my ($buffercfg, $msg_err) = &lib_prontus::get_url($urlCFG, 30);
    if($msg_err || $buffercfg eq '') {
        print STDERR "CFG de modelo no encontrado o invalido [$wizard_lib::URL_MODELS/$modelid/$modelid.cfg]\n";
        $nodisponible = 1;
    };
        
    my $dirmodel = "$prontus_varglb::DIR_SERVER$wizard_lib::MODELS_DIR/$modelid";
    print STDERR "Eliminando modelo: $dirmodel\n";
    &glib_fildir_02::borra_dir($dirmodel);
    
    my $resp;
    $resp->{'error'} = 0;
    $resp->{'msg'} = '';
    $resp->{'nodisponible'} = $nodisponible;
    print "Content-Type: application/json\n\n";
    &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=0');
};

# -------------------------------END SCRIPT----------------------

