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
# Genera las páginas de galería de fotos.
# Los archivos quedan en el mismo directorio del artículo, pero
# con formato:  <ts>_<pag>.html
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 1.0.0 - 28/05/2008 - CVI
# 2.0.0 - 02/08/2012 - CVI - Migrado para coop 2012
# 2.1.0 - 28/01/2013 - JOR - Se incluye dentro de la release prontus y se dejan tamaños dinamicos, provienen desde el fid.
#
# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------
BEGIN {

    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/pproc$//;
    #~ $pathLibsProntus =~ s/\/migracion$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};



    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);

#~ close STDOUT;

use strict;
use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use lib_ppart_galeria;
use Benchmark;
use lib_clustering;
use JSON;

#~ use glib_fildir_02;
#~ use DB;
#~ use XML::Simple;

my %DATOS_XML;
my $MAXITEM = 100;
my @FOTOS;

my $DESCRIPCION_COMUN = '';
my $CREDITO_COMUN = '';

my $document_root;
my $prontus_id;
my $fechac;
my $ts;
my $extension;
my $server;
my $fileZip;
my $origen;
my $mode;
my $destino;
my $xmlpath;

my $PROCDIR;
my $PROCTXT;
my $DIRTMP;

my $LNK_IMG;
my $DST_IMG;

my ($TAM_THUMB_W, $TAM_THUMB_H);
my ($TAM_FOTO_W, $TAM_FOTO_H);

main:{

    $fileZip = $ARGV[0];
    $origen = $ARGV[1];
    $server = $ARGV[2];
    $mode = $ARGV[3];

    #~ print STDERR "-----------------------------\n";

    # Se revisa si viene el archivo y se corrigen los parametros de entrada
    if($mode eq '') {
        $server = $origen;
        $origen = $fileZip;
        $fileZip = '';
    }

    # Se leen los parámetros de entrada
    if($origen =~ m|^((.*)/(.*?)/site/artic/(\d{8})/pags)/(\d{14})(\.\w+)$|) {
        $destino = $1;
        $document_root = $2;
        $prontus_id = $3;
        $fechac = $4;
        $ts = $5;
        $extension = $6;
        $PROCDIR = "$document_root/$prontus_id/cpan/procs/status_fotorama";

    } else {
        &exitProgram("Error al leer el TS del archivo de entrada [$origen]\n");
    };

    &set_semaforo($ts);

    print STDERR "[$ts] Comienza el proceso de fotos\n";
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($prontus_id);
    $prontus_varglb::DIR_SERVER = $document_root;

    &lib_prontus::load_config("$prontus_varglb::DIR_SERVER$relpath_conf");

    # Se imprime el TS y se comienza con el script
    $xmlpath = $origen;
    $xmlpath =~ s/\/pags\/(\w+)(\.\w+)?$/\/xml\/\1\.xml/;
    my $buffer = &lib_ppart_galeria::get_xml_data($xmlpath);

    $TAM_THUMB_W = &lib_ppart_galeria::get_xml_cdata_valor($buffer, "tam_galeria_thumb_w");
    $TAM_THUMB_H = &lib_ppart_galeria::get_xml_cdata_valor($buffer, "tam_galeria_thumb_h");
    $TAM_FOTO_W = &lib_ppart_galeria::get_xml_cdata_valor($buffer, "tam_galeria_foto_w");
    $TAM_FOTO_H = &lib_ppart_galeria::get_xml_cdata_valor($buffer, "tam_galeria_foto_h");
    

    # No se hace nada si no viene el archivo
    if($fileZip ne '') {
        # Se procesa el zip con las fotos
        &procesar_zip($fileZip, $buffer);
        # Por si las fotos fueron actualizadas, se vuelven a leer
    }

    &exitProgram("El proceso ha terminado");
}

#---------------------------------------------------------------------------------------------------
sub searchForFotos {
    my ($buffer) = ($_[0]);
    #for(my $r = 1; $r <= 32 ; $r++) {
    for(my $k=1 ; $k<=$MAXITEM ; $k++) {
        my $num = $k;
        $num = '0'.$num if($num>0 && $num<10);

        my $foto1 = &lib_ppart_galeria::get_xml_cdata_valor($buffer, "fotofija_port${num}_thumb");
        my $foto2 = &lib_ppart_galeria::get_xml_cdata_valor($buffer, "fotofija_port${num}_foto");
        if($foto1 && $foto2) {
            push @FOTOS, $num;
        }
    }
}

