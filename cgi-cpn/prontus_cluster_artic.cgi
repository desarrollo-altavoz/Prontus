#!/usr/bin/perl

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# SCRIPT.
# -----------
#

# ---------------------------------------------------------------
# UBICACION.
# -----------
#

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
#

# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------
#

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como Postproceso de articulo, operando solo con el primero de los parametros enviados:
# <path_al_html_del_artic>: por ejemplo:
# /sites/cooperativa.cl/web/prontus_nots/site/artic/20080522/pags/20080522111854.html
# Debe ser invocado al final de los demas PProcesos que hayan, de manera que copie todo
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
#

# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
#


# ---------------------------------------------------------------
# Tablas.
# ------------------------
#
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 06/2008 - YCH - Primera version.
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
close STDOUT;

BEGIN {

    use FindBin '$Bin';
    my $pathCGIProntus = $Bin; # por ej /sites/misitio.cl/web/cgi-p10.14
    unshift(@INC,$pathCGIProntus);

};

use prontus_varglb; &prontus_varglb::init();
use lib_maxrunning;
use lib_prontus;
use strict;
use lib_clustering;
use Benchmark ':hireswallclock';
use lib_waitlock; # Bloqueos tipo espera.
# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------




main:{
    my ($ts, $prontus_id);

    my $iniTime = new Benchmark;
    &lib_clustering::abreLogServer();
    print STDERR "\n--------------------------------\n";

    # Nro. de instacias simultaneas.
    # Soporta un maximo de n copias corriendo.
    if (&lib_maxrunning::maxExcedido(40)) {
      &lib_clustering::salir("Se ha alcanzado max instancias = 40, se aborta ejecucion\n");
      exit;
    };

    # Descompone y valida dato de entrada
    my $origen = $ARGV[0];
    $origen =~ s/^(.*?\/)pags(\/\d*?\.)(.*?)$/$1xml$2xml/;
    if ($origen =~ m|^(.*)(/(.*?)/site/artic/\d{8}/xml)/(\d{14})\.xml$|) {
        $prontus_varglb::DIR_SERVER = $1;
        $ts = $4;
        $prontus_id = $3;
    } else {
        &lib_clustering::salir("error al descomponer el path de entrada");
    };
    # valida dir prontus
    if (! -d "$prontus_varglb::DIR_SERVER/$prontus_id") {
        &lib_clustering::salir("Error: Directorios de trabajo no válidos.");
    };

    # Semaforo por articulo
    my $dir_smf = "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/data/procs";
    &glib_fildir_02::check_dir($dir_smf) || &lib_clustering::salir("Error: No se pudo crear dir de semaforo [$dir_smf]");
    my $semaforo = "$dir_smf/semaforo_cluster_articulos_$ts";
    $lib_waitlock::MAX_SEGS = 120;
    &lib_waitlock::lock_file($semaforo); # se le pasa el path completo al arch. semaforo.
    print STDERR "dentro de area critica [$semaforo]...\n";

    # Carga variables de configuracion.
    &lib_prontus::load_config("$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id.cfg");

    %lib_clustering::CLUSTERING_SERVER                  = %prontus_varglb::CLUSTERING_SERVER;
    $lib_clustering::CLUSTERING_DEBUG_LEVEL             = $prontus_varglb::CLUSTERING_DEBUG_LEVEL;
    $lib_clustering::CLUSTERING_TIMEOUT_CONNECT_SEGS    = $prontus_varglb::CLUSTERING_TIMEOUT_CONNECT_SEGS;
    $lib_clustering::CLUSTERING_LOG_DURATION_SEGS       = $prontus_varglb::CLUSTERING_LOG_DURATION_SEGS;
    $lib_clustering::CLUSTERING_FILE_UPDATE_SEGS        = $prontus_varglb::CLUSTERING_FILE_UPDATE_SEGS;

    print STDERR "Preparado para iniciar TX FTP\n";
    print STDERR "CLUSTERING_DEBUG_LEVEL[$lib_clustering::CLUSTERING_DEBUG_LEVEL]\n";
    print STDERR "CLUSTERING_TIMEOUT_CONNECT_SEGS[$lib_clustering::CLUSTERING_TIMEOUT_CONNECT_SEGS]\n";
    print STDERR "CLUSTERING_LOG_DURATION_SEGS[$lib_clustering::CLUSTERING_LOG_DURATION_SEGS]\n";
    print STDERR "CLUSTERING_FILE_UPDATE_SEGS[$lib_clustering::CLUSTERING_FILE_UPDATE_SEGS]\n\n";

    # Clusterea archivos estandares del articulo
    # Esta funcion abre automaticamente el ftp si es que la conexion no esta abierta
    &lib_clustering::articUpdateCluster($prontus_varglb::DIR_SERVER, $ts, $prontus_id, \%prontus_varglb::MULTIVISTAS);

    # Cerrar conexiones ftp
    foreach my $numServer (keys %lib_clustering::CLUSTERING_SERVER) {
        $lib_clustering::CLUSTERING_SERVER{$numServer}{'connection'}->quit() || print STDERR "" if (ref($lib_clustering::CLUSTERING_SERVER{$numServer}{'connection'}));
    };

    # recupera log
    &lib_clustering::abreLogServer();

    # Elimina el bloqueo y termina ejecucion.
    &lib_waitlock::unlock_file($semaforo);
    print STDERR "\nsaliendo de area critica [$semaforo]...\n";

    # Tiempo de ejecucion
    my $endTime=new Benchmark;
    print STDERR "\nTotal time: " . timestr(timediff($endTime, $iniTime), 'all') . "\n";

};



# -------------------------END SCRIPT----------------------------