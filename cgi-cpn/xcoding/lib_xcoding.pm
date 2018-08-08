package lib_xcoding;

use glib_fildir_02;
use POSIX qw(ceil);
use strict;

our $HLS = 0;
our $PRECISION_HLS = 0;
our $MODO_PARALELO = 0;
our $MAX_PARALELO = 3;
our $FDK = 0;
our $PATHNICE = '';
our $MAX_PIXEL = '';
our $MAX_VRATE = '';
our $MAX_ARATE = '';
our $RUTA_TEMPORAL = '';
our $RUTA_PRONTUS = '';
our $ARTIC_filename = '';
our $ARTIC_ts_articulo = '';
our $N_THREADS = 0;
our $VBITRATE = 0;
our $ABITRATE = 0;
our $ANCHO = 0;
our $ALTO = 0;
our $VCODEC = '';
our $ACODEC = '';
our $FORMATS_FILE = 'formatos_adv.cfg';
our $XCODING_DATA_PATH = '/cpan/data/xcoding/';

# ---------------------------------------------------------------
# Se leen todas las configuraciones disponibles
sub get_all_formatos {
    my $marca = $_[0];
    my $ts = $_[1];
    my $xcoderFormat = $_[2];
    my %formatos = ();
    my $file_formatos = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID$XCODING_DATA_PATH$FORMATS_FILE";

    if (-f $file_formatos) {
        my $buffer_formatos = &glib_fildir_02::read_file($file_formatos);
        while ($buffer_formatos =~ /\s*(\S+\.?\w*\.)(\w+)\s*=\s*'(.*?)'/ig) {
            if ($3 ne '') {
                my $formatName = $1;
                my $paramName = $2;
                my $value = $3;
                if ($marca ne '') {
                    if ($formatName !~ /^$marca\./i ) {
                        next;
                    }
                }
                if ($xcoderFormat) {
                    $formatName =~ s/\./$ts/;
                    $formatName = lc($formatName);
                    $paramName = lc($paramName);
                    $value = lc($value);
                }
                $formatName =~ s/\.$//;

                if ($xcoderFormat) {
                    $formatName .= '.mp4';
                }
                $formatos{$formatName}{$paramName} = $value;
            }
        }
    }
    return %formatos;
}

# ---------------------------------------------------------------
# Se lee la configuracion por defecto, o lee configuracion para versiones
sub get_formatos {
    my $marca = $_[0];
    my $por_defecto = $_[1];
    my %formatos;
    my $file_formatos = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID$XCODING_DATA_PATH$FORMATS_FILE";

    if ($marca ne '') {
        if (-f $file_formatos) {
            my $buffer_formatos = &glib_fildir_02::read_file($file_formatos);
            if ($por_defecto != 1) {
                while ($buffer_formatos =~ /\s*($marca\.\w+)\.(\w+)\s*=\s*'(.*?)'/ig) {
                    #~ print STDERR "{$1}{$2} = $3;\n";
                    if ($3 ne '') {
                        $formatos{$1}{$2} = $3;
                    }
                }
            } else {
                while ($buffer_formatos =~ /\s*($marca)\.(\w+)\s*=\s*'(.*?)'/ig) {
                    #~ print STDERR "{$1}{$2} = $3;\n";
                    if ($3 ne '') {
                        $formatos{$1}{$2} = $3;
                    }
                }
            }
        }
    }

    return %formatos;
}

