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
# 1- ancho
# 2- alto
#
# prontus_videodoxcode.cgi /sites/prontus_lab/web/prontus_proto/site/artic/20100531/mmedia/multimedia_video120100531182139.avi 320 240
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------
# 1.0 - 31/05/2010 - Primera version.
# 1.1 - 10/09/2012 - EAG - Se agrega deteccion del tipo de codec usado, si el audio es aac o mp3 no se reencodea el audio
#                           Si el video tiene ancho menor a 640 y el codec es h264 baseline no se reencodea el video
# 1.2 - 08/10/2012 - EAG - Se agrega nice al momento de transcodificar
# 1.3 - 19/10/2012 - EAG - Se corrige bug en el comando de transcodificación
# 1.4 - 26/10/2012 - EAG - Se transcodifica cualquier audio excepto AAC.
# 1.5 - 05/03/2013 - EAG - Se agrega variable prontus para parametros de transcodificación.
# ---------------------------------------------------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
    $pathLibsProntus =~ s/\/xcoding$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};
use lib_stdlog;
# &lib_stdlog::set_stdlog($0, 51200); # se comenta porque impide que el proceso ppal capture el error de vuelta
use lib_prontus;
use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use glib_hrfec_02;

use strict;
use FindBin '$Bin';

# Para que suelte el stream del server.
close STDOUT;

&main();
exit;

