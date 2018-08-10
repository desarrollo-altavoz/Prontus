#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

#
# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Realiza en paralelo la transcodificacion de un video de avi, wmv, mp4, mpeg, rm y otros a mp4.
# Cuando termina, deduce donde esta el xml del articulo Prontus y modifica las variables.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Al terminar elimina el video original y sustituye el nombre en el xml del articulo Prontus.
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Por linea de comandos.
# Los parametros son:
# 0- Path absoluto al video a transcodificar.
# 1- prontus id
# /usr/bin/perl prontus_videoxcodeparallel.cgi /sites/prontus_lab/web/prontus_proto/site/artic/20100531/mmedia/multimedia_video120100531182139.avi prontus_proto MULTIMEDIA_VIDEO1.B
# my $cmd = "$pathnice /usr/bin/perl $Bin/prontus_videoxcodeparallel.cgi $origen $prontus_id $key";
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------
# 1.0.0 - 02/12/2014 - EAG - Primera version para transcodificacion en paralelo
# 1.1.0 - 12/05/2015 - EAG - Modificaciones por integracion a la release
# 1.2.0 - 04/06/2015 - EAG - Se mejora compatibilidad con ffmpeg 1.x
# 1.2.1 - 16/06/2015 - EAG - Se ordenan los "use"
# 1.2.2 - 15/06/2015 - EAG - Se corrige la aplicacion de lower case a key en do_xcode
# ---------------------------------------------------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/xcoding$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
}
# ---------------------------------------------


use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use utf8;
use File::Copy;
use POSIX qw(ceil);
use lib_prontus;
use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use glib_hrfec_02;
use lib_xcoding;

#~ use Data::Dumper;

my $ORIGEN = $ARGV[0];
my $PRONTUS_ID = $ARGV[1];
my $FORMATO  = $ARGV[2];
my $RUTA_PRONTUS = $ARGV[3]; # ruta de la carpeta prontus donde esta el video en casa de no usar ruta temporal, se obtiene desde la invocacion

my $ARTIC_dirfecha;
my $ARTIC_ts_articulo;
my $ARTIC_path_xml;
my $ARTIC_filename;
my $ARTIC_extension;

# ---------------------------------------------------------------
main: {
    &lib_xcoding::die_stderr("El parámetro 'origen' no es válido.", "", 0) if ((!-f "$ORIGEN") || (!-s "$ORIGEN"));
    &lib_xcoding::die_stderr("El parámetro 'prontus_id' no es válido.", "", 0) if (! &lib_prontus::valida_prontus($PRONTUS_ID));
    &lib_xcoding::die_stderr("El parámetro 'prontus_id' no es válido.", "", 0) if (!-d "$prontus_varglb::DIR_SERVER/$PRONTUS_ID");
    # ejemplo de formato MULTIMEDIA_VIDEO1.B
    &lib_xcoding::die_stderr("El parámetro 'formato' no es válido.", "", 0) if ($FORMATO !~ /(multimedia_video\d+)\.(\w+)/i);

    if (!&load_artic_info()) {
        &lib_xcoding::die_stderr("No se obtener la información del artículo asociado al video.", "", 0);
    }

    # obtenemos el nombre de la marca
    $ORIGEN =~ /.*?\/((multimedia_video\d+)\d{14})\.(\w+)$/i;
    my $marca = $2;

    # armamos la ruta de destino usando el path prontus y el nombre del archivo
    my $destino = $RUTA_PRONTUS . $1 .".mp4";

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$PRONTUS_ID/cpan/$PRONTUS_ID.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);  # Prontus 6.0
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

    # inicializamos los valores de la libreria
    $lib_xcoding::PATHNICE = &lib_prontus::get_path_nice();
    if ($prontus_varglb::GEN_HLS eq 'SI') {
        $lib_xcoding::HLS = 1;
    }
    if ($prontus_varglb::PRECISION_HLS eq 'SI') {
        $lib_xcoding::PRECISION_HLS = 1;
    }
    if ($prontus_varglb::MODO_PARALELO eq 'SI') {
        $lib_xcoding::MODO_PARALELO = 1;
    }
    if ($prontus_varglb::USAR_LIB_FDK eq 'SI') {
        $lib_xcoding::FDK = 1;
    }
    if ($prontus_varglb::N_THREADS =~ /^\d+$/) {
        $lib_xcoding::N_THREADS = $prontus_varglb::N_THREADS;
    }
    $lib_xcoding::MAX_PIXEL = $prontus_varglb::XCODE_MAX_PIXEL;
    $lib_xcoding::MAX_VRATE = $prontus_varglb::MAX_VIDEO_BITRATE;
    $lib_xcoding::MAX_ARATE = $prontus_varglb::MAX_AUDIO_BITRATE;
    $lib_xcoding::RUTA_TEMPORAL = $prontus_varglb::RUTA_TEMPORAL_XCODING;
    $lib_xcoding::RUTA_PRONTUS = $RUTA_PRONTUS;
    $lib_xcoding::ARTIC_filename = $ARTIC_filename;
    $lib_xcoding::ARTIC_ts_articulo = $ARTIC_ts_articulo;

    my ($start, $total, $segundos);
    $start = time;

    # se obtienen los datos del video original
    ($lib_xcoding::ANCHO, $lib_xcoding::ALTO, $lib_xcoding::VCODEC, $lib_xcoding::ACODEC, $lib_xcoding::VBITRATE, $lib_xcoding::ABITRATE) = &lib_xcoding::get_info_video($ORIGEN);

    # cargamos los formatos para la marca generar la version
    my %formatos_versiones = &lib_xcoding::get_formatos($marca);

    # generamos la version
    &crear_version_video($marca, $ORIGEN, $destino, \%formatos_versiones, $FORMATO);

    $total = time - $start;
    $segundos = $total % 60;
    $segundos = $segundos < 10? '0'.$segundos : $segundos;
    print STDERR "[$ARTIC_filename][$FORMATO] Tiempo Total Version [".int($total/60) .":". $segundos ."]\n";
    exit;
}

