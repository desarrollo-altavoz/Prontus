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
# Realiza efectivamente la transcodificacion de un video de avi, wmv, mp4, mpeg, rm y otros a mp4.
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
#
# /usr/bin/perl prontus_videodoxcode.cgi /sites/prontus_lab/web/prontus_proto/site/artic/20100531/mmedia/multimedia_video120100531182139.avi prontus_proto
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------
# 1.0.0 - 31/05/2010 - Primera version.
# 1.1.0 - 10/09/2012 - EAG - Se agrega deteccion del tipo de codec usado, si el audio es aac o mp3 no se reencodea el audio
#                            Si el video tiene ancho menor a 640 y el codec es h264 baseline no se reencodea el video
# 1.2.0 - 08/10/2012 - EAG - Se agrega nice al momento de transcodificar
# 1.3.0 - 19/10/2012 - EAG - Se corrige bug en el comando de transcodificación
# 1.4.0 - 26/10/2012 - EAG - Se transcodifica cualquier audio excepto AAC.
# 1.5.0 - 05/03/2013 - EAG - Se agrega variable prontus para parametros de transcodificación.
# 1.6.0 - 13/08/2013 - JOR - Cambia main, estaba mal implementado.
#                          - Agrega logeo de STDERR, ya que ahora este script corre en background.
#                          - Ordena codigo.
#                          - Cambia algunas funciones a lib_xcoding.
# 2.0.0 - 20/03/2014 - EAG - Se agrega transcodificación para mp4.
# 2.1.0 - 31/03/2014 - EAG - Se modifica el momento en el que se ajusta el mp4, se determina una vez los parametros del video
# 2.2.0 - 31/03/2014 - EAG - Se agrega limite para transcodificar audio aac
# 2.2.1 - 03/10/2014 - EAG - Se convierte cgi a utf8 y agrega use utf8;
# 2.3.0 - 06/10/2014 - EAG - Se agrega la generacion de HLS.
#                          - Se corrige un bug en el paso de parámetros a x264
#                          - Se revisan los parametros usado, se eliminan de listado los que corresponden a valores por defecto
#                          - Se modifica el uso de formatos.cfg, se restructuran los parametros
# 2.3.1 - 24/10/2014 - EAG - Se modifica la generacion de HLS para siempre procesar el audio
# 2.4.0 - 27/10/2014 - EAG - Se agrega purge para los archivos HLS generados
#                          - Se agrega la opcion de redefinir los aprametros por defecto desde formatos.cfg,
#                            sin que sea una version del video original
# 2.4.1 - 28/10/2014 - EAG - Se evita que la lista generada contenga la misma resolucion 2 veces
#                            Se aplican etiquetas para anchos definidos
# 2.4.2 - 26/11/2014 - EAG - Se corrige bug que no eliminaba el video original si no era mp4.
#                            Se corrige bug al pasar el formato original
# 2.4.3 - 27/11/2014 - EAG - Se agrega la opcion para saltarse el primer paso al codificar las versiones
# 2.4.4 - 28/11/2014 - EAG - Se agrega la creacion de un temporal con el video orignal para usar al crear todas las versiones
#                            Se modifica la forma en la que se hacen las versiones
# 2.4.5 - 03/12/2014 - EAG - Se agrega transcodificacion en paralelo para generar versiones de los videos
# 2.4.6 - 11/05/2015 - EAG/JOR - Integracion soporte dropbox
# 2.4.7 - 12/05/2015 - EAG - Modificaciones por integracion a la release
# 2.4.8 - 28/05/2015 - EAG - Agrega hora inicio y fin al STDERR
# 2.4.9 - 01/06/2015 - EAG - Se agregan etiquetas adicionales para las resoluciones "estandar"
# 2.4.10 - 03/06/2015 - EAG - Se agrega verificacion al hacer garbage, RUTA_PRONTUS no puede ser vacio
# 2.5.0 - 04/06/2015 - EAG - Se mejora compatibilidad con ffmpeg 1.x
# ---------------------------------------------------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/xcoding$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};
# ---------------------------------------------
END {
    &garbageTempFiles();
};