# ---------------------------------------------------------------
sub get_info_video {
    my $origen = $_[0];
    my @info =`$prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen 2>&1`;
    my ($width, $height, $vcodec, $acodec, $ext, $vbitrate, $abitrate);

    if ($origen =~ /.+\/\d{8}\/mmedia\/multimedia_video.+?\d{6}\.(\w+)$/) {
        $ext = $1;
    }

    foreach (@info) {
        # Video: h264 (Baseline), yuv420p, 1920x1080, 20745 kb/s, 29.97 fps, 29.97 tbr, 600 tbn, 1200 tbc
        if ($_ =~ m/(Video): ([^,]+), (.*?), ([0-9]+)x([0-9]+)[^,]*, ([^,]+) kb\/s.*/) {
            #~ print STDERR "Video: [$1] [$2] [$3] [$4] [$5] [$6]\n";
            $vcodec = $2;
            $width = $4;
            $height = $5;
            $vbitrate = $6;
        # Video: mpeg4 (Advanced Simple Profile) (XVID / 0x44495658), yuv420p, 624x352 [SAR 1:1 DAR 39:22], SAR 180224:180219 DAR 8192:4621, 25 tbr, 25 tbn, 25 tbc
        } elsif ($_ =~ m/(Video): ([^,]+), (.*?), ([0-9]+)x([0-9]+)[^,]*,/) {
            # ffmpeg no informa bitrate, se asume 0, eso fuerza recodificacion
            $vcodec = $2;
            $width = $4;
            $height = $5;
            $vbitrate = 0;
        }
        # Audio: aac, 44100 Hz, mono, s16, 62 kb/s
        if ($_ =~ m/(Audio): ([^,]+), ([^,]+), ([^,]+), ([^,]+), ([^,]+) kb\/s.*/) {
            #~ print STDERR "Audio: [$1] [$2] [$3] [$4] [$5] [$6]\n";
            $acodec = $2;
            $abitrate = $6;
        }
    }
    print STDERR "[$origen] [$width] [$height] [$vcodec] [$acodec] [$vbitrate] [$abitrate]\n";

    return ($width, $height, $vcodec, $acodec,$vbitrate, $abitrate);
}

