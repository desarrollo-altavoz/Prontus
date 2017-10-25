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
# Procesa el archivo zip cargado al articulo para generar los
# tamaños de imagenes definidos para la galería y los agrega al
# xml del artículo
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 1.0.0 - 28/05/2008 - CVI
# 2.0.0 - 02/08/2012 - CVI - Migrado para coop 2012
# 2.0.1 - 28/01/2013 - JOR - Se incluye dentro de la release prontus y se dejan tamaños dinamicos, provienen desde el fid.
# 2.0.2 - 11/03/2014 - JOR/CVI
# 2.0.3 - 09/06/2014 - CVI
# 2.0.4 - 17/06/2014 - MPG
# 2.0.5 - 17/07/2014 - EAG - Se agrega parametro -j a la descompresion para que no genere subcarpetas desde el zip
# 2.0.6 - 17/06/2016 - SCT Se mantiene nombre original para agregar al nombre final de la foto
# 2.0.10 - 17/08/2016 - MPG - Corrige contador de fotos y agrega escritura a salidas paralelas y multivistas
# 2.1.0 - 11/05/2017 - EAG - Se integra a Prontus
#
# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------
BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/[^\/]+$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

close STDOUT;

use utf8;
use strict;
use JSON;
use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use glib_fildir_02;

#~ use Data::Dumper;

my $MAXITEM = 100;
my @FOTOS;

my $TS;
my $PROCDIR;
my $DIRTMP;

my %HASHSIZES;

main:{
    my $origen = $ARGV[0];
    my $prontus_id;
    my $document_root;
    my $fechac;

    # Se leen los parámetros de entrada
    if ($origen =~ m|^(.*)/(.*?)/site/artic/(\d{8})/pags/(\d{14})\.\w+$|) {
        $document_root = $1;
        $prontus_id = $2;
        $fechac = $3;
        $TS = $4;
    } else {
        &exitProgram("Error al leer el TS del archivo de entrada [$origen]");
    };

    print STDERR "[$TS] Comienza el proceso de fotos\n";
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($prontus_id);
    $prontus_varglb::DIR_SERVER = $document_root;
    &lib_prontus::load_config("$prontus_varglb::DIR_SERVER$relpath_conf");
    $PROCDIR = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/procs/galeria_prontus";

    &set_semaforo();

    # Se imprime el TS y se comienza con el script
    my $xmlpath = $origen;
    $xmlpath =~ s/\/pags\/(\w+)(\.\w+)?$/\/xml\/$1\.xml/;
    my $bufferxml = &lib_prontus::get_xml_data($xmlpath);

    # Se lee la configuración para saber cuantas fotos hay
    my %campos_xml = &lib_prontus::getCamposXml($bufferxml, "_galeria_prontus_conf,_gal_archive");
    my $filezip = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/$fechac$prontus_varglb::DIR_ASOCFILE/$TS/$campos_xml{'_gal_archive'}";

    # No se hace nada si no viene el archivo
    if ($filezip =~ /[^\/]+\.zip$/i) {
        my @tmp = split /\|/, $campos_xml{'_galeria_prontus_conf'};
        foreach my $str (@tmp) {
            if ($str =~ /^(.*?):(.*?)$/) {
                my $num = $1;
                my $fotofija = $2;

                my %strsize = &lib_prontus::getCamposXml($bufferxml, "tam_galeria_prontus_$num");
                if ($strsize{"tam_galeria_prontus_$num"} =~ /^(\d+):(\d+)$/) {
                    print STDERR $str. " " . $strsize{"tam_galeria_prontus_$num"}."\n";
                    my %data;
                    $data{'ancho'} = $1;
                    $data{'alto'} = $2;
                    $data{'nombre'} = $fotofija;
                    $HASHSIZES{$num} = \%data;
                }
            }
        }

        # Se procesa el zip con las fotos
        &procesar_zip($filezip, $bufferxml, $fechac);
    } else {
        &exitProgram("No hay archivo zip en el articulo [$origen]");
    }

    # Se borra el directorio temporal
    if (-d $DIRTMP) {
        &glib_fildir_02::borra_dir($DIRTMP);
    }

    # Se hace un poco de garbage de las carpetas temporales
    &garbage_archivos($PROCDIR);

    # se actualiza el DAM con las nuevas imagenes
    my $cmd = "$prontus_varglb::DIR_SERVER/$prontus_varglb::DIR_CGI_CPAN/dam/prontus_dam_ppart_save.cgi $origen $prontus_varglb::PUBLIC_SERVER_NAME &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "] $cmd\n";
    system $cmd;

    &exitProgram("El proceso ha terminado. Se debe recargar el FID");
}