# ---------------------------------------------------------------
sub crear_version_video {
    my $marca = $_[0];
    my $origen = $_[1];
    my $destino = $_[2];
    my %formatos = %{$_[3]};
    my $key = $_[4];

    my $new_name = $key;
    $new_name =~ s/\./$ARTIC_ts_articulo/sg;
    $new_name = lc $new_name;

    $destino =~ s/\/multimedia_video\d+\d{14}\.(\w+)$/\/$new_name\.mp4/is;
    print STDERR "Procesando formato [$key] => [$destino]\n";

    if (-f $destino) {
        unlink $destino;
    }

    &do_xcode($origen, $destino, 1, $formatos{$key}, $marca, $key);
    # para obtener la carpeta prontus relativa del video
    $destino =~ /\/.*(\/.*?\/site\/\w+\/\d{8}\/mmedia\/multimedia_video.*\d{6}\S?\.\w+)$/;
    # purgeamos el archivo
    &lib_prontus::purge_cache($1);
    # segmentamos el video para generar HLS
    if ($lib_xcoding::HLS) {
        &lib_xcoding::generar_HLS($destino);
    }
}

# ---------------------------------------------------------------
sub do_xcode {
    my $origen = $_[0];
    my $destino = $_[1];
    my $no_borr_origen = $_[2];
    my $formato = $_[3];
    my $marca = $_[4];
    my $key = $_[5];

    # obtenemos y guardamos el nombre de la marca
    if ($key =~ /\.(\w+)$/) {
        $key = lc $1;
    }

    my ($cmd, $res, $nd_pass, $start, $end, $total, $segundos);

    $destino =~ /\/\d{8}\/mmedia\/(multimedia_video.*\d{6}\S?\.mp4)$/;
    my $archivo_destino = $1;
    $archivo_destino =~ s/\.mp4$/\.tmp/;

    ($cmd,$nd_pass) = &lib_xcoding::get_cmd_ffmpeg($origen, $archivo_destino, 0, \%{$formato});

    # se determina la ubicacion del archivo de estadisticas
    my $stats_file = '';
    if ($lib_xcoding::RUTA_TEMPORAL eq '')  {
        $stats_file = "$RUTA_PRONTUS$ARTIC_filename.log";
    } else {
        $stats_file = "$lib_xcoding::RUTA_TEMPORAL$ARTIC_filename.log";
    }

    # cargamos el formato por defecto de la marca para verificar si se cambio el profile
    # si el profile no es main se debe hacer los 2 pasos al transcodificar
    my %formato_defecto = &lib_xcoding::get_formatos($marca, 1);

    my $perfil_defecto = 'main'; # por defecto se usa main
    if (defined($formato_defecto{'H264PROFILE'}) && $formato_defecto{'H264PROFILE'} ne 'main')  {
        $perfil_defecto = $formato_defecto{'H264PROFILE'};
    }

    # verificamos si es main o no
    my $perfil_formato = 'main'; # por defecto se usa main
    if (defined($formato->{'H264PROFILE'}) && $formato->{'H264PROFILE'} ne 'main')  {
        $perfil_formato = $formato->{'H264PROFILE'};
    }

    my $paso_1 = 0;
    # si el perfil de la version principal es distinto al de la version general se debe hacer el paso 1
    if ($perfil_defecto ne $perfil_formato) {
        print STDERR "Perfil de version [".uc("$marca.$key")."] es distinto de la version principal [$perfil_defecto] != [$perfil_formato]\n";
        $paso_1 = 1;
    }

    my $nuevolog = 0;
    # si no hay que hacer 2 pasos se procesa siempre
    # o si hay que hacer 2 pasos y ya existe el log de estadisticas nos saltamos el paso 1
    # $stats_file-0.log es el log que genera ffmpeg 1
    # $paso_1 indica nque el paso 1 debe hacerse sin importar las otras condiciones
    if ((!$nd_pass || !($nd_pass && (-s $stats_file || -s "$stats_file-0.log"))) || $paso_1) {
        # si no existe el archivo de estadisticas debemos crear uno unico para este proceso
        if (!-s $stats_file || $paso_1) {
            # cambiamos el nombre del log en el comando
            $cmd =~ s/\.log/\.log$key/g;
            # hay que usar este log para el paso 2 tambien
            $nuevolog = 1;
        }
        print STDERR "* Transcodificacion paso 1 [$cmd]\n";

        $start = time;
        # Ejecuta la transcodificacion redirigiendo stderr to stdout.
        # Por ahora no se analiza la salida del ffmpeg. La redireccion del stderr al stdout es porque ffmpeg imprime su salida al stderr en vez de al stdout
        $res = `$cmd 2>&1`;

        $end = time;
        $total = $end - $start;
        $segundos = $total % 60;
        $segundos = $segundos < 10? '0'.$segundos : $segundos;
        print STDERR "[$ARTIC_filename] Tiempo FFMPEG [".int($total/60) .":". $segundos ."]\n";
        &lib_xcoding::die_stderr("Falló transcodificación", "[$!][$res].", 1) if ($? != 0);
    }

    # se hace el segundo paso si es necesario
    if ($nd_pass) {
        ($cmd,$nd_pass) = &lib_xcoding::get_cmd_ffmpeg($origen, $archivo_destino, 1, \%{$formato});
        if ($nuevolog) {
            # cambiamos el nombre del log en el comando
            $cmd =~ s/\.log/\.log$key/g;
        }
        print STDERR "* Transcodificacion paso 2 [$cmd]\n";
        $start = time;
        $res = `$cmd 2>&1`;

        $end = time;
        $total = $end - $start;
        $segundos = $total % 60;
        $segundos = $segundos < 10? '0'.$segundos : $segundos;
        print STDERR "[$ARTIC_filename] Tiempo FFMPEG [".int($total/60) .":". $segundos ."]\n";
        &lib_xcoding::die_stderr("Falló transcodificación", "[$!][$res].", 1) if ($? != 0);
    }

    #si el archivo de destino existe, lo borramos
    if (-f $destino) {
        unlink $destino;
    }

    #si existe ruta temporal de trabajo se mueve el archivo a su destino final
    if ($lib_xcoding::RUTA_TEMPORAL ne '')  {
        #se ajusta el mp4
        $cmd = "$Bin/qtfaststart.cgi $lib_xcoding::RUTA_TEMPORAL$archivo_destino";
        $res = `$cmd 2>&1`;

        &lib_xcoding::die_stderr("1 Falló Ajuste de Mp4.", "[$!][$res][$cmd]", 1) if ($? != 0);

        # se mueve el mp4 a su destino final
        move("$lib_xcoding::RUTA_TEMPORAL$archivo_destino",$destino);
    } else {
        #se ajusta el mp4
        $cmd = "$Bin/qtfaststart.cgi $RUTA_PRONTUS$archivo_destino";
        $res = `$cmd 2>&1`;

        &lib_xcoding::die_stderr("2 Falló Ajuste de Mp4.", "[$!][$res][$cmd]", 1) if ($? != 0);

        #sino se renombra de tmp a mp4
        rename("$RUTA_PRONTUS$archivo_destino",$destino);
    }

    if (-f $destino) {
        #se borra el original si no es mp4, si es mp4 en esta etapa ya es el destino
        unlink $ORIGEN if (!$no_borr_origen && $ORIGEN !~ /\.mp4$/i );
    } else {
        &lib_xcoding::die_stderr("El archivo de destino no se genero correctamente.", "", 1);
    }
}

# ---------------------------------------------------------------
sub load_artic_info {
    # Deduce ubicacion datos asociados del video.
    if ($ORIGEN =~ /(.*?)\/(multimedia_video.+?(\d{8})(\d{6}))\.(\w+)$/) {
        #~ print STDERR "[$1] [$2] [$3] [$4] [$5]\n";
        $ARTIC_ts_articulo = $3 . $4;
        $ARTIC_filename = $2;
        return 1;
    } else {
        return 0;
    }
}
