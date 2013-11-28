#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Funciones para controlar maximo de instancias de un script en ejecucion

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 1.0.0 - 06/2008 - YCC - Primera version.

# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

package lib_clustering;

use glib_fildir_02;
use glib_hrfec_02;

use Net::FTP;
use POSIX;
use Net::DNS;
use lib_maxrunning;
use lib_prontus;
use lib_artic;

our %CLUSTERING_SERVER; # servers a los que se debe transmitir
# 0:SOLO ERRORES | 1: ERRORES E INFORMACION BASICA | 2: TODO LO ANTERIOR Y ADEMAS DEBUG ESPECIFICO DE FTP
our $CLUSTERING_DEBUG_LEVEL = 0;

our $CLUSTERING_TIMEOUT_CONNECT_SEGS = 15;
our $CLUSTERING_LOG_DURATION_SEGS = 60; # el log se resetea despues de 1 minuto.
our $CLUSTERING_FILE_UPDATE_SEGS = 30; # Diferencia en segundos para actualizar un archivo.
# our $MAX_SEGS_DURACION = 180; # experimental

# our $BEGIN_TIME; # experimental: SETEARLO CON time() apenas se comience a transmitir, o bien, se ingrese al area critica

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub articUpdateCluster {
# Actualiza cluster con todos los archivos relacionados con el articulo
# o que hayan sido modificados producto de la actualizacion del articulo.
# Transmite todos los archivos que hayan sido modificados hace T minutos o menos.
# Se transmite:
#        - todas las vistas del artículo y los recursos asociados (fotos, asocfiles, etc)
#        - art. relac de la tax del art, todas las salidas paralelas que hayan
#        - art relac específico, en caso de haber indicado manualmente los relacionados

    my ($docRoot, $ts, $prontusID, $refHashMv) = @_;

    my %multivistas = %$refHashMv;

    my $dirFecha = substr($ts, 0, 8);
    my $relDirMmedia = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_EXMEDIA . "/$dirFecha";
    my $relDirArtic = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . "/$dirFecha";
    #~ my $dirArticXML = "$docRoot/$prontusID/site/artic/$dirFecha/xml";

    # Cargar datos del xml del articulo
    my $xmlArt = &lib_prontus::get_xml_data("$docRoot$relDirArtic/xml/$ts.xml");

    # Carga campos de interes desde el xml del articulo
    my %camposArtXML = &lib_prontus::getCamposXml($xmlArt, '_SECCION1,_TEMA1,_SUBTEMA1');

    # Artic. relacionados 4_0_0_art_relac.html en prontus_nots\site\cache\taxonomia\pags\
    # En base a:
    # <_SECCION1>2</_SECCION1>
    # <_TEMA1>28</_TEMA1>
    # <_SUBTEMA1>97</_SUBTEMA1>

    # Transmite los relacionados por s,t,st
    my $s = $camposArtXML{'_SECCION1'};
    my $t = $camposArtXML{'_TEMA1'};
    my $st = $camposArtXML{'_SUBTEMA1'};
    if ($s) {
        &transmiteArchs($docRoot, "/$prontusID/site/cache/taxonomia/pags", '^' . $s . '_' . $t . '_' . $st . '_');
    };

    # imag, swf, mmedia, asocfile, pags
    &transmiteArchs($docRoot, "$relDirArtic/imag", $ts . '\.\w+$');
    &transmiteArchs($docRoot, "$relDirArtic/swf", $ts . '\.\w+$');
    &transmiteArchs($docRoot, "$relDirArtic/asocfile/$ts", '[\w\-]+\.\w+$');
    &transmiteArchs($docRoot, "$relDirMmedia/mmedia", $ts . '\.\w+$');

    # Vista principal
    # relDirArtic: /prontus_nots/site/artic/20080714
    # /pags/20080714114420.html
    &transmiteArchs($docRoot, "$relDirArtic/pags", $ts . '\.\w+$');

    # XML
    &transmiteArchs($docRoot, "$relDirArtic/xml", $ts . '\.\w+$');

    # Multivistas
    foreach my $mv (keys %multivistas) {
        &transmiteArchs($docRoot, "$relDirArtic/pags-$mv", $ts . '\.\w+$');
    };

};