#---------------------------------------------------------------------------------------------------
sub procesar_zip {
    my ($filezip, $bufferxml, $fechac) = (@_);

    # Para medir tiempo de ejecucion
    my $timeini = time;

    # Se imprime el TS y se comienza con el script
    print STDERR "[$TS] Comienza el proceso batch del zip\n";

    # Se revisa extensión del archivo
    if ($filezip !~ /([^\/]+\.zip)$/i) {
        &exitProgram("El archivo debe ser un ZIP");
    };
    my $nameZip = $1;
    print STDERR "nameZip $nameZip\n";

    # si el zip se llama asi, es porque se cargaron imagenes a través de D&D
    # obtenemos el identificador de la carpeta temporal
    if ($nameZip =~ /_prontus_galeria_(\d+)\.zip/) {
        # si el articulo se habia guardado corresponde al TS del articulo
        # si el articulo es nuevo corresponde al epoch en milisegundos
        $DIRTMP = $PROCDIR . '/' . $1;
    } else {
        $DIRTMP = $PROCDIR . '/' . $TS;
    }

    # Se crea el directorio temporal, si no existiera
    &glib_fildir_02::check_dir($DIRTMP);

    # Se recorren la imagenes
    my @DIRFILES;
    # Se revisa la ruta del archivo
    $filezip = $prontus_varglb::DIR_SERVER . $filezip;
    if(! (-f $filezip)) {
        @DIRFILES = &glib_fildir_02::lee_dir($DIRTMP);
        # si hay menos de 3 archivos (= 2), no hay fotos en la carpeta
        # si hay 3 o mas hay al menos 1 imagen.
        if (scalar @DIRFILES < 3) {
            print STDERR "El archivo indicado no existe: $filezip\n";
            &exitProgram("El archivo zip no existe");
        } else {
            # revisamos los tipos de archivos subidos, si hay algun .zip
            # se debe descomprimir en la misma carpeta
            foreach my $file (@DIRFILES) {
                print STDERR $file;
                if ($file =~ /[^\/]+\.zip$/i) {
                    # Se descomprime el archivo
                    `unzip -oj $DIRTMP/$file -d $DIRTMP`;
                    # se borra despues de descomprimir
                    unlink "$DIRTMP/$file";
                }
            }
            # se actualiza el listado de archivos de la carpeta
            @DIRFILES = &glib_fildir_02::lee_dir($DIRTMP);
        }
    } else {
        # Se cambia al directorio temporal
        my $resp = `cd $DIRTMP`;
        if ($resp) {
            &exitProgram("No se pudo cambiar al directorio temporal: $resp");
        }

        # Se limpia el directorio temporal, para que no haya basura
        $resp = `rm -rf $DIRTMP/*`;
        if ($resp) {
            &exitProgram("Error al borrar los archivos del directorio temporal: $resp");
        }

        # Se mueve el Archivo al directorio temporal
        my $newZip = $DIRTMP . '/' . $nameZip;

        print STDERR "[$TS] Copiando el Zip $filezip -> $newZip\n";
        $resp = `cp '$filezip' '$newZip'`;
        if ($resp) {
            &exitProgram("Error al mover el archivo ZIP: $resp");
        }

        # Se descomprime el archivo
        $resp = `unzip -oj $newZip -d $DIRTMP`;
        if($resp =~ /such file/i) {
            &exitProgram("Error al descomprimir el archivo: $resp", 1);
        }

        # Se elimina el ZIP copiado
        if (-f $newZip) {
            unlink $newZip;
        }

        # Se recorren la imagenes
        @DIRFILES = &glib_fildir_02::lee_dir($DIRTMP);
    }

    # Se calculan datos del articulo
    my $dst_img = $prontus_varglb::DIR_SERVER . '/'.$prontus_varglb::PRONTUS_ID.'/site/artic/'.$fechac.'/imag';
    &glib_fildir_02::check_dir($dst_img);

    my $artic_obj = Artic->new(
                'prontus_id'=>$prontus_varglb::PRONTUS_ID,
                'public_server_name'=>$prontus_varglb::PUBLIC_SERVER_NAME,
                'cpan_server_name'=>$prontus_varglb::IP_SERVER,
                'document_root'=>$prontus_varglb::DIR_SERVER,
                'ts'=> $TS,
                'campos'=>{}) || die "Error inicializando objeto articulo: $Artic::ERR\n";

    $artic_obj->{xml_data} = &glib_fildir_02::read_file($artic_obj->{fullpath_xml});

    my $counter = 1;
    my $res;
    my $newimage;
    my $parse_as_cdata = 1;

    my %campos_xml = &lib_prontus::getCamposXml($bufferxml, '_galeria_prontus_str,_txt_galeria_description_total,_txt_galeria_credito_total');

    my %strfotos;
    my $id_str_photos = 1;
    foreach my $str_foto (split(/@@/, $campos_xml{'_galeria_prontus_str'})) {
        $strfotos{$id_str_photos} = $str_foto;
        $id_str_photos++;
    }
    # inicializamos el contador con el total de fotos del la galeria
    $counter = scalar(split(/\|/, $strfotos{'1'}));

    foreach my $file (sort @DIRFILES) {
        next if(-d $DIRTMP.'/'.$file);
        next unless($file =~ /\.jpg$/i or $file =~ /\.jpeg$/i or $file =~ /\.png$/i);

        while(&existe_imagen_xml($bufferxml, $counter) && $counter < $MAXITEM) {
            # Se agrega la imagen al string de fotos
            my $idx = ($counter+1);
            foreach my $num (keys %HASHSIZES) {
                my $fotofija = $HASHSIZES{$num}{'nombre'};
                $fotofija =~ s/@@/$idx/g;
                my %nomfoto = &lib_prontus::getCamposXml($bufferxml, $fotofija);
                $nomfoto{$fotofija} =~ s/^.*?\/(foto_\d+\.\w+)$/$1/;
                $strfotos{$num} = $nomfoto{$fotofija} .'|'. $strfotos{$num};
                # agregamos creditos y descripcion dummy
                if ($num eq '1') {
                    $campos_xml{'_txt_galeria_credito_total'} = '||==' . $campos_xml{'_txt_galeria_credito_total'};
                    $campos_xml{'_txt_galeria_description_total'} = '||==' . $campos_xml{'_txt_galeria_description_total'};
                }
            }
            $counter++;
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
            if ($resp) {
                print STDERR "No se pudo mover la imagen: '$DIRTMP/$file'\n";
                next;
            }
            print STDERR "Renombrando imagen: $file -> $newfile\n";
        }

        # Se mantiene nombre original para agregar al nombre final de la foto - SCT
        my $nom_foto_orig = "";
        if($file =~ /(.*?)\.(\w+)$/) {
            $nom_foto_orig = $1;
            $nom_foto_orig =~ s/\-/\_/sig;
            $nom_foto_orig = &lib_prontus::strip_text($nom_foto_orig);
            print STDERR "NOMBRE_ORIGINAL[$nom_foto_orig] \n";
        };

        # Se obtienen las dimensiones
        my ($msgx, $ancho, $alto) = &lib_prontus::dev_tam_img("$DIRTMP/$newfile");
        if($msgx ne '') {
            print STDERR "Error: $msgx [$ancho, $alto] -> [$newfile]\n";
            next;
        }
        print STDERR "procesando imagen: $DIRTMP/$newfile ($ancho, $alto)\n";

        my ($newimage, $nomfoto);

        # Procesando las imagenes
        foreach my $num (keys %HASHSIZES) {
            my $fotofija = $HASHSIZES{$num}{'nombre'};
            my $tam_w = $HASHSIZES{$num}{'ancho'};
            my $tam_h = $HASHSIZES{$num}{'alto'};

            my $cuadrar = '';
            $cuadrar = 'si' if($num eq '1');

            $newimage = &procesarImagen("$DIRTMP/$newfile", $ancho, $alto, $tam_w, $tam_h, $cuadrar);
            next unless($newimage);

            $nomfoto = $artic_obj->_add_foto_filesystem($newimage, $nom_foto_orig);
            $strfotos{$num} = $nomfoto .'|'. $strfotos{$num};
            my $pathfoto = "/".$prontus_varglb::PRONTUS_ID."/site/artic/$fechac/imag/$nomfoto";
            my $idx = ($counter+1);
            $fotofija =~ s/@@/$idx/g;

            # agregamos creditos y descripcion dummy
            if ($num eq '1') {
                if ($campos_xml{'_txt_galeria_credito_total'} ne '') {
                    $campos_xml{'_txt_galeria_credito_total'} = '||==' . $campos_xml{'_txt_galeria_credito_total'};
                    $campos_xml{'_txt_galeria_description_total'} = '||==' . $campos_xml{'_txt_galeria_description_total'};
                }
            }

            print STDERR "\tRedimensionando $fotofija a ($tam_w, $tam_h)\n";
            $artic_obj->{'xml_data'} = &lib_prontus::replace_in_xml($artic_obj->{'xml_data'}, $fotofija, $pathfoto, $parse_as_cdata);
        };

        $counter++;
        last if($counter >= $MAXITEM);
    };

    # Se guardan los Strings con las fotos
    my $str_gal = '';
    for (my $i = 1; $i <= scalar(keys %strfotos); $i++) {
        my $str = $strfotos{$i};
        # se elimina el | sobrante al final
        $str =~ s/\|$//;
        $str_gal .= $str ."@@";
    };
    $str_gal = substr($str_gal, 0, -2);

    # actualizamos los datos en el articulo
    # se actualiza la galeria
    $artic_obj->{'xml_data'} = &lib_prontus::replace_in_xml($artic_obj->{'xml_data'}, "_galeria_prontus_str", $str_gal, $parse_as_cdata);

    # Se actualizan las descripciones
    $artic_obj->{'xml_data'} = &lib_prontus::replace_in_xml($artic_obj->{'xml_data'}, "_txt_galeria_description_total", $campos_xml{'_txt_galeria_description_total'}, $parse_as_cdata);
    $artic_obj->{'xml_data'} = &lib_prontus::replace_in_xml($artic_obj->{'xml_data'}, "_txt_galeria_credito_total", $campos_xml{'_txt_galeria_credito_total'}, $parse_as_cdata);

    # Si todo salió bien hasta acá de limpia el ZIP original
    if (-f $filezip) {
        unlink $filezip;
    }
    $artic_obj->{'xml_data'} = &lib_prontus::replace_in_xml($artic_obj->{'xml_data'}, "_gal_archive", '', 0);

    # se actualiza el xml
    $artic_obj->_flush_xml();
    print STDERR "[$TS] Actualizando $artic_obj->{fullpath_xml}\n";

    # Finalmente el articulo se escribe a disco
    %{$artic_obj->{xml_content}} = (); # fuerza a que se lea el XML nuevamente
    $artic_obj->generar_vista_art('', '', $prontus_varglb::PRONTUS_KEY)
                || die("Error: $Artic::ERR");
    print STDERR "[$TS] Escribiendo a disco\n";

    # Generar vistas secundarias (a partir del xml)
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        $artic_obj->generar_vista_art($mv, '', $prontus_varglb::PRONTUS_KEY)
                || die("Error: $Artic::ERR");
        print STDERR "[$TS] Escribiendo multivista [$mv]\n";
    };

    # Parsear plantillas paralelas.
    my %campos_prontus = $artic_obj->get_xml_content();
    my @plt_paralelas_list = split(/;/, $prontus_varglb::FORM_PLTS_PARALELAS{$campos_prontus{'_fid'}});
    foreach my $plt_paralela (@plt_paralelas_list) {
        $artic_obj->generar_vista_art('', '', $prontus_varglb::PRONTUS_KEY, $plt_paralela, 1)
                || die("Error: $Artic::ERR");
        print STDERR "[$TS] Escribiendo salida paralela [$plt_paralela]\n";
    };

    print STDERR "[$TS] Escribiendo a disco\n";

    my $timefin = time;
    my $diff = $timefin - $timeini;
    print STDERR "[$TS] El proceso batch ha terminado.\n[$TS] Tiempo estimado: $diff segundos\n";
};