# ---------------------------------------------------------------
# arma el comando de ffmpeg a ejecutar para transcodificar
sub get_cmd_ffmpeg {
    my $origen = $_[0];
    my $destino = $_[1];
    my $pass = $_[2];
    my $formato = $_[3];
    my $video_string = 'copy'; #por defecto no se recodifica video
    my $audio_string = 'copy'; #por defecto no se recodifica audio
    my $resize_string = '';
    my $resize = 0;
    my $nd_pass = 0;
    my $ruta_trabajo = '';
    my $force_frames = '';
    my $threads_string = '';
    my $max_size = $MAX_PIXEL; # tamaño maximo del frame por defecto
    my $max_vrate = ceil(0.9*$MAX_VRATE); # bitrate maximo por defecto para video, se saca el 10%
    my $max_arate = $MAX_ARATE; # bitrate maximo por defecto para audio
    my ($nuevo_alto, $nuevo_ancho) = (0 ,0);

    my $videoFlags = '';
    my $audioFlags = '';

    # si existen cargamos los valores del formato a generar, sino usamos los valores
    # por defecto seteados anteriormente
    if (defined($formato->{'VIDEOSIZE'}) && $formato->{'VIDEOSIZE'} ne '')  {
        $max_size = $formato->{'VIDEOSIZE'};
    }
    if (defined($formato->{'VIDEOBITRATE'}) && $formato->{'VIDEOBITRATE'} ne '')  {
        $max_vrate = $formato->{'VIDEOBITRATE'};
    }

    # se carga el bitrate de audio, si se indica en el formato, sino usamos el maximo por defecto
    # ya seteado
    if (defined($formato->{'AUDIOBITRATE'}) && $formato->{'AUDIOBITRATE'} ne '')  {
        $max_arate = $formato->{'AUDIOBITRATE'};
    }

    if ($N_THREADS > 0) {
        $threads_string = "-threads $N_THREADS";
    }

    # ej: /var/www/sitio.cl/web/prontus/site/mm/20140319/mmedia/multimedia_video120140319122141.flv
    # si existe ruta temporal de trabajo se usa, si no usamos la misma ruta del archivo original en prontus
    if ($RUTA_TEMPORAL eq '')  {
        $ruta_trabajo = $RUTA_PRONTUS;
    } else {
        $ruta_trabajo = $RUTA_TEMPORAL;
    }

    # si el bitrate de video es mayor al maximo se debe cambiar la resolucion
    # o si el alto o ancho superan el tamaño definido
    if ($VBITRATE > $max_vrate || $ANCHO > $max_size || $ALTO > $max_size) {
        # si el tamaño se sobrepasa, ajustarlo.
        if ($ANCHO > $max_size || $ALTO > $max_size) {
            # si el ancho es > alto => ancho es mayor que $MAX_PIXEL
            if ($ANCHO > $ALTO) {
                #se ajusta el alto manteniendo la proporcion y el ancho se deja fijo al maximo
                $nuevo_alto = int ($max_size*$ALTO/$ANCHO);
                $nuevo_ancho = $max_size;
            } else {
                #se ajusta el ancho manteniendo la proporcion y el alto se deja fijo al maximo
                $nuevo_ancho = int ($max_size*$ALTO/$ANCHO);
                $nuevo_alto = $max_size;
            }
            $resize = 1;
        }
    }

    # la resolucion SIEMPRE debe ser par, si no es par se debe redimensionar
    if ($nuevo_ancho %2 != 0) {
        $nuevo_ancho += 1;
        $resize = 1;
    }
    if ($nuevo_alto%2 != 0) {
        $nuevo_alto += 1;
        $resize = 1;
    }

    # se arma string de cambio de tamaño de video:
    if ($resize) {
        $resize_string = "-s $nuevo_ancho" . 'x' . "$nuevo_alto";
    }

    #parametros de configuracion por defecto para video

    # si no es h264, o se hace resize, o el bitrate es muy alto, se necesita recodificar y hacer 2 pasos
    # tambien si hay que generar HLS se debe recodificar para generar keyframes alineados
    if ($VCODEC !~ /h264/i || $resize || $VBITRATE > $max_vrate || $HLS) {
        if (!defined($formato->{'X264'}) || (defined($formato->{'X264'}) && $formato->{'X264'} eq '')) {
            # TODO decidir si usar flags para ffmpeg <1 o >=1
            $videoFlags = 'b_adapt=2:trellis=1:cabac=1:bframes=3:keyint=90'; #configuracion de compresion para utilizar main por defecto y key int cada 2 segundos approx
        } else {
            $videoFlags = $formato->{'X264'}; #cargamos los parametros indicados
        }

        # si el video es h264 y el bitrate original es menor que el maximo indicado para el formato se usa el mismo
        if ($VBITRATE > 0 && $VBITRATE < $max_vrate && $VCODEC =~ /h264/i) {
            $videoFlags .= ':vbv-maxrate='.ceil(1.05*$VBITRATE).':vbv-bufsize='.(3*$VBITRATE).'" -b:v '.$VBITRATE.'000';
        } else {
            # sino usamos el bitrate indicado en el formato
            $videoFlags .= ':vbv-maxrate='.ceil(1.05*$max_vrate).':vbv-bufsize='.(3*$max_vrate).'" -b:v '.$max_vrate.'000';
        }

        # eliminamos las opciones que hacen demorar mas el primer paso
        if (!$pass) {
            $videoFlags =~ s/trellis=1://igs;
            $videoFlags =~ s/cabac=1://igs;
        }

        # eliminamos las opciones que no son necesarias en el paso 2
        if ($pass) {
            $videoFlags =~ s/b_adapt=2://igs; # no se necesita en paso 2
        }

        # se define el profile
        if (defined($formato->{'H264PROFILE'}) && $formato->{'H264PROFILE'} ne '')  {
            $videoFlags .= " -profile:v " . $formato->{'H264PROFILE'};
        } else {
            $videoFlags .= " -profile:v main";
        }

        # si este es el primer paso, agregamos opciones de paso 1 mas rapido
        if (!$pass) {
            $videoFlags = 'pass=1:subq=1:frameref=1:' . $videoFlags;
        }
        # al usar x264 ffmpeg 1.x usa -passlog file, ffmpeg 2.x usa stats=, se indican los 2 para compatibilidad
        # ya que si no se indica passlogfile en ffmpeg 1, escribe un log con prefijo "ffmpeg2pass" en la misma carpeta de xcoding
        # y usa el mismo para cada video
        $video_string = "libx264 -x264opts \"stats=$ruta_trabajo$ARTIC_filename.log:$videoFlags";

        # se necesitan 2 pasos si se recodifica el video
        $nd_pass = 1;
    }

    # se transcodifica audio si no es aac o sobrepasa el limite de bitrate definido
    # 2014/10/24 por problemas al generar HLS se transcodifica siempre el audio si se crea HLS
    if ($ACODEC !~ /aac/i || $ABITRATE > $max_arate || $HLS) {
        # generamos el string de compresion de audio
        # se elige encoder segun disponibilidad
        $audio_string = "libfaac"; # por defecto se usa libfaac
        if ($FDK) {
            $audio_string = "libfdk_aac";
        }
        # se elige frecuencia de sampleo, si no se especifica usa la original
        if (defined($formato->{'AUDIOSAMPLING'}) && $formato->{'AUDIOSAMPLING'} ne '') {
            $audio_string .= " -ar $formato->{'AUDIOSAMPLING'}";
        }

        # se elige bitrate de audio, si es mayor se usa el maximo, sino conservamos el que venia
        if ($ABITRATE > $max_arate) {
            # si el bitrate de audio es mayor que el maximo, usamos el maximo
            $audio_string .= " -ab ".$max_arate."k";
        } else {
            # si no usamos el mismo que tenia
            $audio_string .= " -ab ".$ABITRATE."k";
        }
        # se elige numero de canales, si no se especifica usa la original
        if (defined($formato->{'AUDIOCHANNELS'}) && $formato->{'AUDIOCHANNELS'} ne '') {
            $audio_string .= " -ac $formato->{'AUDIOCHANNELS'}";
        }
    }

    # para HLS se generan key frames alineados
    if ($HLS && $PRECISION_HLS) {
        $force_frames = '-force_key_frames expr:gte\(t,n_forced*10\)';
    }

    if ($nd_pass) {
        #si se hacen 2 pasos hay que entregar el string correspondiente a cada paso
        if (!$pass) {
            # primer paso los datos se envian a /dev/null ya que no se necesitan, no se procesa resize tampoco $ruta_trabajo$ARTIC_filename
            return ("$PATHNICE $prontus_varglb::DIR_FFMPEG/ffmpeg $threads_string -i $origen -y $force_frames -vcodec $video_string -pass 1 -an -passlogfile $ruta_trabajo$ARTIC_filename.log -f rawvideo /dev/null", 1);
        } else {
            # segundo paso
            return ("$PATHNICE $prontus_varglb::DIR_FFMPEG/ffmpeg $threads_string -i $origen -y $resize_string $force_frames -vcodec $video_string -pass 2 -acodec $audio_string -passlogfile $ruta_trabajo$ARTIC_filename.log -f mp4 $ruta_trabajo$destino", 1);
        }
    } else {
        #no se necesita segundo paso si no se codifica video
        return ("$PATHNICE $prontus_varglb::DIR_FFMPEG/ffmpeg $threads_string -i $origen -y -vcodec copy -acodec $audio_string -f mp4 $ruta_trabajo$destino", 0);
    }
}