# ---------------------------------------------------------------
sub main {
    my $origen = $ARGV[0];
    my $prontus_id = $ARGV[1];
    &die_stdout("DoXCode: Primer parámetro 'origen' no es válido") if ((!-f "$origen") || (!-s "$origen"));
    &die_stdout("DoXCode: Segundo parámetro 'prontus_id' no es válido") if ($prontus_id !~ /^[\w\-]+$/);
    &die_stdout("DoXCode: Segundo Parámetro ARGV[1] -> 'prontus_id' no es válido") if (!-d "$prontus_varglb::DIR_SERVER/$prontus_id");

    my $cmd;
    my $res;

    # No transcodifica peliculas que ya son mp4.
    # Sin embargo, se aplica la correccion de los headers y offset, moviendolo al comienzo
    if ($origen =~ /\.mp4$/i) {
        print STDERR "\n\nNo transcodifican peliculas que ya son mp4\n"; # para debug
        print STDERR "Moviendo las cabeceras al comienzo\n"; # para debug

        $cmd = "$Bin/qtfaststart.cgi $origen";
        $res = qx/$cmd 2>&1/;

        # print STDERR "\n\n$res"; # para debug
        &die_stdout("Falló Ajuste de Mp4 [$!][$res].") if ($? != 0);
        &die_stdout("\nProceso terminado OK\n");
    };

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$prontus_id/cpan/$prontus_id.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);  # Prontus 6.0
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

    # Verifica que no haya otro transcoding identico en ejecucion.
    # my $res = qx/ps auxww |grep ffmpeg|grep $origen|grep -v grep/;
    # my $res = qx/ps auxww |grep 'prontus_videodoxcode.cgi $origen'|grep -v grep|grep -v $0/;
    # print STDERR "Execution test = [$res]\n";
    # &die_stdout("Hay otro transcoding identico en ejecucion") if ($res ne '');

    # Forma el nombre de la pelicula destino sustituyendo la extension.
    my $destino = $origen;
    $destino =~ s/\.\w+$/\.mp4/;
    unlink $destino;
    # $cmd = "ffmpeg -i $origen -r 25 -s $ancho" . 'x' . "$alto -f mp4 $destino";
    # $cmd = "ffmpeg -i $origen -y -vcodec libx264 -vpre hq -vpre ipod640 -b 700000 -acodec libfaac -ab 128k -f mp4 $destino";
    $cmd = &get_cmd_ffmpeg($origen, $destino);

    print STDERR "\n\n\n*************** NUEVO TRANSCODING:\n$cmd\n\n"; # para debug

    #~ print STDERR "\nProceso terminado FAIL\n";
    #~ exit 1;

    # Ejecuta la transcodificacion redirigiendo stderr to stdout.
    # Por ahora no se analiza la salida del ffmpeg. La redireccion del stderr al stdout es porque ffmpeg imprime su salida al stderr en vez de al stdout
    $res = qx/$cmd 2>&1/;
    # print STDERR "\n\n$res"; # para debug
    &die_stdout("Falló transcodificación [$!][$res].") if ($? != 0);

    # my $ret_chmod = chmod 0755, "$Bin/qtfaststart.pl";
    # $cmd = "$prontus_varglb::DIR_SERVER/cgi-cpn/xcoding/qtfaststart.py $destino";
    $cmd = "$Bin/qtfaststart.cgi $destino";

    $res = qx/$cmd 2>&1/;
    # print STDERR "\n\n$res"; # para debug
    &die_stdout("Falló Ajuste de Mp4 [$!][$res].") if ($? != 0);
    # Elimina el archivo de origen si es que el destino se genero ok
    if (-s $destino) {
        print STDERR "\nProceso terminado OK\n";
        my $ret_reparseo = &procesar_artic($origen);
        print STDERR "\nError al reparsear art: $ret_reparseo\n" if ($ret_reparseo);

    } else {
        print STDERR "\nProceso terminado FAIL\n";
    };
};
# ---------------------------------------------------------------
sub procesar_artic {

    my $origen = shift;

    unlink $origen;
    # Modifica xml de Prontus.
    # Deduce ubicacion del xml del articulo.
    # /sites/prontus_lab/web/prontus_proto/site/artic/20100531/mmedia/multimedia_video120100531182139.avi
    if ($origen =~ /(.+)\/(\d{8})\/mmedia\/(multimedia_video.+?(\d{6}))\.(\w+)$/) {
        my $dirfecha = $2;
        my $ts_articulo = $2 . $4;
        my $path = $1 .'/'. $2 .'/xml/'. $ts_articulo . '.xml';
        my $filename = $3;
        my $extension = $5;
        # print "[$path][$filename][$extension]\n";
        my $buffer = &glib_fildir_02::read_file($path);
        my %camposHash = &lib_prontus::getCamposXml($buffer, '_plt');
        my $plt = $camposHash{'_plt'};

        # print STDERR "\n\n\nbuffer antes[$buffer]\n";
        if ($buffer =~ s/$filename\.$extension/$filename\.mp4/s) {
            # print STDERR "\n\n\nbuffer despues[$buffer]\n";
            &glib_fildir_02::write_file($path, $buffer);
        };

        my $artic_obj = Artic->new(
                    'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                    'public_server_name'=> $prontus_varglb::PUBLIC_SERVER_NAME,
                    'cpan_server_name'  => $prontus_varglb::IP_SERVER,
                    'document_root'     => $prontus_varglb::DIR_SERVER,
                    'ts'                => $ts_articulo,
                    'campos'=>{}) || return "Error inicializando objeto articulo: $Artic::ERR TS[$ts_articulo]";

        # Generar vista (a partir del xml)
        $artic_obj->generar_vista_art('', '', $prontus_varglb::PRONTUS_KEY) || return $Artic::ERR;

        # Generar vistas secundarias
        foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
            $artic_obj->generar_vista_art($mv, '', $prontus_varglb::PRONTUS_KEY) || return $Artic::ERR;
        };

        # Actualizar el DAM
        my $ext = &lib_prontus::get_file_extension($plt);
        my $fullpath_artic = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/site/artic/$dirfecha/pags/$ts_articulo.$ext";
        use FindBin '$Bin';
        my $rutaScript = $Bin;
        $rutaScript =~ s/\/[^\/]+$//;
        my $cmd = "$rutaScript/dam/prontus_dam_ppart_save.cgi $fullpath_artic $prontus_varglb::PUBLIC_SERVER_NAME &";
        print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
        system $cmd;

    } else {
        return "Nombre de archivo no valido: origen[$origen]";
    }
    return '';
};

