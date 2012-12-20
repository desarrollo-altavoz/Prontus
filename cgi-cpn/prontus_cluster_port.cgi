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
    unshift(@INC,$Bin); # Para dejar disponibles las librerias


};


use prontus_varglb; &prontus_varglb::init();
use lib_maxrunning;
use lib_prontus;
use strict;
use lib_waitlock; # Bloqueos tipo espera.
use lib_clustering;
use Benchmark ':hireswallclock';

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------


main:{
    my ($nomport, $extport, $prontus_id, $edic);

    my $iniTime=new Benchmark;
    &lib_clustering::abreLogServer();
    print STDERR "\n--------------------------------\n";

    # Nro. de instacias simultaneas.
    # Soporta un maximo de n copias corriendo.
# Desactivado para permitir invocaciones masivas.
#    if (&lib_maxrunning::maxExcedido(500)) {
#      &lib_clustering::salir("Se ha alcanzado max instancias = 500, se aborta ejecucion\n");
#    };

    # /sites/prontus_development/web/prontus_toolbox/site/edic/2009_04_22_1/port/inicio.php
    my $origen = $ARGV[0];

    if ($origen =~ m|^(.*)/(\w+?)/site/edic/(\w+)/port/(\w+)\.(\w+)$|) {
        $prontus_varglb::DIR_SERVER = $1;
        $prontus_id = $2;
        $edic = $3;
        $nomport = $4;
        $extport = $5;
    } else {
        &lib_clustering::salir("error al descomponer el path de entrada");
    };


    # valida dir prontus
    if (! -d "$prontus_varglb::DIR_SERVER/$prontus_id") {
        &lib_clustering::salir("Error: Directorios de trabajo no válidos [$prontus_id].");
    };

    # Semaforo
    my $dir_smf = "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/data/procs";
    &glib_fildir_02::check_dir($dir_smf) || &lib_clustering::salir("Error: No se pudo crear dir de semaforo [$dir_smf]");
    my $semaforo = "$dir_smf/semaforo_cluster_portadas_$nomport";
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


    # Clusterea archivos
    # -------- PARTE ESPECIFICA --------
    # Esta funcion abre automaticamente el ftp si es que la conexion no esta abierta
    my ($relDir) = "/$prontus_id/site/edic/$edic/port";
    &lib_clustering::transmiteArchs($prontus_varglb::DIR_SERVER, $relDir, '^' . $nomport . '\.' . $extport . '$');

    my ($relDirXml) = "/$prontus_id/site/edic/$edic/xml";
    &lib_clustering::transmiteArchs($prontus_varglb::DIR_SERVER, $relDirXml, '^' . $nomport . '\.xml' . '$');

    my $nomport_origen = $nomport . '.' . $extport;


    # Agregar las portadas secundarias
    my @paralel_ports;
    foreach my $nomport_in_cfg (keys %prontus_varglb::PORT_PLTS_EXTRA) {

        next if ($nomport_origen ne $nomport_in_cfg); # obtiene las portadas extras solo para la portada en cuestion
        my $extra_ports = $prontus_varglb::PORT_PLTS_EXTRA{$nomport_in_cfg}; # contiene los items separados por ;
        # warn "nomport[$nomport]   extra_ports[$extra_ports]";
        while ($extra_ports =~ /([\w\-\.]+) *;?/g) {
            my $extra_port = $1;
            next if (!-f "$prontus_varglb::DIR_SERVER$relDir/$extra_port");
            push @paralel_ports, $extra_port;
            my ($nom, $ext) = &lib_prontus::split_nom_y_extension($extra_port);
            &lib_clustering::transmiteArchs($prontus_varglb::DIR_SERVER, $relDir, '^' . $nom . '\.' . $ext . '$');
            # print STDERR "extra_port[$extra_port]\n";
        };
    };


    # Multivistas
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        &lib_clustering::transmiteArchs($prontus_varglb::DIR_SERVER, "$relDir-$mv", '^' . $nomport . '\.' . $extport . '$');
        foreach my $paralel_port (@paralel_ports) {
            my ($nom, $ext) = &lib_prontus::split_nom_y_extension($paralel_port);
            &lib_clustering::transmiteArchs($prontus_varglb::DIR_SERVER, "$relDir-$mv", '^' . $nom . '\.' . $ext . '$');
        };
    };

    # Rss
    $relDir = "/$prontus_id/site/edic/base/rss";
    &lib_clustering::transmiteArchs($prontus_varglb::DIR_SERVER, $relDir, '^' . $nomport . '\.xml$');

    # -------- /PARTE ESPECIFICA --------

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