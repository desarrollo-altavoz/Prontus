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
# CGI encargada de descargar/actualizar un modelo Local
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
    my $res = qx/ps auxww |grep 'wizard_models_download_real.cgi '|grep -v grep/; # con un espacio, para no confundir con tail de error log.

    if ($res ne '') {
        my $resp;
        $resp->{'error'} = 1;
        $resp->{'msg'} = 'Por favor, espere a que termine la descarga anterior.';
        print "Content-Type: application/json\n\n";
        &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=0');
    };

    # Se chequea si existe el modelo online
    my $nodisponible = 0;
    my $urlCFG = "$wizard_lib::URL_MODELS/$modelid/$modelid.cfg";
    print STDERR "Chequeando el modelo online [$urlCFG]\n";
    my ($buffercfg, $msg_err) = &lib_prontus::get_url($urlCFG, 30);
    if($msg_err || $buffercfg eq '') {
        my $resp;
        $resp->{'error'} = 1;
        $resp->{'msg'} = "CFG de modelo no encontrado o invalido [$wizard_lib::URL_MODELS/$modelid/$modelid.cfg]\n";
        print STDERR $resp->{'msg'};
        print "Content-Type: application/json\n\n";
        &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=0');
    };

    # En el caso que no exista el directorio de los modelos
    &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$wizard_lib::MODELS_DIR");

    # Se respalda el modelo si es que existe.
    my $dirmodel = "$prontus_varglb::DIR_SERVER$wizard_lib::MODELS_DIR/$modelid";
    if(-d $dirmodel) {
        if (! &wizard_lib::backup_model($modelid)) {
            my $resp;
            $resp->{'error'} = 1;
            $resp->{'msg'} = "No se pudo respaldar el modelo antes de eliminar. El modelo no ha sido eliminado";
            print "Content-Type: application/json\n\n";
            &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=0');
        };
    };

    &glib_fildir_02::write_file($STATUS_FILE, 0);

    my $cmd = "/usr/bin/perl $prontus_varglb::DIR_SERVER/$prontus_varglb::DIR_CGI_CPAN/wizard_models_download_real.cgi $modelid >/dev/null 2>&1 &";
    print STDERR "cmd[$cmd]\n";
    system($cmd);

    my $resp;
    $resp->{'error'} = 0;
    $resp->{'msg'} = '';
    print "Content-Type: application/json\n\n";
    &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=0');
}
