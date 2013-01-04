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
# Elimina los archivos, en tabla ASSET, asociados a un articulo eliminado
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 1.0.0 - 17/07/2009 - PRB - Primera version
# 1.0.1 - 18/05/2010 - YCC - $prontus_id ahora se recibe por ARGV en vez de estar en duro.
#                          - En Begin{} usa $Bin para determinar ruta de las libs CGI
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
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus

};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

close STDOUT;

use strict;
use prontus_varglb;&prontus_varglb::init();
use lib_prontus;

# Fix Dir Server
my $cron_server = $Bin;
$cron_server =~ s/\/[^\/]+\/dam$//;
$prontus_varglb::DIR_SERVER = $cron_server;

main:{

    # Carga archivo de configuracion
    my $prontus_id = $ARGV[1];
    my $path_conf = &lib_prontus::ajusta_pathconf('/' . $prontus_id . '/cpan/' . $prontus_id . '.cfg');
    &lib_prontus::load_config($path_conf);

    # Inicia conexion a BD
    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        warn('Hubo problemas para conetarse a la BD: [' . $msg_err_bd . ']');
        exit;
    };

    # Elimina los archivos de ese TS
    my $ts = $ARGV[0];
    if($ts =~ /^\d{14}$/i) {
      my $sql = 'delete from ASSET where ASSET_ART_ID = "' . $ts . '"';
      $base->do($sql);
    };
};