# ---------------------------------------------------------------
# genera hls para el video indicado
sub generar_HLS {
    my $origen = $_[0];

    $origen =~ /(\/.*\/\d{8}\/mmedia\/multimedia_video\d+\d{14}\S*)\.mp4$/;

    my $path_hls = $1;
    # si existe borramos el directorio y su contenido
    if (-d $path_hls) {
        &glib_fildir_02::borra_dir($path_hls);
    }
    &glib_fildir_02::check_dir($path_hls);

    my $cmd = "$lib_xcoding::PATHNICE $prontus_varglb::DIR_FFMPEG/ffmpeg  -i $origen -y -codec copy -map 0 -bsf h264_mp4toannexb -f segment -segment_list $path_hls/playlist.m3u8 -segment_list_type m3u8 -segment_time 10 -segment_time_delta 0.05 $path_hls/%03d.ts";

    #~ print STDERR "generar HLS origen [$origen][$cmd]\n";
    print STDERR "generar HLS origen [$origen]\n";

    my $res = qx/$cmd 2>&1/;
    &die_stderr("Falló generación de HLS", "[$!][$res].", 1) if ($? != 0);

    # leemos el directorio para hacer purge
    my @archivos = &glib_fildir_02::lee_dir($path_hls);
    my $filepath = '';
    # hacemos purge de los archivos generados
    foreach my $archivo (@archivos) {
        next if($archivo eq '.' || $archivo eq '..');
        # armamos la ruta completa
        $filepath = "$path_hls/$archivo";
        # dejamos la ruta relativa
        if($filepath =~ /.*(\/.*?\/site\/\w+\/\d{8}\/mmedia\/multimedia_video\d+\S?.*)/) {
            &lib_prontus::purge_cache($1);
        }
    }
}
# ---------------------------------------------------------------
sub die_stderr {
    my $msg = $_[0];
    my $detalle = $_[1];
    my $write = $_[2];
    &write_status($msg) if ($write);
    print STDERR "[ERROR] $msg - $detalle";
    exit 1;
}

# ---------------------------------------------------------------
sub write_status {
    my $msg = $_[0];
    $msg =~ s/\n//sg;
    my $dir_xcoding_status = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/procs/xcoding";
    # chequeamos que el dir xcoding exista, y si no, lo creamos.
    return 0 if !glib_fildir_02::check_dir($dir_xcoding_status);
    
    my $file = "$dir_xcoding_status/xcoding_status_$ARTIC_ts_articulo.txt";

    &glib_fildir_02::write_file($file, $msg);
}

