#!/usr/bin/perl
# --------------------------------------------------------------
# Respaldo de archivos prontus en Dropbox.
# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 11/11/2014 - JOR - Primera versión
# 2.0.0 - 26/02/2017 - ALD - Actualiza a v2 de la API
#                          - Cambios en la logica para asegurar el proceso
#                            de todos los archivos en /dropbox.
#                          - Usa forks para acelerar el proceso.
#                          - Solo considera el nombre del Prontus como parametro,
#                            ya que siempre procesa todos los archivos en /dropbox.
# 2.0.1 - 28/02/2017 - ALD - Elimina el fork, ya que es penalizado por la API 2 de dropbox.
#                          - Valida hash de los archivos antes de subirlos.
# 2.0.2 - 09/03/2017 - EAG - Se agrega funcion de salida para no dejar tomado el semaforo en caso de error.
#                            Se modifica opcion para no tener problemas al dejar en segundo plano
# ---------------------------------------------------------------
# 2do:
# - Perfeccionar el sistema de semaforo: si hay un proceso corriendo estaria ok,
#   no hay para que matarlos a todos.
# - Revisar que otros directorios seria necesario sincronizar para tener un
#   verdadero site de contingencia.

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};
END {
    &tareas_salida();
};

use sigtrap 'handler' => \&signal_catch, 'INT';
use sigtrap 'handler' => \&signal_catch, 'TERM';

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use Time::Local;

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use lib_dropbox;

my %FORM;
my $DIR_SEMAF;

main: {
    $FORM{'prontus_id'} = $ARGV[0];

    &valida_params();

    my ($prontus_id, $ts, $dir_fecha, $relpath_artic);

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus_id'});
    &lib_prontus::load_config(&lib_prontus::ajusta_pathconf($relpath_conf));

    if ($prontus_varglb::DROPBOX eq 'NO' || $prontus_varglb::DROPBOX_ACCESS_TOKEN eq '') {
        # No se hace nada.
        exit;
    };

    print STDERR "[$$] Inicio\n";

    $DIR_SEMAF = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/data/semaforos";
    &glib_fildir_02::check_dir($DIR_SEMAF) if (! -d $DIR_SEMAF);

    if (-f "$DIR_SEMAF/dropbox_backup.lck") {
        my $mtime = (stat("$DIR_SEMAF/dropbox_backup.lck"))[9];
        my $now = time;
        my $diff = $now - $mtime;

        if ($diff > 7200) { # 2 hrs.
            print STDERR "[$$] Semaforo muy antiguo, eliminando...";
            unlink "$DIR_SEMAF/dropbox_backup.lck";

            my $res = `ps auxww |grep 'prontus_dropbox_backup.cgi $prontus_varglb::PRONTUS_ID' | grep -v grep | wc -l`;

            if ($res) {
                system('kill -9 `ps -auxww | grep \'prontus_dropbox_backup.cgi ' . $prontus_varglb::PRONTUS_ID . '\' | grep -v grep | awk \'{print $2}\' | grep -v ' . $$ . '`');
            };
        };
    };

    &glib_fildir_02::write_file("$DIR_SEMAF/dropbox_backup.lck", $$);

    # Inicializa modulo dropbox.
    &lib_dropbox::init($prontus_varglb::DROPBOX_ACCESS_TOKEN);

    # Revisa si hay archivos.
    my $dir_dropbox = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/dropbox";
    my ($file,$recurso);
    my %days; # 2.0.0 Dias a procesar (un dia especial es 'port', que procesa las portadas).

    my @files = glob("$dir_dropbox/*.txt");
    while (scalar @files > 0) {
        print STDERR "[$$] Buscando si hay archivos...\n";
        %days = ();
        while (defined($file = shift @files)) {
            print STDERR "[$$] Procesando [$file]\n";
            next if (!-s $file);
            &procesar_archivo($file,\%days);
            # print STDERR "[$$] Se termino de procesar [$file].\n";

        };
        # Respalda los contenidos correspondientes.
        foreach $recurso (keys %days) {
            print STDERR "[$$] Procesando recurso [$recurso]\n";
            if ($recurso eq 'port') {
                &procesar_port();
            }else{
                &procesa_art($recurso);
            };
            # Actualiza fecha modificacion semaforo, para que no lo vayan a matar!
            utime time, time, "$DIR_SEMAF/dropbox_backup.lck";
        };

        @files = glob("$dir_dropbox/*.txt");
    };

    # Respalda la taxonomia.
    &procesa_tax();

    # &procesa_ejemplo(); # debug

    print STDERR "[$$] Fin.\n";

}; # main