#---------------------------------------------------------------------------------------------------
sub parseThumbs {

    my ($buffer, $tmpl, $fileurl) = (@_);
    my ($loop, $looptemp, $looptotal);
    if($tmpl =~ /%%loop%%(.*?)%%\/loop%%/isg) {
        $loop = $1;
        for(my $r = 0; $r <= $#FOTOS ; $r++) {
            $looptemp = $loop;
            my $num = $FOTOS[$r];
            my $actual = ($r+1);
            my $foto1     = &lib_ppart_galeria::get_xml_cdata_valor($buffer, "fotofija_port${num}_thumb");
            my $wfoto1    = &lib_ppart_galeria::get_ancho_foto($buffer, $foto1);
            my $hfoto1    = &lib_ppart_galeria::get_altura_foto($buffer, $foto1);
            $looptemp =~ s/%%thumb%%/$foto1/g;
            $looptemp =~ s/%%wthumb%%/$wfoto1/g;
            $looptemp =~ s/%%hthumb%%/$hfoto1/g;
            $looptemp =~ s/%%r%%/$actual/g;
            my $urltemp = $fileurl;
            $urltemp =~ s/(\.\w+)$/_$actual\1/ if($actual != 1);
            $looptemp =~ s/%%url%%/$urltemp/g;
            $looptotal = $looptotal . $looptemp;
        }
        $tmpl =~ s/%%loop%%.*?%%\/loop%%/$looptotal/isg;
    }
    return $tmpl;
}