# ---------------------------------------------------------------
sub transmiteArchs {
# Lee dir y transmite todos los archivos del dir indicado que cumplan con la expresion regular
# indicada en $condicion.
# No se controla retorno de la funcion ya que se transmite lo que se pueda no mas

    my ($docRoot, $relDir2Transfer, $condicion) = @_;
    return if (! -d "$docRoot$relDir2Transfer");
    my @lisdir = &glib_fildir_02::lee_dir("$docRoot$relDir2Transfer");
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    foreach my $k (@lisdir) {
        if ($condicion ne '') {
            next if ($k !~ /$condicion/); # salta los que no correspondan
        };

        # En cada loop se intenta enviar el archivo a cada uno de los 3 servers
        &abreLogServer();
        print STDERR "\nEnviar [$docRoot$relDir2Transfer/$k]\n";

        my (@pid) = (); # PIDs de los procesos hijos.
        foreach my $numServer (keys %CLUSTERING_SERVER) {

            my ($ipServer) = $CLUSTERING_SERVER{$numServer}{'ip'};
            my ($userServer) = $CLUSTERING_SERVER{$numServer}{'user'};
            my ($passServer) = $CLUSTERING_SERVER{$numServer}{'pass'};

            # Usa un log por cada server
            &abreLogServer($ipServer, $userServer);
            print STDERR "\n[" . &glib_hrfec_02::get_dtime_pack4() . "] Enviar [$docRoot$relDir2Transfer/$k]\n"; # repite para que salga en el log local del server

            # Si el server presento algun error al conectarse a el, ya no se intenta transmitir nada
            # a ese server para este articulo.
            if ($CLUSTERING_SERVER{$numServer}{'errors'}) {
                print STDERR "\t* FTP a [$ipServer][$userServer]... Saltando server por haber presentado error de conexion\n";
                next;
            };

            # Mata conexion si es que se perdio luego de los reintentos (la verifica)
            my $serverResponde;
            if (ref($CLUSTERING_SERVER{$numServer}{'connection'})) {
                $serverResponde = $CLUSTERING_SERVER{$numServer}{'connection'}->pwd()
                                  || print STDERR "[$ipServer][$userServer]no se pudo ejecutar pwd\n";
                # print STDERR "\t[$ipServer][$userServer] serverResponde[$serverResponde]\n";
                if ($serverResponde !~ /^\//) {
                    print STDERR "\tMatando conexion...\n";
                    $CLUSTERING_SERVER{$numServer}{'connection'}->quit()
                                  || print STDERR "\t[$ipServer][$userServer]no se pudo ejecutar quit\n";
                    undef $CLUSTERING_SERVER{$numServer}{'connection'}; # la remata, por si las moscas
                };
            };


            # Se conecta si es que aun no lo esta.
            if (! ref($CLUSTERING_SERVER{$numServer}{'connection'})) {
                my ($ret, $offset) = &ftp_connect($ipServer, $userServer, $passServer, $docRoot);
                if (ref $ret) { # coneccion y login ok
                    $CLUSTERING_SERVER{$numServer}{'connection'} = $ret;
                    $CLUSTERING_SERVER{$numServer}{'offset'} = $offset;
                } else {
                    # Si no se puede conectar o loguear, sigue al siguiente server
                    print STDERR $ret;
                    $CLUSTERING_SERVER{$numServer}{'errors'} = 1;
                    next;
                };
            } else {
                print STDERR "\tFTP a [$ipServer][$userServer]... Reutilizando conexion existente / Offset [$CLUSTERING_SERVER{$numServer}{'offset'}]segs\n" if ($CLUSTERING_DEBUG_LEVEL >=1);
            };

            # Forkea transmision de archivo a cada server
            ELFORK: {
                $| = 1;
                  if ($pid = fork) {
                        # Yo soy el papa.
                    push @pid,$pid; # Recuerda el pid para control futuro.

                } elsif (defined $pid) { # $pid es 0, ya que es el hijo.
                    &writeFTPFile($docRoot, $relDir2Transfer, $k, $ipServer,
                                  $userServer, $passServer, $numServer, $CLUSTERING_SERVER{$numServer}{'connection'}, $CLUSTERING_SERVER{$numServer}{'offset'});
                    exit;
                  } elsif ($! =~ /no more process/) {
                    # Recuperacion del error.
                    sleep 5;
                    redo ELFORK;
                  }else{
                    # Error irrecuperable.
                    die "No puedo forkiarme [$!]\n";
                  }; # if
            }; # ELFORK
        }; # foreach CLUSTERING_SERVER

        # Espera que todos los hijos finalicen su ejecucion.
        foreach $pid (@pid) {
            waitpid $pid, 0; # Espera por los procesos hijos.
        };

    }; # foreach @lisdir
};