# ------------------------------------------------------------------------------
sub procesarImagen {
    my ($imagen, $ancho, $alto, $anchomax, $altomax, $cuadrar) = @_;

    #~ print STDERR "procesarImagen ($imagen, $ancho, $alto, $anchomax, $altomax, $fotofija)\n";
    return '' unless($imagen =~ /(\.\w+)$/);
    my $ext = $1;

    # Obtenemos el nombre de la imagen
    my $newimage = "$DIRTMP/temporal$ext";
    #~ print STDERR "newimage[$newimage]\n";
    my ($newbin, $newdimx, $newdimy);

    if($ancho > $anchomax || $alto > $altomax) {
        ($newbin, $newdimx, $newdimy) = &lib_thumb::make_thumbnail($anchomax, $altomax, $imagen, $cuadrar);
        &glib_fildir_02::write_file($newimage, $newbin);
    } else { # Si la imagen es mas pequeña, se copia nomas
        $newdimx = $ancho;
        $newdimy = $alto;
        #~ print STDERR "Copiando imagen pequena: $fotofija '$newimage'\n";
        my $resp = `cp '$imagen' '$newimage'`;
        if ($resp) {
            print STDERR "Error al copiar la imagen: $resp\n";
        }
    }

    $newimage =~ s/^$prontus_varglb::DIR_SERVER//;
    return $newimage;
}

