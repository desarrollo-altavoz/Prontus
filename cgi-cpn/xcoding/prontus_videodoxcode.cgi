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
# 1.6 - 13/08/2013 - JOR - Cambia main, estaba mal implementado.
#                        - Agrega logeo de STDERR, ya que ahora este script corre en background.
#                        - Ordena codigo.
#                        - Cambia algunas funciones a lib_xcoding.
# ---------------------------------------------------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/xcoding$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use lib_prontus;
use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use glib_hrfec_02;
use lib_xcoding;
use strict;
use Artic;

my $ORIGEN = $ARGV[0];
my $PRONTUS_ID = $ARGV[1];
my $GENERAR_VERSIONES = $ARGV[2];
my $ARTIC_dirfecha;
my $ARTIC_ts_articulo;
my $ARTIC_path_xml;
my $ARTIC_filename;
my $ARTIC_extension;

# ---------------------------------------------------------------
main: {
    &die_stderr("El parámetro 'origen' no es válido.", "", 1) if ((!-f "$ORIGEN") || (!-s "$ORIGEN"));
    &die_stderr("El parámetro 'prontus_id' no es válido.", "", 1) if (! &lib_prontus::valida_prontus($PRONTUS_ID));
    &die_stderr("El parámetro 'prontus_id' no es válido.", "", 1) if (!-d "$prontus_varglb::DIR_SERVER/$PRONTUS_ID");

    $GENERAR_VERSIONES = 0 if (!$GENERAR_VERSIONES);
    my ($cmd, $res);

    if (!&load_artic_info()) {
        &die_stderr("No se obtener la información del artículo asociado al video.", "", 1);
    };

    $ORIGEN =~ /\/mmedia\/(multimedia_video\d+)\d{14}\.(\w+)$/i;
    my $marca = $1;

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$PRONTUS_ID/cpan/$PRONTUS_ID.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);  # Prontus 6.0
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

    if ($GENERAR_VERSIONES) {
        &crear_versiones_video($marca, $ORIGEN);
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

    &do_xcode($ORIGEN, $destino);

    # Crear versiones adicionales del video.
    &crear_versiones_video($marca, $destino);

    # Actualizar articulo.
    &actualizar_articulo($marca);
};

# ---------------------------------------------------------------
sub crear_versiones_video {
    my $marca = $_[0];
    my $origen = $_[1];

    print STDERR "Creando versiones [$marca]...\n";
    my %formatos = &lib_xcoding::get_formatos($marca);
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

        &do_xcode($origen, $new_destino, $flags, 1);
    };
};

# ---------------------------------------------------------------
sub actualizar_articulo {
    my $marca = $_[0];

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

    return '';
};

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

sub do_xcode {
    my $origen = $_[0];
    my $destino = $_[1];
    my $flags = $_[2];
    my $no_borr_origen = $_[3];

    my ($cmd, $res);
    $cmd = &lib_xcoding::get_cmd_ffmpeg($origen, $destino, $flags);

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