# -----------------------------------------------------------------
sub writeFTPFile {
# Escribe un archivo en el servidor FTP.
# No se controla retorno de la funcion ya que se transmite lo que se pueda no mas

    my ($docRoot, $localDir, $entry, $ipServer, $userServer, $passServer, $numServer, $coneccionFTP, $serverOffset) = @_;

    # por compatibilidad En clustering prontus habitualmente seran iguales.
    my $remote_dir = $localDir;

    # No hace nada si el archivo posee caracteres prohibidos.
    if ($entry =~ /[^0-9a-zA-Z\-\_\.]/) {
        print STDERR "\t* ERROR: [$docRoot$localDir/$entry] es un nombre corrupto, archivo no se transmite.\n";
        return;
    };

    # Realiza transmision del archivo
    my ($i) = 1;
    my ($error);
    my ($reconectado);

    do {
        my $cwd_ok = $coneccionFTP->cwd($remote_dir);
        # Si falla al posicionarse en el dir destino, lo mas probable es que no exista, tonces lo crea
        if (! $cwd_ok) {
            print STDERR "\tCreando dir remoto [$remote_dir]\n" if ($CLUSTERING_DEBUG_LEVEL >=1);
            if (! $coneccionFTP->mkdir($remote_dir, 1)) {
                # Si no puede crear dir, no intenta transferir el archivo y sigue al siguiente server
                print STDERR "\t* No se pudo crear [$remote_dir] en [$ipServer][$userServer]: " . $coneccionFTP->message;
                last;
            };
            # Ahora que lo ha creado, se posiciona y si ahora no se puede posicionar ya la cuestion guateo definitivamente
            $cwd_ok = $coneccionFTP->cwd($remote_dir);
            if (! $cwd_ok) {
                print STDERR "\t* No se puede cambiar a dir [$remote_dir] en [$ipServer][$userServer]: " . $coneccionFTP->message;
                last;
            };
        };

        print STDERR "\tPosicionado ok en dir remoto [$remote_dir]\n\tIniciando transmision del archivo...\n" if ($CLUSTERING_DEBUG_LEVEL >=1);

        # Ver si es necesario transferir de acuerdo a mtime del archivo
        my $rTime;
        $rTime = $coneccionFTP->mdtm($entry) || ($rTime = 0); # !$rTime implica que el arch. remoto no existe
        my $lTime = (stat("$docRoot$localDir/$entry"))[9];
        # my $lTime = time;
        my $difTime;
        # Compensa diferencia de horas entre ambos servidores.
        $difTime = $lTime - ($rTime + $serverOffset);
        # $difTime = ($rTime + $serverOffset) - $lTime;
#        if ($serverOffset >= 0) {
#            $difTime = $lTime - ($rTime + $serverOffset); # si el remote esta atrasado, le sumo el offset
#        } else {
#            $difTime = ($rTime + $serverOffset) - $lTime; # si el remote esta adelantado, le resto el offset (le sumo el valor negativo)
#        };

        my $debeActualizar = 0;
        if (!$rTime) {
            $debeActualizar = 1;
            print STDERR "Archivo nuevo, --> transferir.\n";
        } else {
            print STDERR "\tlTime[$lTime] time[" . time . "] rTime[$rTime] serverOffset[$serverOffset] difTime[$difTime]\n";
            if ($difTime > $CLUSTERING_FILE_UPDATE_SEGS) {
                print STDERR "Arch. existente pero antiguo --> Debe actualizar.\n";
                $debeActualizar = 1;
            };
        };

        if (!$debeActualizar) {
            print STDERR "\tArchivo estaba actualizado (difTime[$difTime]), envio ftp no requerido [...$entry]\n" if ($CLUSTERING_DEBUG_LEVEL >=1);
            return; # DEBUG, ACTUALIZAR SIEMPRE!! SIN CONSIDERAR LA ANTIG. DEL ARCHIVO.
        };

        # DEBUG, ACTUALIZAR SIEMPRE!! SIN CONSIDERAR LA ANTIG. DEL ARCHIVO.
        # print STDERR "COMPARACION DE ANTIGUEDAD DESACTIVADO --> SE COPIA SIEMPRE.\n";

        $error = $coneccionFTP->put("$docRoot$localDir/$entry") || ($error = '');

        # $error = 'mula' if ($entry =~ /FOTO_0420080702130349/); # debug para simular reintentos
        if ($error ne $entry) {
            print STDERR "\t* ERROR: [$error] $i ... reintentando envio...\n";
            # Intenta reestablecer la conexion con el servidor.
            $coneccionFTP->quit();
            my ($ret, $filler) = &ftp_connect($ipServer, $userServer, $passServer, ''); # al reconectarse sigue usando el mismo ofset anterior
            if (ref $ret) { # coneccion y login ok
                $coneccionFTP = $ret;
                $reconectado = 1;
            } else {
                # Si no se puede conectar o loguear, no reintenta en el envio
                print STDERR $ret;
                last;
            };
        };
        # exit; # debug para transmitir un solo archivo
        $i++;
    } until (($i > 10) || ($error eq $entry));  # Intenta hasta 10 veces o hasta que no de error.

    # Cierra conexion local si se tuvo que reconectar ya que esta coneccion no es reutilizable para otros hijos.
    $coneccionFTP->quit() if ($reconectado);

    if ($error eq $entry) {
        print STDERR "\tTransmitido Ok [...$entry]\n" if ($CLUSTERING_DEBUG_LEVEL >=1);
    };

    # Se alcanzo el max de reintentos sin exito
    if ($i > 10) {
        print STDERR "\t* Server[$ipServer][$userServer]: No se pudo transmitir Local:[$localDir][$entry] a [$remote_dir], 10 reintentos agotados.\n";
    };

}; # write_ftp_file