# ---------------------------------------------------------------
sub get_cmd_ffmpeg {
    my $origen = shift;
    my $destino = shift;
    my @info =`$prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen 2>&1`; # instantaneo
    my ($width, $height);

    my $videoFlags = $prontus_varglb::FFMPEG_PARAMS;
    if ($videoFlags eq '' ) {
        $videoFlags = "-flags +loop -cmp +chroma -partitions +parti8x8+parti4x4+partp8x8+partb8x8 -me_method umh -subq 8 -me_range 16 -keyint_min 25 -sc_threshold 40 -i_qfactor 0.71 -b_strategy 2 -qcomp 0.6 -qmin 10 -qmax 51 -qdiff 4 -directpred 3 -trellis 1 -coder 0 -bf 0 -refs 1 -flags2 -wpred-dct8x8+mbtree -level 30 -maxrate 10000000 -bufsize 10000000 -wpredp 0 -g 25 -b 600000"; #configuracion de compresion, para no utilizar presets ffmpeg
    }

    my ($h264, $baseline,$vcodec,$acodec,$ext);
    print STDERR "$origen \n";
    if ($origen =~ /.+\/\d{8}\/mmedia\/multimedia_video.+?\d{6}\.(\w+)$/) {
        $ext = $1;
        print STDERR "$ext\n";
    }

    foreach (@info) {
        # Video: h264 (Baseline), yuv420p, 1920x1080, 20745 kb/s, 29.97 fps, 29.97 tbr, 600 tbn, 1200 tbc
        if ($_ =~ m/(Video): ([^,]+), (\S+), ([0-9]+)x([0-9]+).+/) {
            if ($1 eq 'Video') {
                print STDERR "Video: [$1] [$2] [$3] [$4] [$5]\n";
                $vcodec = $2;
                $width = $4;
                $height = $5;
            }
        }
        # Audio: aac, 44100 Hz, mono, s16, 62 kb/s
        if ($_ =~ m/(Audio): ([^,]+), ([^,]+), ([^,]+), ([^,]+),.+/) {
            if ($1 eq 'Audio') {
                print STDERR "Audio: [$1] [$2] [$3] [$4] [$5]\n";
                $acodec = $2;
            }
        }
    };

    my $pathnice = &lib_prontus::get_path_nice();

    # si el codec de video es h264 y el perfil es baseline,
    #if ( ($acodec =~ /aac/i || $acodec  =~ /mp3/i) && $vcodec =~ /h264/i && $vcodec =~ /baseline/i) {
    if ($width > 640 || ($width %2 != 0) || ($height %2 != 0) ) {
        my $ancho = $width;
        my $alto = $height;
        if ($ancho > 640) {
            $ancho = 640;
            $alto = int (640*$height/$width);
            if ($alto %2 != 0){
                $alto +=1;
            }
        } else {
            if ($ancho %2 != 0) {
                $ancho += 1;
            }
            if ($alto%2 != 0) {
                $alto += 1;
            }
        }
        print STDERR "ancho[$ancho], alto[$alto]\n";
        if ($acodec =~ /aac/i) {
            return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -s $ancho" . 'x' . "$alto -vcodec libx264 $videoFlags -acodec copy -f mp4 $destino";
        } else {
            return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -s $ancho" . 'x' . "$alto -vcodec libx264 $videoFlags -acodec libfaac -ar 44100 -ab 128k -f mp4 $destino";
        }
    } elsif ($acodec =~ /aac/i && $vcodec =~ /h264/i && $vcodec =~ /baseline/i) {
        return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -vcodec copy -acodec copy -f mp4 $destino";
    } elsif ($acodec =~ /aac/i) {
        return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -vcodec libx264 $videoFlags -acodec copy -f mp4 $destino";
    } else {
        return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -vcodec libx264 $videoFlags -acodec libfaac -ar 44100 -ab 128k -f mp4 $destino";
    };
};
# ---------------------------------------------------------------
sub die_stdout {
    my $msg = shift;
    print STDERR "[ERROR] $msg";
    exit 1;
};
