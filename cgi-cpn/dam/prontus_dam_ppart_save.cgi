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
# Guarda datos en tabla ASSET
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 1.0.0 - 03/07/2009 - PRB - Primera version
# 1.0.1 - 18/05/2010 - YCC - En Begin{} usa $Bin para determinar ruta de las libs CGI
# 1.0.2 - 06/08/2010 - CVI - Se corrige bug al poner un primer video o video sin foto
# 1.0.3 - 24/02/2011 - PRB - Se quitan comillas a campos del insert, ya que la lib_prontus
#                            las deja listas entre comillas.
#
# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);

    $pathLibsProntus =~ s/\/dam$//;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

close STDOUT;

use strict;
use prontus_varglb;&prontus_varglb::init();
use lib_prontus;
use lib_dam;
use Artic;
use glib_dbi_02;

use DBI;

# Fix Dir Server
my $cron_server = $Bin;
$cron_server =~ s/\/[^\/]+\/dam$//;
$prontus_varglb::DIR_SERVER = $cron_server;

main:{
    #warn('+++'.$prontus_varglb::IP_SERVER.'++++');
    my $dir_server;
    my $prontus_id;
    my $fechap;
    my $ts_artic;

    my $origen = $ARGV[0];
    $origen =~ /(\d{14}\.\w+)$/;
    my $file_artic = $1;
    $origen =~ s/^(.*?\/)pags(\/\d*?\.)(.*?)$/$1xml$2xml/;
    if($origen =~ m|^(.*)/(.*?)/site/artic/(\d{8})/xml/(\d{14})\.xml$|) {
        $dir_server = $1;
        $prontus_id = $2;
        $fechap     = $3;
        $ts_artic   = $4;
    } else {
        warn('Error al descomponer el path de entrada');
        exit;
    };

    # Carga variables de configuracion.
    my $path_conf = &lib_prontus::get_relpathconf_by_prontus_id($prontus_id);
    &lib_prontus::load_config( &lib_prontus::ajusta_pathconf($path_conf) );

    # Inicia conexion a BD
    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        warn('Hubo problemas para conetarse a la BD: [' . $msg_err_bd . ']');
        exit;
    };

    my ($prontus_id, $dir_server, $ip_server) = ($prontus_varglb::PRONTUS_ID, $prontus_varglb::DIR_SERVER, $prontus_varglb::IP_SERVER);
    &lib_dam::procesa_artic($ts_artic, $prontus_id, $dir_server, $ip_server, $base);
};