#---------------------------------------------------------------------------------------------------
sub procesar_zip {

    my ($fileZip, $bufferxml) = (@_);

    # Para medir tiempo de ejecucion
    my $timeini = time;

    # Se imprime el TS y se comienza con el script
    print STDERR "[$ts] Comienza el proceso batch del zip\n";

    # Se revisa extensión del archivo
    if($fileZip !~ /[^\/]+\.zip$/i) {
        &exitProgram("El archivo debe ser un ZIP");
    };

    # Se revisa que venga el zip con fotos
    my $origen = $document_root.'/'.$prontus_id.'/site/artic/'.$fechac.'/xml/'.$ts.'.xml';
    my $buffer = &lib_ppart_galeria::get_xml_data($origen);

    # Se crea el directorio temporal, si no existiera
    $DIRTMP = $PROCDIR . '/' . $ts;
    &glib_fildir_02::check_dir($DIRTMP);

    # Se revisa la ruta del archivo
    my $fileZip = $document_root . $fileZip;
    if(! (-f $fileZip)) {
        &exitProgram("El archivo indicado no existe: $fileZip");
    }

    $fileZip =~ /\/([^\/]+)$/;
    my $nameZip = $1;

    # Se cambia al directorio temporal
    my $resp = `cd $DIRTMP`;
    if($resp) {
        &exitProgram("No se pudo cambiar al directorio temporal: $resp");
    }

    # Se limpia el directorio temporal, para que no haya basura
    $resp = `rm -rf $DIRTMP/*`;
    if($resp) {
        &exitProgram("Error al borrar los archivos del directorio temporal: $resp");
    }

    # Se mueve el Archivo al directorio temporal
    #~ print STDERR "[$ts] Copiando el Zip $fileZip -> $DIRTMP\n";
    $resp = `cp '$fileZip' '$DIRTMP'`;
    if($resp) {
        &exitProgram("Error al mover el archivo ZIP: $resp");
    }

    # Se descomprime el archivo
    my $newZip = $DIRTMP . '/' . $nameZip;
    $resp = `/usr/bin/unzip -o $newZip -d $DIRTMP`;
    if($resp =~ /such file/i) {
        &exitProgram("Error al descomprimir el archivo: $resp", 1);
    }

    # Se elimina el ZIP copiado
    unlink $newZip;

    # Se calculan datos del articulo
    $LNK_IMG = '/'.$prontus_id.'/site/artic/'.$fechac.'/imag';
    $DST_IMG = $document_root . $LNK_IMG;
    &glib_fildir_02::check_dir($DST_IMG);

    my $artic_obj = Artic->new(
                'prontus_id'=>$prontus_id,
                'public_server_name'=>$prontus_varglb::PUBLIC_SERVER_NAME,
                'cpan_server_name'=>$prontus_varglb::IP_SERVER,
                'document_root'=>$prontus_varglb::DIR_SERVER,
                'ts'=> $ts,
                'campos'=>{}) || die "Error inicializando objeto articulo: $Artic::ERR\n";
    #~ $artic_obj->get_xml_content();
    $artic_obj->{xml_data} = &glib_fildir_02::read_file($artic_obj->{fullpath_xml});

    my $strthumbs = '';
    my $strfotos = '';

    # Se recorren la imagenes
    my @DIRFILES = &glib_fildir_02::lee_dir($DIRTMP);
    my $counter = 0;
    my $res;
    my $newimage;
    my $parse_as_cdata = 1;
    foreach my $file (sort @DIRFILES) {
        next if(-d $DIRTMP.'/'.$file);
        next unless($file =~ /\.jpg$/i or $file =~ /\.jpeg$/i or $file =~ /\.png$/i);

        while(&existe_imagen_xml($bufferxml, $counter) && $counter < $MAXITEM) {
            $counter++;
            #~ print STDERR "----- Saltando a siguiente imagen\n";
            next;
        }
        if ($counter >= $MAXITEM) {
            last;
        }

        # Procesando la primera imagen
        print STDERR "--- Procesando la imagen: $file\n";

        # Se cambia el nombre de la imagen
        my $newfile = $file;
        $newfile =~ s/ /_/g;
        $newfile = lc $newfile;
        if($newfile ne $file) {
            my $resp = `mv '$DIRTMP/$file' '$DIRTMP/$newfile'`;
            if($resp) {
                print STDERR "No se pudo mover la imagen: '$DIRTMP/$file'\n";
                next;
            }
            print STDERR "Renombrando imagen: $file -> $newfile\n";
        }

        # Se obtienen las dimensiones
        my ($msgx, $ancho, $alto) = &lib_prontus::dev_tam_img("$DIRTMP/$newfile");
        if($msgx ne '') {
            print STDERR "Error: $msgx [$ancho, $alto] -> [$newfile]\n";
            next;
        }
        print STDERR "Dimensiones de la imagen ($ancho, $alto)\n";
        my $strcounter = ($counter+1);
        $strcounter = '0'.$strcounter if($strcounter < 10);

        my ($newimage, $nomfoto);
        my $cuadrar = '';

        # Procesando las imagenes
        print STDERR "Creando imagen de: 600px ALTO\n";
        $newimage = &procesarImagen("$DIRTMP/$newfile", $ancho, $alto, $TAM_FOTO_W, $TAM_FOTO_H, $cuadrar);
        next unless($newimage);
        $nomfoto = $artic_obj->_add_foto_filesystem("$newimage");
        $strfotos = $strfotos.'|'.$nomfoto;
        $nomfoto = "/$prontus_id/site/artic/$fechac/imag/$nomfoto";
        $artic_obj->{xml_data} = &lib_prontus::replace_in_xml($artic_obj->{xml_data}, "fotofija_port${strcounter}_foto", $nomfoto, $parse_as_cdata);

        print STDERR "Creando imagen de: 65px\n";
        ($newimage) = &procesarImagen("$DIRTMP/$newfile", $ancho, $alto, $TAM_THUMB_W, $TAM_THUMB_H, 'si');
        next unless($newimage);
        $nomfoto = $artic_obj->_add_foto_filesystem("$newimage");
        $strthumbs = $strthumbs.'|'.$nomfoto;
        $nomfoto = "/$prontus_id/site/artic/$fechac/imag/$nomfoto";
        $artic_obj->{xml_data} = &lib_prontus::replace_in_xml($artic_obj->{xml_data}, "fotofija_port${strcounter}_thumb", $nomfoto, $parse_as_cdata);


        $counter++;
        last if($counter >= $MAXITEM);
    }
    $strthumbs =~ s/^\|//;
    $strfotos =~ s/^\|//;
    $artic_obj->{xml_data} = &lib_prontus::replace_in_xml($artic_obj->{xml_data}, "galeria_thumbs", $strthumbs, $parse_as_cdata);
    $artic_obj->{xml_data} = &lib_prontus::replace_in_xml($artic_obj->{xml_data}, "galeria_fotos", $strfotos, $parse_as_cdata);

    # Si todo salió bien hasta acá de limpia el ZIP original
    unlink $fileZip;

    # $artic_obj->{xml_data} = &lib_prontus::replace_in_xml($artic_obj->{xml_data}, "ASOCFILE_BATCH", '', 1);
    $artic_obj->{xml_data} =~ s/<asocfile_batch>.*?<\/asocfile_batch>\s//igs;
    $artic_obj->_flush_xml();
    print STDERR "[$ts] Actualizando $xmlpath\n";

    # Finalmente el articulo se escribe a disco
    $artic_obj->generar_vista_art('', '', $prontus_varglb::PRONTUS_KEY)
                || die("Error: $Artic::ERR");
    print STDERR "[$ts] Escribiendo a disco\n";

    my $timefin = time;
    my $diff = $timefin - $timeini;
    print STDERR "[$ts] El proceso batch ha terminado.\n[$ts] Tiempo estimado: $diff segundos\n";
    # &exitProgram("El proceso ha terminado.\nTiempo estimado: $diff segundos.\n\n\n", 1);

};