# ------------------------------------------------------------------------------
sub existe_imagen_xml {
    my ($bufferxml, $counter) = @_;
    my $idx = ($counter+1);

    foreach my $num (keys %HASHSIZES) {
        my $fotofija = $HASHSIZES{$num}{'nombre'};
        $fotofija =~ s/@@/$idx/g;
        my %foto = &lib_prontus::getCamposXml($bufferxml, $fotofija);
        return 1 if($foto{$fotofija});
    }
    return 0;
}

#---------------------------------------------------------------------------------------------------
sub garbage_archivos {
    my($eldir) = shift;
    my $borrados = 0;
    my $totales = 0;
    # print "Garbage de Archivos [$eldir]\n";
    # Abre directorio.
    if (opendir(DIR, $eldir)) {
        my @entries = readdir(DIR);
        closedir DIR;

        # my $limite = (time - 31536000); # 1 año atras
        # my $limite = (time - 15768000); # 6 meses atras
        # my $limite = (time - 2628000); # 1 mes atras
        my $limite = (time - 259200); # 3 días atras
        # my $limite = (time - 86400); # 1 día atras
        foreach my $file (@entries) {
            next unless($file =~ /\d{14}/);
            # Detecta si son archivos.
            if (-f "$eldir/$file" || -d "$eldir/$file") {
                $totales++;
                if ((stat("$eldir/$file"))[9] < $limite) {
                    $borrados++;
                    my $resp = `rm -rf $eldir/$file`;
                    # print STDERR "Eliminando [$eldir/$file]\n";
                }
            }
        }
        # print STDERR "Archivos totales[$totales] borrados[$borrados]\n";
    }
}
#---------------------------------------------------------------------------------------------------
sub exitProgram {
    my ($msg) = (@_);
    if ($TS) {
        &unset_semaforo($msg);
        print STDERR "[$TS] $msg\n---------- exit --------\n";
    } else {
        print STDERR "Error: $msg\n---------- exit --------\n";
    }
    exit;
}
#---------------------------------------------------------------------------------------------------
sub unset_semaforo {
    my ($msg) = (@_);

    &glib_fildir_02::check_dir($PROCDIR);
    my $proctxt = "$PROCDIR/$TS.json";

    my %hash;
    $hash{'procesando'} = 0;
    $hash{'msg'} = $msg;

    my $jsonstr = &generaJson(\%hash);
    &glib_fildir_02::write_file($proctxt, $jsonstr);

    # borramos el semaforo despues de 10 segundos
    sleep 10;
    if(-f $proctxt) {
        unlink $proctxt;
    }
}
#---------------------------------------------------------------------------------------------------
sub set_semaforo {
    &glib_fildir_02::check_dir($PROCDIR);
    my $proctxt = "$PROCDIR/$TS.json";

    my %hash;
    $hash{'procesando'} = 1;
    $hash{'msg'} = 'Procesando la galeria';

    my $jsonstr = &generaJson(\%hash);
    &glib_fildir_02::write_file($proctxt, $jsonstr);
}
#---------------------------------------------------------------------------------------------------
sub generaJson {
    my $hash = $_[0];
    if ($JSON::VERSION =~ /^1\./) {
        my $json = new JSON;
        return $json->objToJson($hash);
    } else {
        return &JSON::to_json($hash);
    }
}