# ----------------------------------------------------------------------------- #
# tareas que se deben realizar al terminar el script
sub tareas_salida {
    unlink "$DIR_SEMAF/dropbox_backup.lck";
}
# ---------------------------------------------------------------
# funcion para capturar las señales INT y TERM y logearlas
sub signal_catch {
    print STDERR  "Terminado por signal @_\n";
    exit(0);
}
# ----------------------------------------------------------------------------- #
sub procesar_archivo {
    my ($file,$days) = @_;

    open (FILE, "<$file");
    foreach my $linea (<FILE>) {
        chomp($linea);
        my ($tipo, $recurso, $param1, $param2, $param3) = split(';', $linea);
        print STDERR "[$$] tipo[$tipo] recurso[$recurso]\n";
        if ($tipo eq 'art') {
            # Reduce recurso a un dia especifico.
            $recurso = substr($recurso,0,8);
            $$days{$recurso} = 1;
        } elsif ($tipo eq 'port') {
            $$days{'port'} = 1;
        };
    };
    close FILE;

    unlink $file;

}; # procesar_archivo

# ----------------------------------------------------------------------------- #
# 2.0.0 Sincroniza los directorios de portadas completos.
sub procesar_port {
    &recurseDirs("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/edic",
                                            "$prontus_varglb::DIR_CONTENIDO/edic");
}; # procesar_port

# ----------------------------------------------------------------------------- #
# 2.0.0 Sincroniza el directorio del dia del articulo completo.
sub procesa_art {
    my $ts = $_[0];
    my $dir_fecha;

    if ($ts =~ /(\d{8})/) {
        $dir_fecha = $1; # solo fecha.
        &recurseDirs("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha",
                                                "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$dir_fecha");
        # Se incluye la media externa.
        if ($prontus_varglb::EXTERNAL_MMEDIA == 1) {
            &recurseDirs("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EXMEDIA/$dir_fecha",
                                                    "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EXMEDIA/$dir_fecha");
        };

        # Se incluyen los archivos asociados externos.
        if ($prontus_varglb::EXTERNAL_ASOCFILE == 1) {
            &recurseDirs("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EXASOCFILE/$dir_fecha",
                                                    "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EXASOCFILE/$dir_fecha");
        };
    };
}; # procesa_art

# ----------------------------------------------------------------------------- #
# 2.0.0 Sincroniza el directorio de la taxonomia.
sub procesa_tax {
    # Incluye taxonomia.
    &recurseDirs("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/cache/taxonomia/pags",
                                            "$prontus_varglb::DIR_CONTENIDO/cache/taxonomia/pags");
}; # procesa_tax

# ----------------------------------------------------------------------------- #
# 2.0.0 Directorio de pruebas.
sub procesa_ejemplo {
    &recurseDirs("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO/artic/20170227/pags",
                                            "$prontus_varglb::DIR_CONTENIDO/artic/20170227/pags");
}; # procesa_ejemplo

# ----------------------------------------------------------------------------- #
sub valida_params {
    if ($FORM{'prontus_id'} eq '') {
        print STDERR "[$$] Debe indicar el nombre del Prontus.\n";
        exit;
    };

    if (!&lib_prontus::valida_prontus($FORM{'prontus_id'})) {
        print STDERR "Directorio Prontus no es v&aacute;lido\n";
        exit;
    }

}; # valida_params