# ------------------------------------------------------------------------------
sub procesarImagen {

    my ($imagen, $ancho, $alto, $anchomax, $altomax, $cuadrar) = @_;

    #~ print STDERR "procesarImagen ($imagen, $ancho, $alto, $anchomax, $altomax, $fotofija)\n";
    return '' unless($imagen =~ /(\.\w+)$/);
    my $ext = $1;

    # Obtenemos el nombre de la imagen
    #~ my $nomfile = &get_nom_foto($ext, $ts);
    my $newimage = "$DIRTMP/temporal$ext";
    print STDERR "newimage[$newimage]\n";
    my ($newbin, $newdimx, $newdimy);

    #~ # Si termina con _70 se hace el thumb cuadrado
    #~ if($fotofija =~ /88x50$/) {
        #~ ($newbin, $newdimx, $newdimy) = &lib_thumb::make_thumbnail($anchomax, $altomax, $imagen, 'si');
        #~ &glib_fildir_02::write_file($newimage, $newbin);
    #~
    #~ # Aca se redimensiona la imagen si es mas grande
    #~ } elsif($ancho > $anchomax || $alto > $altomax) {
    if($ancho > $anchomax || $alto > $altomax) {
        ($newbin, $newdimx, $newdimy) = &lib_thumb::make_thumbnail($anchomax, $altomax, $imagen, $cuadrar);
        &glib_fildir_02::write_file($newimage, $newbin);

    # Si la imagen es mas pequeña, se copia nomas
    } else {
        $newdimx = $ancho;
        $newdimy = $alto;
        #~ print STDERR "Copiando imagen pequena: $fotofija '$newimage'\n";
        my $resp = `cp '$imagen' '$newimage'`;
        if($resp) {
            print STDERR "Error al copiar la imagen: $resp\n";
        }
    }

    $newimage =~ s/^$document_root//;
    # $buffer = &add_foto_prontus($newdimx, $newdimy, "$nomfile$ext", $buffer);
    # $buffer = &lib_ppart_galeria::actualizaCampo($buffer, $fotofija, "$LNK_IMG/$nomfile$ext");
    # replace_in_xml

    return $newimage;
}

# ------------------------------------------------------------------------------
sub existe_imagen_xml {
    my ($bufferxml, $counter) = @_;

    my $strcounter = ($counter+1);
    $strcounter = '0'.$strcounter if($strcounter < 10);

    my $foto700    = &lib_ppart_galeria::get_xml_cdata_valor($bufferxml, 'fotofija_port'.$strcounter.'_700x393'); # ?
    my $foto632    = &lib_ppart_galeria::get_xml_cdata_valor($bufferxml, 'fotofija_port'.$strcounter.'_632x355'); # ?
    my $foto88    = &lib_ppart_galeria::get_xml_cdata_valor($bufferxml, 'fotofija_port'.$strcounter.'_88x50'); # ?
    if($foto700 || $foto632 || $foto88) {
        # Existe por lo menos una foto
        return 1;
    }
    return 0;
}

#---------------------------------------------------------------------------------------------------
sub exitProgram {

    my ($msg) = (@_);
    if($ts) {
        &unset_semaforo($ts, $msg);
        print STDERR "[$ts] $msg\n---------- exit --------\n";
    } else {
        print STDERR "Error: $msg\n---------- exit --------\n";
    }
    exit;
}
#---------------------------------------------------------------------------------------------------
sub unset_semaforo {

    my ($ts, $msg) = (@_);

    &glib_fildir_02::check_dir($PROCDIR);
    my $proctxt = "$PROCDIR/$ts.json";

    my $hash;
    $hash->{'procesando'} = 0;
    $hash->{'msg'} = $msg;

    my $json = new JSON;
    # print $json->to_json($resp);
    my $jsonstr = &JSON::to_json($hash);
    &glib_fildir_02::write_file($proctxt, $jsonstr);

}
#---------------------------------------------------------------------------------------------------
sub set_semaforo {

    my ($ts) = (@_);

    &glib_fildir_02::check_dir($PROCDIR);
    my $proctxt = "$PROCDIR/$ts.json";

    my $hash;
    $hash->{'procesando'} = 1;
    $hash->{'msg'} = 'Procesando la galeria';

    my $json = new JSON;
    # print $json->to_json($resp);
    my $jsonstr = &JSON::to_json($hash);
    &glib_fildir_02::write_file($proctxt, $jsonstr);
}