# ---------------------------------------------------------------
sub ftp_connect {
    my ($ipServer, $userServer, $passServer, $docRoot) = @_;
    my $ftp_debug = 0;
    sleep 1;
    my $stamp = &glib_hrfec_02::get_dtime_pack4();
    print STDERR "[" . $stamp . "]" . "Iniciando ftp_connect...\n";
    $ftp_debug = 1 if ($CLUSTERING_DEBUG_LEVEL >=2);
    my $ftp = Net::FTP->new($ipServer,Timeout=>$CLUSTERING_TIMEOUT_CONNECT_SEGS,Debug=>$ftp_debug,Passive=>1) or return ("\t* $stamp - FTP a [$ipServer][$userServer]... No se puede conectar con el servidor, timeout[$CLUSTERING_TIMEOUT_CONNECT_SEGS]segs, modo[Pasivo] : $@\n");
    my $ret;
    $ret = $ftp->login($userServer,$passServer);
    if (!$ret) {
        my $errMsg = $ftp->message; # incluye un \n al final
        $ftp->quit();
        return("\t* FTP a [$ipServer][$userServer]... Falla login : " . $errMsg);
    };


    $ret = $ftp->cwd('/');
    if (!$ret) {
        my $errMsg = $ftp->message;
        $ftp->quit();
        return("\t* FTP a [$ipServer][$userServer]... Falla cwd('/') : " . $errMsg);
    };

    $ret = $ftp->binary();
    if (!$ret) {
        my $errMsg = $ftp->message;
        $ftp->quit();
        return("\t* FTP a [$ipServer][$userServer]... Falla binary() : " . $errMsg);
    };

    # Calcula Offset de reloj de este server
    my $offset;
    if ($docRoot) {
        my $localDirTest = $docRoot;
        my $archTest = "ftp_check_offset_" . $$ . ".$ipServer.$userServer.txt";

        # Escribe arch local
        open (ARCHIVO, ">$localDirTest/$archTest")
          || die "\t* ERROR  al escribir archivo local [$localDirTest/$archTest] para calcular offset, aborta ejecucion del script.\n $!\n";
        binmode ARCHIVO;
        print ARCHIVO 'test';
        close ARCHIVO;

        # Escribe arch remoto
        $ret = $ftp->put("$localDirTest/$archTest");
        if (!$ret) {
            unlink "$localDirTest/$archTest";
            my $errMsg = $ftp->message;
            $ftp->quit();
            return("\t* FTP a [$ipServer][$userServer][$passServer]... Obtener Offset: Falla put( $localDirTest/$archTest ) : " . $errMsg);
        };
        my $rTime;
        $rTime = $ftp->mdtm($archTest) || ($rTime = 0); # !$rTime implica que el arch. remoto no existe
        if (!$rTime) {
            unlink "$localDirTest/$archTest";
            my $errMsg = $ftp->message;
            $ftp->quit();
            return("\t* FTP a [$ipServer][$userServer]... Obtener Offset: Falla mdtm( $archTest ) : " . $errMsg);
        };
        my $lTime = (stat("$localDirTest/$archTest"))[9];
        $offset = $lTime - $rTime;

        print STDERR "Offset inicial  lTime[$lTime] rTime[$rTime] offset[$offset] file[$archTest]\n";


        # Borra el archivo usado para obtener offset.
        $ftp->delete($archTest);

        unlink "$localDirTest/$archTest";
    };
    print STDERR "\n--------------------------------\n";
    my $msg = "FTP a [$ipServer][$userServer]... Nueva conexion establecida Ok ";
    $msg .= " / OFFSET [$offset]segs" if ($offset);
    $msg .= "\n";
    print STDERR $msg if ($CLUSTERING_DEBUG_LEVEL >=1);


    return ($ftp, $offset);
};

#-----------------------------------------------------------------------
sub abreLogServer {
# Abre un log dedicado para un server especifico, con duracion maxima de acuerdo a CLUSTERING_LOG_DURATION_SEGS
    my ($ipServer, $userServer) = @_;

    my $pesoscero = $0;
    if ($pesoscero =~ /(\w+\.\w+)$/) {
        $pesoscero = $1;
    };

    use FindBin '$Bin';

    my $pid = $$;
    my $archLog = "$Bin/prontus_temp/$pesoscero.error.log";
    $archLog = "$Bin/prontus_temp/$pesoscero.error.$ipServer.$userServer.log" if ($ipServer);

    my $modoOPEN = ">>";

    if (&lib_prontus::arch_antiguo($archLog, $CLUSTERING_LOG_DURATION_SEGS)) {
        $modoOPEN = ">";
    };
    open (STDERR, "$modoOPEN$archLog");

};


# ---------------------------------------------------------------
sub salir {
    my $msg = $_[0];
    print STDERR "$msg\n";
    exit;
};

# ---------------------------------------------------------------
1;
# -------------------------------END LIBRERIA--------------------