use sigtrap 'handler' => \&signal_catch, 'INT';
use sigtrap 'handler' => \&signal_catch, 'TERM';

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use File::Copy qw(copy);
use POSIX qw(ceil);
use lib_prontus;
use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use glib_hrfec_02;
use lib_xcoding;
use strict;
use Artic;
use File::Copy;
use utf8;
use Data::Dumper;

my $ORIGEN = $ARGV[0];
my $PRONTUS_ID = $ARGV[1];
my $GENERAR_VERSIONES = $ARGV[2];
my $ARTIC_dirfecha;
my $ARTIC_ts_articulo;
my $ARTIC_path_xml;
my $ARTIC_filename = '';
my $ARTIC_extension;
my $RUTA_PRONTUS = '';  # ruta de la carpeta prontus donde esta el video en caso de no usar ruta temporal
my %FORMATOS_VERSIONES; # hash que guarda los formatos de las versiones del video
my $VERSIONS_FILE = ''; # archivo temporal para crear las versiones del video original
my $MARCA; # nombre de la marca prontus del video

# ---------------------------------------------------------------
main: {
    &die_stderr("El parámetro 'origen' no es válido.", "", 1) if ((!-f "$ORIGEN") || (!-s "$ORIGEN"));
    &die_stderr("El parámetro 'prontus_id' no es válido.", "", 1) if (! &lib_prontus::valida_prontus($PRONTUS_ID));
    &die_stderr("El parámetro 'prontus_id' no es válido.", "", 1) if (!-d "$prontus_varglb::DIR_SERVER/$PRONTUS_ID");

    $GENERAR_VERSIONES = 0 if (!$GENERAR_VERSIONES);
    my ($cmd, $res);
    my ($start, $total, $segundos);
    $start = time; # tiempo inicial para medir la duracion del proceso

    if (!&load_artic_info()) {
        &die_stderr("No se obtener la información del artículo asociado al video.", "", 1);
    };

    $ORIGEN =~ /\/mmedia\/(multimedia_video\d+)\d{14}\.(\w+)$/i;
    $MARCA = $1;

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$PRONTUS_ID/cpan/$PRONTUS_ID.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);  # Prontus 6.0
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

    print STDERR "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] [$ARTIC_filename] Inicio Proceso\n";

    # se inicializa el uso de libfdk_aac, es comun para ambos metodos
    if ($prontus_varglb::USAR_LIB_FDK eq 'SI') {
        $lib_xcoding::FDK = 1;
    }

    if ($prontus_varglb::ADVANCED_XCODING eq 'NO') { # transcodificacion basica
        if ($GENERAR_VERSIONES) {
            &crear_versiones_video_v1($MARCA, $ORIGEN);
            exit;
        };

        # No transcodifica peliculas que ya son mp4.
        # Sin embargo, se aplica la correccion de los headers y offset, moviendolo al comienzo
        if ($ORIGEN =~ /\.mp4$/i) {
            print STDERR "* No transcodifican peliculas que ya son mp4.\n";
            print STDERR "* Moviendo las cabeceras al comienzo.\n";

            $cmd = "$Bin/qtfaststart.cgi $ORIGEN";
            $res = qx/$cmd 2>&1/;

            &die_stderr("Falló Ajuste de Mp4.", "[$!][$res]", 1) if ($? != 0);
            &die_stderr("El video no necesita conversión.\n", "", 0);
        };

        # Forma el nombre de la pelicula destino sustituyendo la extension... lo borra si existe.
        my $destino = $ORIGEN;
        $destino =~ s/\.\w+$/\.mp4/;
        if (-f $destino) {
            unlink $destino;
        };

        &do_xcode_v1($ORIGEN, $destino);

        # Crear versiones adicionales del video.
        &crear_versiones_video_v1($MARCA, $destino);
    } elsif ($prontus_varglb::ADVANCED_XCODING eq 'SI') { # transcodificacion avanzada
        # Forma el nombre de la pelicula destino sustituyendo la extension
        my $destino = $ORIGEN;
        $destino =~ s/\.\w+$/\.mp4/;

        # para obtener la carpeta prontus del video
        $destino =~ /(\/.*\/\d{8}\/mmedia\/)multimedia_video.*\d{6}\S?\.\w+$/;
        $RUTA_PRONTUS = $1;
        #~ print STDERR "RUTA_PRONTUS [$RUTA_PRONTUS]\n";

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
        # se resta 1 para descontar el proceso actual
        $lib_xcoding::MAX_PARALELO = $prontus_varglb::XCODE_MAX_PARALELO - 1;

        #se obtienen los datos del video original
        ($lib_xcoding::ANCHO, $lib_xcoding::ALTO, $lib_xcoding::VCODEC, $lib_xcoding::ACODEC, $lib_xcoding::VBITRATE, $lib_xcoding::ABITRATE) = &lib_xcoding::get_info_video($ORIGEN);

        # cargamos los formatos para la marca para saber si hay que generar versiones y
        # necesitamos conservar el archivo original o no
        %FORMATOS_VERSIONES = &lib_xcoding::get_formatos($MARCA);

        if ($GENERAR_VERSIONES) {
            #~ print STDERR "generar versiones\n";
            if (scalar(keys %FORMATOS_VERSIONES) > 0) {
                &crear_versiones_video($MARCA, $ORIGEN, $destino);
            }
            # si es modo paralelo debemos esperar que terminen los otros procesos
            if ($lib_xcoding::MODO_PARALELO) {
                &esperar_procesos();
            }
            # Actualizar articulo.
            &actualizar_articulo($MARCA, 1);
            if ($lib_xcoding::HLS) {
                &generar_lista_HLS($destino);
            }
            $total = time - $start;
            $segundos = $total % 60;
            $segundos = $segundos < 10? '0'.$segundos : $segundos;
            print STDERR "[$ARTIC_filename] Tiempo Total Transcodificacion [".int($total/60) .":". $segundos ."]\n";

            # si esta definido un post proceso lo ejecutamos en segundo plano
            if ($prontus_varglb::XCODING_PPROC ne '') {
                system("$prontus_varglb::XCODING_PPROC $PRONTUS_ID $ARTIC_ts_articulo >/dev/null 2>&1 &");
            }
            exit;
        };

        # Se transcodifican mp4s si el bitrate de video es muy alto
        # Sin embargo, se aplica la correccion de los headers y offset, moviendolo al comienzo
        if ($ORIGEN =~ /\.mp4$/i) {
            if ($lib_xcoding::VBITRATE <= $lib_xcoding::MAX_VRATE && $lib_xcoding::ABITRATE <= $lib_xcoding::MAX_ARATE && !$lib_xcoding::HLS) {
                print STDERR "* No se transcodifican peliculas que ya son mp4 con bitrate no muy alto.\n";
                print STDERR "* Moviendo las cabeceras al comienzo.\n";

                $cmd = "$Bin/qtfaststart.cgi $ORIGEN";
                $res = qx/$cmd 2>&1/;

                &die_stderr("Falló Ajuste de Mp4.", "[$!][$res][$cmd]", 1) if ($? != 0);
                &die_stderr("El video no necesita conversión.\n", "", 0);
            }
        };

        # si hay formatos > 0 copiamos el archivo original para usarlo al generar las versiones
        # para no tener que realizar un nuevo analisis para transcodificar
        # si no hay directorio de trabajo se guarda en la misma ubicacion del original
        if ($lib_xcoding::RUTA_TEMPORAL eq '')  {
            $VERSIONS_FILE = "$RUTA_PRONTUS$ARTIC_filename.prontustmp";
        } else {
            # si hay directorio de trabajo se guarda ahi
            $VERSIONS_FILE = "$lib_xcoding::RUTA_TEMPORAL$ARTIC_filename.prontustmp";
        }
        if (scalar(keys %FORMATOS_VERSIONES) > 0) {
            # si existe el archivo temporal, se borra
            if (-e $VERSIONS_FILE) {
                unlink $VERSIONS_FILE;
            }
            copy($ORIGEN, $VERSIONS_FILE) or &die_stderr("Fallo la copia del original a $VERSIONS_FILE", "[$!][$res].", 1) ;
        }

        # cargamos los formatos por defecto si estan redefinidos
        my %formatos = &lib_xcoding::get_formatos($MARCA, 1);
        # realizamos la transcoficacion del original
        &do_xcode($ORIGEN, $destino, 0, $formatos{uc $MARCA}, ''); # $key es vacio

        # si existe el mp4
        if (-s $destino) {
            # Actualizamos el articulo  articulo. solo guardamos el xml en el articulo.
            &actualizar_articulo($MARCA, 0);
            # para obtener la carpeta prontus relativa del video
            $destino =~ /\/.*(\/.*?\/site\/\w+\/\d{8}\/mmedia\/multimedia_video.*\d{6}\S?\.\w+)$/;
            &lib_prontus::purge_cache($1);
        } else {
            # sino terminamos
            &die_stderr("Ha ocurrido un error al generar [$destino].\n", "", 1);
        }

        # segmentamos el video para generar HLS
        if ($lib_xcoding::HLS) {
            &lib_xcoding::generar_HLS($destino);
        }

        # si no es modo paralelo se procesan las versiones
        if (!$lib_xcoding::MODO_PARALELO) {
            # si hay formatos para versiones generamos las versiones indicadas
            if (scalar(keys %FORMATOS_VERSIONES) > 0) {
                # se obtienen los datos del video creado para generar las versiones de este
                ($lib_xcoding::ANCHO, $lib_xcoding::ALTO, $lib_xcoding::VCODEC, $lib_xcoding::ACODEC, $lib_xcoding::VBITRATE, $lib_xcoding::ABITRATE) = &lib_xcoding::get_info_video($destino);

                # Crear versiones adicionales del video.
                &crear_versiones_video($MARCA, $VERSIONS_FILE, $destino);
            }
        } else {
            # si es modo paralelo debemos esperar que terminen los otros procesos
            &esperar_procesos();
        }

        if ($lib_xcoding::HLS) {
            &generar_lista_HLS($destino);
        }
    } else {
        # salimos sin hacer nada
        &die_stderr("Ha ocurrido un error al transcodificar, el valor de ADVANCED_XCODING es incorrecto [$prontus_varglb::ADVANCED_XCODING].\n", "", 1);
    }

    # Actualizar articulo.
    &actualizar_articulo($MARCA, 1);

    $total = time - $start;
    $segundos = $total % 60;
    $segundos = $segundos < 10? '0'.$segundos : $segundos;
    print STDERR "[$ARTIC_filename] Tiempo Total Transcodificacion [".int($total/60) .":". $segundos ."]\n";

    # si esta definido un post proceso lo ejecutamos en segundo plano
    if ($prontus_varglb::XCODING_PPROC ne '') {
        system("$prontus_varglb::XCODING_PPROC $PRONTUS_ID $ARTIC_ts_articulo >/dev/null 2>&1 &");
    }
};
# ---------------------------------------------------------------
# determina cuantos procesos en paralelo estan corriendo para este video
sub cuenta_procesos {
    my $origen =  $_[0];
    my $res = `ps auxww |grep 'prontus_videoxcodeparallel.cgi $origen' | grep -v grep | wc -l`;
    #~ print STDERR "cuenta_procesos [$res]\n";
    if ($res eq '') {
        return 0;
    } else {
        return $res + 0;
    }
}
# ---------------------------------------------------------------
# espera que terminen los procesos que estan corriendo en background
sub esperar_procesos {
    # si es modo paralelo debemos esperar que terminen los otros procesos
    while (1) {
        my $res = `ps auxww |grep 'prontus_videoxcodeparallel.cgi' | grep $PRONTUS_ID | grep $ARTIC_filename |grep -v grep | grep -v tail`;
        #~ print STDERR "[$res]\n";
        # si ya no hay procesos corriendo terminamos
        if ($res eq '') {
            last;
        }
        # esperamos segundos antes de volver a chequear
        sleep(5);
    }
}
# ---------------------------------------------------------------
sub crear_versiones_video {
    my $marca = $_[0];
    my $origen = $_[1];
    my $destino = $_[2];

    print STDERR "Creando versiones [$marca]...\n";

    foreach my $key (sort keys(%FORMATOS_VERSIONES)) {
        # si estamos procesando en modo paralelo se lanzan las versiones en background
        if ($lib_xcoding::MODO_PARALELO) {
            while (&cuenta_procesos($origen) > $lib_xcoding::MAX_PARALELO) {
                # print STDERR "Muchos procesos, esperando...\n";
                # esperamos que termine algun proceso antes de lanzar mas
                sleep(10);
            };
            my $cmd = "$lib_xcoding::PATHNICE /usr/bin/perl $Bin/prontus_videoxcodeparallel.cgi $origen $PRONTUS_ID $key $RUTA_PRONTUS";
            print STDERR "Transcodificando en Paralelo [$origen $key]\n";
            system("$cmd >/dev/null 2>&1 &");
        } else {
            my $new_name = $key;
            $new_name =~ s/\./$ARTIC_ts_articulo/sg;
            $new_name = lc $new_name;
            my $new_destino = $destino;
            $new_destino =~ s/\/multimedia_video\d+\d{14}\.(\w+)$/\/$new_name\.mp4/is;
            print STDERR "Procesando formato [$key] => [$new_destino]\n";

            if (-f $new_destino) {
                unlink $new_destino;
            };
            &do_xcode($origen, $new_destino, 1, $FORMATOS_VERSIONES{$key}, $key);
            # para obtener la carpeta prontus relativa del video
            $new_destino =~ /\/.*(\/.*?\/site\/\w+\/\d{8}\/mmedia\/multimedia_video.*\d{6}\S?\.\w+)$/;
            # purgeamos el archivo
            &lib_prontus::purge_cache($1);
            # segmentamos el video para generar HLS
            if ($lib_xcoding::HLS) {
                &lib_xcoding::generar_HLS($new_destino);
            }
        }
    };
};
# ---------------------------------------------------------------
sub do_xcode {
    my $origen = $_[0];
    my $destino = $_[1];
    my $no_borr_origen = $_[2];
    my $formato = $_[3];
    my $key = $_[4];

    # obtenemos y guardamos el nombre de la marca
    $key =~ /\.(\w+)$/;
    $key = lc $1;

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
    my %formato_defecto = &lib_xcoding::get_formatos($MARCA, 1);

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
        print STDERR "Perfil de version [$MARCA".uc($key)."] es distinto de la version principal [$perfil_defecto] != [$perfil_formato]\n";
        $paso_1 = 1;
    }

    my $nuevolog = 0;
    # si no hay que hacer 2 pasos se procesa siempre
    # o si hay que hacer 2 pasos y ya existe el log de estadisticas nos saltamos el paso 1
    # $stats_file-0.log es el log que genera ffmpeg 1
    #~ if (!$nd_pass || !($nd_pass && (-s $stats_file))) {
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
        &die_stderr("Falló transcodificación", "[$!][$res].", 1) if ($? != 0);
    }

    # si no hay que borrar el origen, se esta haciendo el video principal
    # despues del analisis podemos lanzar las versiones en paralelo
    if (!$no_borr_origen && $lib_xcoding::MODO_PARALELO) {
        &crear_versiones_video($MARCA, $VERSIONS_FILE, $destino);
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
        &die_stderr("Falló transcodificación", "[$!][$res].", 1) if ($? != 0);
    }

    #si el archivo de destino existe, lo borramos
    if (-f $destino) {
        unlink $destino;
    };

    #si existe ruta temporal de trabajo se mueve el archivo a su destino final
    if ($lib_xcoding::RUTA_TEMPORAL ne '')  {
        #se ajusta el mp4
        $cmd = "$Bin/qtfaststart.cgi $lib_xcoding::RUTA_TEMPORAL$archivo_destino";
        $res = `$cmd 2>&1`;

        &die_stderr("1 Falló Ajuste de Mp4.", "[$!][$res][$cmd]", 1) if ($? != 0);

        # se mueve el mp4 a su destino final
        move("$lib_xcoding::RUTA_TEMPORAL$archivo_destino",$destino);
    } else {
        #se ajusta el mp4
        $cmd = "$Bin/qtfaststart.cgi $RUTA_PRONTUS$archivo_destino";
        $res = `$cmd 2>&1`;

        &die_stderr("2 Falló Ajuste de Mp4.", "[$!][$res][$cmd]", 1) if ($? != 0);

        #sino se renombra de tmp a mp4
        rename("$RUTA_PRONTUS$archivo_destino",$destino);
    }

    if (-f $destino) {
        #se borra el original si no es mp4, si es mp4 en esta etapa ya es el destino
        unlink $ORIGEN if (!$no_borr_origen && $ORIGEN !~ /\.mp4$/i );
    } else {
        &die_stderr("El archivo de destino no se genero correctamente.", "", 1);
    };
};
# ---------------------------------------------------------------
# genera la playlist que contiene las listas de las variantes del video
sub generar_lista_HLS {
    my ($ancho, $alto, $vcodec, $acodec, $vbitrate, $abitrate, $fps, $duration, $fullpath, $hlspath);
    my $list = "#EXTM3U\n#EXT-X-VERSION:3\n";
    my @archivos  = glob "$RUTA_PRONTUS$ARTIC_filename*";
    @archivos = sort @archivos;
    my $ult_resolucion = '';

    foreach my $archivo (@archivos) {
        # se busca la informacion del mp4 asociado
        # /var/www/prontus_development/prontus_develop/site/artic/20140814/mmedia/multimedia_video120140814172639.mp4
        if ($archivo !~ /(\/.*(\/[^\/]+\/[^\/]+\/[^\/]+\/\d{8}\/mmedia\/multimedia_video\d+\d{14}\S*))\.mp4$/) {
            next;
        }
        $hlspath = $2;
        $fullpath = $1;

        if (-s "$fullpath/playlist.m3u8") {
            # se obtienen los datos del video para usar en la lista
            ($ancho, $alto, $vcodec, $acodec, $vbitrate, $abitrate, $fps, $duration) = &lib_xcoding::get_info_video($archivo);
            if ($ult_resolucion ne "$ancho"."x$alto") {
                $list .= "#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=". 1100*($vbitrate +$abitrate).",RESOLUTION=$ancho"."x$alto";
                # etiquetas para las resoluciones estandar
                if ($ancho == 1920) {
                    $list .= ",NAME=\"1080p\"";
                } elsif ($ancho == 1280) {
                    $list .= ",NAME=\"720p\"";
                } elsif ($ancho == 854) {
                    $list .= ",NAME=\"480p\"";
                } elsif ($ancho == 640) {
                    $list .= ",NAME=\"360p\"";
                } elsif ($ancho == 426) {
                    $list .= ",NAME=\"240p\"";
                }
                $list .= "\n$hlspath/playlist.m3u8\n";
                $ult_resolucion = "$ancho"."x$alto";
            }
        }
    }

    my $filename = "$RUTA_PRONTUS$ARTIC_filename.mp4.m3u8";
    glib_fildir_02::write_file($filename, $list);
    if ($filename =~ /.*(\/.*?\/site\/mm\/\d{8}\/mmedia\/multimedia_video\d+\S?.*)/) {
        &lib_prontus::purge_cache($1);
    }
}
# ---------------------------------------------------------------
# funcion para capturar las señales INT y TERM y logearlas
sub signal_catch {
    print STDERR  "Terminado por señal @_\n";
    exit(0);
}
# ---------------------------------------------------------------
# borra los archivos temporales asociados a la transcodificacion.
sub garbageTempFiles {
    #borramos los logs de multipasos y archivos temporales que pudieran quedar
    my @logs;
    if ($ARTIC_filename ne '')  {
        if ($lib_xcoding::RUTA_TEMPORAL ne '')  {
            @logs = glob "$lib_xcoding::RUTA_TEMPORAL$ARTIC_filename*";
        } elsif ($RUTA_PRONTUS ne '') {
            @logs = glob "$RUTA_PRONTUS$ARTIC_filename*";
        }
        foreach my $log (@logs) {
            # no se borran:
            # 1.- archivo mp4, es el resultado de la transcodificacion
            # 2.- directorio con el mismo nombre, es el directorio de HLS
            # 3.- si es igual al origen, indica problema de trancodificacion
            if ($log =~ /\.mp4$/ || $log =~ /\.m3u8$/ || -d $log || $log eq $ORIGEN) {
                #~ print STDERR "no borrar $log\n";
                next;
            }

            print STDERR "Borrando archivo $log\n";
            unlink $log;
        }

        #~ print STDERR Dumper(\@logs);
    } else {
        print STDERR "ARTIC_filename vacío, no se hace nada \n";
    }
    print STDERR "[".&glib_hrfec_02::fecha_human()." ". &glib_hrfec_02::hora_human()."] [$ARTIC_filename] Fin Proceso\n";
}
# ---------------------------------------------------------------
sub actualizar_articulo {
    my $marca = $_[0];
    my $generar_actualizar_dam = $_[1];

    my $artic_obj = Artic->new(
                'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                'public_server_name'=> $prontus_varglb::PUBLIC_SERVER_NAME,
                'cpan_server_name'  => $prontus_varglb::IP_SERVER,
                'document_root'     => $prontus_varglb::DIR_SERVER,
                'ts'                => $ARTIC_ts_articulo,
                'campos'=>{}) || return "Error inicializando objeto articulo: $Artic::ERR TS[$ARTIC_ts_articulo]";

    my $parse_as_cdata = '';
    my $xml_base = &glib_fildir_02::read_file($artic_obj->{fullpath_xml});
    $xml_base = &lib_prontus::replace_in_xml($xml_base, $marca, "$ARTIC_filename.mp4", $parse_as_cdata);
    $artic_obj->{xml_data} = $xml_base;
    $artic_obj->_flush_xml();

    if ($generar_actualizar_dam) {
        # Generar vista (a partir del xml)
        $artic_obj->generar_vista_art('', '', $prontus_varglb::PRONTUS_KEY) || return $Artic::ERR;

        my %datos = &lib_prontus::getCamposXml($xml_base, '_fid,_plt');
        my $fid = $datos{'_fid'};
        my $plt = $datos{'_plt'};

        # Parsear plantillas paralelas.
        my @plt_paralelas_list = split(/;/, $prontus_varglb::FORM_PLTS_PARALELAS{$fid});
        foreach my $plt_paralela (@plt_paralelas_list)  {
            $artic_obj->generar_vista_art('', '', $prontus_varglb::PRONTUS_KEY, $plt_paralela, 1) || return $Artic::ERR;
        };

        # Generar vistas secundarias
        foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
            $artic_obj->generar_vista_art($mv, '', $prontus_varglb::PRONTUS_KEY) || return $Artic::ERR;
        };

        # Actualizar el DAM
        my $ext = &lib_prontus::get_file_extension($plt);
        my $fullpath_artic = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/site/artic/$ARTIC_dirfecha/pags/$ARTIC_ts_articulo.$ext";
        use FindBin '$Bin';
        my $rutaScript = $Bin;
        $rutaScript =~ s/\/[^\/]+$//;
        my $cmd = "$rutaScript/dam/prontus_dam_ppart_save.cgi $fullpath_artic $prontus_varglb::PUBLIC_SERVER_NAME &";
        print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
        system $cmd;
    }

    # Dropbox.
    &call_dropbox_backup($ARTIC_ts_articulo);

    return '';
};
# ---------------------------------------------------------------
sub call_dropbox_backup {
    my $ts = $_[0];

    if ($prontus_varglb::DROPBOX eq 'SI') {
        &lib_prontus::dropbox_backup("art;$ts");
    };
};
# ---------------------------------------------------------------
sub load_artic_info {
    # Deduce ubicacion del xml del articulo.
    if ($ORIGEN =~ /(.+)\/(.*?)\/(\d{8})\/mmedia\/(multimedia_video.+?(\d{6}))\.(\w+)$/) {
        $ARTIC_dirfecha = $3;
        $ARTIC_ts_articulo = $3 . $5;
        $ARTIC_path_xml = $1 . $prontus_varglb::DIR_ARTIC . '/'. $3 .'/xml/'. $ARTIC_ts_articulo . '.xml';
        $ARTIC_filename = $4;
        $ARTIC_extension = $6;

        return 1;
    } else {
        return 0;
    };
};
# ---------------------------------------------------------------
sub die_stderr {
    my $msg = $_[0];
    my $detalle = $_[1];
    my $write = $_[2];
    &write_status($msg) if ($write);
    print STDERR "[ERROR] $msg - $detalle";
    exit 1;
};
# ---------------------------------------------------------------
sub write_status {
    my $msg = $_[0];
    $msg =~ s/\n//sg;
    my $file = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/procs/xcoding_status_$ARTIC_ts_articulo.txt";

    &glib_fildir_02::write_file($file, $msg);
};
# ---------------------------------------------------------------
# Funciones Legacy para mantener compatibilidad transcodificacion basica
# ---------------------------------------------------------------
sub crear_versiones_video_v1 {
    my $marca = $_[0];
    my $origen = $_[1];

    print STDERR "Creando versiones [$marca]...\n";
    my %formatos = &lib_xcoding::get_formatos_v1($marca);
    foreach my $key (keys(%formatos)) {
        print STDERR "key[$key] formato[$formatos{$key}]\n";
        my $flags = $formatos{$key};
        $key =~ s/\./$ARTIC_ts_articulo/sg;
        $key = lc $key;
        my $new_destino = $origen;
        $new_destino =~ s/\/multimedia_video\d+\d{14}\.(\w+)$/\/$key\.mp4/is;
        print STDERR "new_destino[$new_destino]\n";

        if (-f $new_destino) {
            unlink $new_destino;
        };

        &do_xcode_v1($origen, $new_destino, $flags, 1);
    };
};
# ---------------------------------------------------------------
sub do_xcode_v1 {
    my $origen = $_[0];
    my $destino = $_[1];
    my $flags = $_[2];
    my $no_borr_origen = $_[3];

    my ($cmd, $res);
    $cmd = &lib_xcoding::get_cmd_ffmpeg_v1($origen, $destino, $flags);

    print STDERR "* Transcodificacion [$cmd]\n";

    # Ejecuta la transcodificacion redirigiendo stderr to stdout.
    # Por ahora no se analiza la salida del ffmpeg. La redireccion del stderr al stdout es porque ffmpeg imprime su salida al stderr en vez de al stdout
    $res = qx/$cmd 2>&1/;

    &die_stderr("Falló transcodificación", "[$!][$res].", 1) if ($? != 0);

    $cmd = "$Bin/qtfaststart.cgi $destino";
    $res = qx/$cmd 2>&1/;

    &die_stderr("Falló Ajuste de Mp4", "[$!][$res].", 1) if ($? != 0);

    if (-f $destino) {
        unlink $ORIGEN if (!$no_borr_origen);
    } else {
        &die_stderr("El archivo de destino no se genero correctamente.", "", 1);
    };

};