# ----------------------------------------------------------------------------- #
# Recorre los directorios recursivamente, subiendo a Dropbox los archivos que no
# existen o que tienen un peso distinto.
sub recurseDirs {
    my($source,$destination) = @_;
    my($entry,$dropBoxEntry,$path,$esdir,$size,$pid,$res);
    my ($fileTime,$numEntries,$aux,$localHash,$dropBoxHash,$debeSubir);
    my(@entries,@dropboxEntries);
    my %dropboxFileSizes;
    my %dropboxFileTimes;
    my %dropboxFileHashes;

    # Si el directorio es cpan/data/search o es /cache o /bak, sale sin hacer nada.
    if (($source =~ /cpan\/data\/search/) || ($source =~ /\/cache$/) || ($source =~ /\/bak$/)) {
        # print "    Banned Dir: $source\n"; # debug
        return;
    };

    opendir(DIR, $source) || die "Can't opendir " . $source . $!;
    @entries = readdir(DIR);
    closedir DIR;

    # 2.1.0 Si el directorio esta vacio, sale sin hacer nada.
    $numEntries = scalar(@entries);
    if ($numEntries <= 2) {
        # print "    Empty Dir: $source\n"; # debug
        return;
    };

    print STDERR "[$$] Inicio: $source [$numEntries] -> $destination\n"; # debug

    # Lee las entradas de dropbox en el destino. <path>\t<es dir>\t<tamano en bytes>
    @dropboxEntries = &lib_dropbox::getDir($destination);
    # Obtiene los tamanos de archivo. Si es un directorio asigna el tamano -1.
    %dropboxFileSizes = ();
    %dropboxFileTimes = ();
    # print "    Listado de $destination en dropbox:\n";
    foreach $dropBoxEntry (@dropboxEntries) {
        ($path,$esdir,$size,$fileTime,$dropBoxHash) = split(/\t/,$dropBoxEntry);
        # Elimina los directorios superiores del path.
        if ($path =~ /\/([^\/]+)$/) {
            $path = $1;
        }else{
            $path = '/';
        };
        # Asigna el tamano.
        if ($esdir) {
            $dropboxFileSizes{$path} = -1;
        }else{
            $dropboxFileSizes{$path} = $size;
        };
        # Asigna el tiempo de modificacion en Dropbox.
        $dropboxFileTimes{$path} = &iso8601ToEpoch($fileTime);
        $dropboxFileHashes{$path} = $dropBoxHash;
        # print "    $path $size $fileTime\n"; # debug
    };

    # Recorre los archivos y subdirectorios.
    foreach $entry (sort @entries) {
        # # 1.1.0 Solo procesa si la fecha es posterior a 20161201
        # if ($entry =~ /^\d{8}$/) {
        #     next if ($entry < 20161201);
        # };
        # Si es un directorio, entonces aplica de nuevo la rutina en forma recursiva.
        # No copia los directorios que empiezan con un punto.
        if ((-d "$source/$entry") && ($entry !~ /^\./)) {
            &recurseDirs("$source/$entry","$destination/$entry");
        };

        if (-f "$source/$entry") {
            # 2.1.0 No considera los archivos que contengan 'preview.' en su nombre,
            # o sean nombres baneados por dropbox.
            $aux = lc $entry;
            if (($aux =~ /preview\./) || ($aux eq 'desktop.ini') || ($aux eq 'thumbs.db')
                 || ($aux eq '.ds_store') || ($aux eq "icon\r") || ($aux =~ /^\.dropbox/)) {
                # print "  Me salto preview: $source/$entry\n";
                next;
            };
            # Si los tamanos son cero arriba y abajo, no hace nada.
            if (($dropboxFileSizes{$entry} == 0) && ((-s "$source/$entry") == 0)) {
                next;
            };
            $debeSubir = 0;
            # Si no existe en dropbox o si los tamanos son distintos, lo sube.
            if ( $dropboxFileSizes{$entry} != -s "$source/$entry") {
                $debeSubir = 1;
            };
            ($dropBoxHash,$localHash) = ('','');
            # Si la fecha local es mas reciente que en dropbox, verifica hashes y sube si corresponde.
            if (($debeSubir == 0) && ( $dropboxFileTimes{$entry} < (stat "$source/$entry")[9] )) {
                # Compara los hashes por si los contenidos son identicos (suele suceder...).
                $dropBoxHash = $dropboxFileHashes{$entry};
                $localHash = &lib_dropbox::computeContentHash("$source/$entry");
                if ($localHash ne $dropBoxHash) {
                    $debeSubir = 1;
                };
            };
            if ($debeSubir == 1) {
                    print STDERR "[$$] Sube: $source/$entry d[".$dropboxFileSizes{$entry}.
                        "] s[".(-s "$source/$entry")."] t[".((stat "$source/$entry")[9] - $dropboxFileTimes{$entry}).
                        "] d[$dropBoxHash] s[$localHash]\n"; # debug
                # Hace la sincronizacion.
                $res = 0;
                while ($res == 0) { # 2.2.0
                    $res = &lib_dropbox::putFile("$source/$entry","$destination/$entry");
                    if ($res == 0) {
                        print STDERR "[$$] Falla subir: $source/$entry\n"; # debug
                    }else{
                        print STDERR "[$$] Res OK [$res]: $source/$entry\n"; # debug
                    };
                };
            }else{
                # print STDERR "    [$$] NO Sube: $source/$entry [".(-s "$source/$entry").
                #     "][".$dropboxFileSizes{$entry}."] t[".((stat "$source/$entry")[9] - $dropboxFileTimes{$entry}).
                #     "] d[$dropBoxHash] s[$localHash]\n"; # debug
            };
        };
    };

}; # recurseDirs

# ----------------------------------------------------------------------------- #
# Convierte una fecha en formato iso8601 (UTC) en epoch. Ejemplo: 2017-02-27T12:05:28Z
sub iso8601ToEpoch {
    my $utc = $_[0];
    my ($year,$mon,$mday,$hour,$min,$sec,$epoch);
    if ($utc =~ /(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z/) {
        ($year,$mon,$mday,$hour,$min,$sec) = ($1,$2,$3,$4,$5,$6);
        $year -= 1900;
        $mon--;
        # $epoch = POSIX::mktime( $sec, $min, $hour, $mday, $mon, $year );
        $epoch = timegm( $sec, $min, $hour, $mday, $mon, $year );
    };
    return $epoch;
}; # iso8601ToEpoch

# ----------------------------------------------------------------------------- #
sub epochToFechaHora {
    my $epoch = $_[0];
    my @utc = gmtime($epoch);
    my $fechahora = sprintf('%04d/%02d/%02d %02d:%02d:%02d',(1900 + $utc[5]),(1 + $utc[4]),$utc[3],$utc[2],$utc[1],$utc[0]);
}; # epochToFechaHora

# ----------------------------------------------------------------------------- #
# Retorna cuantas copias del mismo script hay corriendo.
sub myselfRunning {
   my($res) = qx/ps axww | grep $0 | grep -v ' grep ' | grep -v ' nice ' | wc -l/;
   $res =~ s/\D//gs;
   return $res;
}; # myselfRunning