# ---------------------------------------------------------------
# Funciones para mantener compatibilidad transcodificacion basica
# ---------------------------------------------------------------
sub get_formatos_v1 {
    my $marca = $_[0];
    my %formatos;
    my $file_formatos = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/data/xcoding/formatos.cfg";

    if (-f $file_formatos) {
        my $buffer_formatos = &glib_fildir_02::read_file($file_formatos);
        if ($marca ne '') {
            while ($buffer_formatos =~ /\s*($marca\.\w)\s*=\s*["|'](.*?)["|']/ig) {
                $formatos{$1} = $2;
            }
        }
    }

    return %formatos;
}

# ---------------------------------------------------------------
sub get_info_video_v1 {
    my $origen = $_[0];
    my @info =`$prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen 2>&1`;
    my ($width, $height, $h264, $baseline, $vcodec, $acodec, $ext);

    if ($origen =~ /.+\/\d{8}\/mmedia\/multimedia_video.+?\d{6}\.(\w+)$/) {
        $ext = $1;
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
    }

    # si el tamaño se sobrepasa, ajustarlo.
    my ($new_width, $new_height);
    if ($width > 640 || ($width %2 != 0) || ($height %2 != 0) ) {
        $new_width = $width;
        $new_height = $height;
        if ($new_width > 640) {
            $new_width = 640;
            $new_height = int (640*$height/$width);
            if ($new_height %2 != 0){
                $new_height +=1;
            }
        } else {
            if ($new_width %2 != 0) {
                $new_width += 1;
            }
            if ($new_height%2 != 0) {
                $new_height += 1;
            }
        }
    }

    return ($new_width, $new_height, $h264, $baseline, $vcodec, $acodec);
}

# ---------------------------------------------------------------
sub get_cmd_ffmpeg_v1 {
    my $origen = $_[0];
    my $destino = $_[1];
    my $videoFlags = $_[2];
    my $pathnice = &lib_prontus::get_path_nice();

    if ($videoFlags ne '') {
        return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen $videoFlags $destino";
    }

    $videoFlags = $prontus_varglb::FFMPEG_PARAMS;
    if ($videoFlags eq '' ) {
        $videoFlags = "-flags +loop -cmp +chroma -partitions +parti8x8+parti4x4+partp8x8+partb8x8 -me_method umh -subq 8 -me_range 16 -keyint_min 25 -sc_threshold 40 -i_qfactor 0.71 -b_strategy 2 -qcomp 0.6 -qmin 10 -qmax 51 -qdiff 4 -directpred 3 -trellis 1 -coder 0 -bf 0 -refs 1 -flags2 -wpred-dct8x8+mbtree -level 30 -maxrate 10000000 -bufsize 10000000 -wpredp 0 -g 25 -b 600000"; #configuracion de compresion, para no utilizar presets ffmpeg
    }

    my ($ancho, $alto, $h264, $baseline, $vcodec, $acodec) = &get_info_video_v1($origen);

    my $audio_string = "libfaac -ar 44100 -ab 64k"; # por defecto se usa libfaac
    if ($FDK) {
        $audio_string = "libfdk_aac -ar 44100 -ab 48k";
    }

    if ($ancho ne '' && $alto ne '') {
        print STDERR "Redimension: ancho[$ancho], alto[$alto]\n";
        if ($acodec =~ /aac/i) {
            return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -s $ancho" . 'x' . "$alto -vcodec libx264 $videoFlags -acodec copy -f mp4 $destino";
        } else {
            return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -s $ancho" . 'x' . "$alto -vcodec libx264 $videoFlags -acodec $audio_string -f mp4 $destino";
        }

    } elsif ($acodec =~ /aac/i && $vcodec =~ /h264/i && $vcodec =~ /baseline/i) {
        return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -vcodec copy -acodec copy -f mp4 $destino";
    } elsif ($acodec =~ /aac/i) {
        return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -vcodec libx264 $videoFlags -acodec copy -f mp4 $destino";
    } else {
        return "$pathnice $prontus_varglb::DIR_FFMPEG/ffmpeg -i $origen -y -vcodec libx264 $videoFlags -acodec $audio_string -f mp4 $destino";
    }
}
# -------------------------------END LIBRERIA--------------------
return 1;
