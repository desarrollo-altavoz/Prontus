#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------------------------------------------
# 1.0.0 - 24/05/2017 - JOR - Primera versión
# ---------------------------------------------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use glib_cgi_04;
use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;
use glib_str_02;
use lib_thumb;
use File::Copy;
use Artic;
use strict;

my (%FORM);

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'path_conf'}  = &glib_cgi_04::param('_path_conf');

    # Parametros del editor.
    $FORM{'foto'}           = &glib_cgi_04::param('foto');
    $FORM{'srcX'}           = &glib_cgi_04::param('srcX');
    $FORM{'srcY'}           = &glib_cgi_04::param('srcY');
    $FORM{'width'}          = &glib_cgi_04::param('width');
    $FORM{'height'}         = &glib_cgi_04::param('height');
    $FORM{'rotate'}         = &glib_cgi_04::param('rotate');
    $FORM{'aspectRatio'}    = &glib_cgi_04::param('aspectRatio');
    $FORM{'zoomRatio'}      = &glib_cgi_04::param('zoomRatio');
    $FORM{'ts'}             = &glib_cgi_04::param('ts');
    $FORM{'fotow'}          = &glib_cgi_04::param('fotow'); # fotofija
    $FORM{'fotoh'}          = &glib_cgi_04::param('fotoh'); # fotofija
    $FORM{'only_resize'}    = &glib_cgi_04::param('only_resize'); # indica que solo debe aplicar resize.

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'path_conf'});  # Prontus 6.0
    $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # user check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    }

    # valida imag
    if (!(-f $prontus_varglb::DIR_SERVER . $FORM{'foto'})) {
        &glib_html_02::print_json_result(0, 'La imagen no es válida', 'exit=1,ctype=1');
    }

    if (!$FORM{'only_resize'}) { # continua normal.
        &valida_parametros();
    }

    # Directorio de trabajo: /cpan/procs/imgedit
    my $prontus_id = $prontus_varglb::PRONTUS_ID;
    my $reldir_imgedit = "/$prontus_id/cpan/procs/imgedit";
    &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$reldir_imgedit");
    # Garbage
    &garbage_work_images("$prontus_varglb::DIR_SERVER$reldir_imgedit");

    my $relpath_img_dst;
    my $nom_orig_foto;

    # Determinar si la imagen es la original o una tmp y segun eso determinar el path de la imagen de trabajo
    if ($FORM{'foto'} =~ /^\/$prontus_id\/site\/.*?\/[0-9]{8}\/imag\/foto_([0-9]+)\_*([a-zA-Z0-9\_\-]*?)\.(\w+)$/) {
        my $random = &glib_str_02::random_string(12);
        my $ts = $1;
        my $ext = $3; # sin punto
        $nom_orig_foto = $2; # nombre original de la foto, solo si esta en formato friendly url de imagenes.

        $relpath_img_dst = "$reldir_imgedit/foto_$ts" . '_' . "$random.$ext";
        while (-f "$prontus_varglb::DIR_SERVER$relpath_img_dst") {
            $random = &glib_str_02::random_string(12);
            $relpath_img_dst = "$reldir_imgedit/foto_$ts" . '_' . "$random.$ext";
        }
        # genera imagen nueva tmp para trabajar sobre ella
        &File::Copy::copy($prontus_varglb::DIR_SERVER . $FORM{'foto'}, "$prontus_varglb::DIR_SERVER$relpath_img_dst");
    }  else {
        # Invalida.
        &glib_html_02::print_json_result(0, "La imagen es inválida.", 'exit=1,ctype=1');
    }

    my $path_img_dst = "$prontus_varglb::DIR_SERVER$relpath_img_dst";

    if ($FORM{'only_resize'}) { # es solo resize de foto.
        &aplicar_resize($nom_orig_foto, $path_img_dst, $relpath_img_dst);
    }

    # Rotar antes de hacer crop.
    if ($FORM{'rotate'}) {
        my $degrees = $FORM{'rotate'};
        # cropper.js lo entrega asi. hay que ajustarlo.
        $degrees = 270 if ($degrees == -90);
        $degrees = 180 if ($degrees == -180);
        $degrees = 90 if ($degrees == -270);

        my $binfoto = &lib_thumb::make_rotate($degrees, $path_img_dst);
        $path_img_dst =~ s/\.gif$/\.png/i if($path_img_dst =~ /\.gif$/i);


        &lib_thumb::write_image($path_img_dst, $binfoto);
    }

    # Cropper
    my ($binfoto, $final_w, $final_h) = &lib_thumb::make_crop($FORM{'srcX'}, $FORM{'srcY'}, $FORM{'width'}, $FORM{'height'}, $path_img_dst);
    &lib_thumb::write_image($path_img_dst, $binfoto);

    # Se aplica el zoom si existe.
    if ($FORM{'zoomRatio'} > 1) {
        my $zoomW = $final_w * $FORM{'zoomRatio'};
        my $zoomH = $final_h * $FORM{'zoomRatio'};

        my ($binfoto, $anchofinal, $altofinal) = &lib_thumb::make_resize($zoomW, $zoomH, $path_img_dst);
        &lib_thumb::write_image($path_img_dst, $binfoto);
    }

    # Se redimensiona al tamaño de la fotofija real, ya que el crop lo deja mas grande.
    # Si es libre, no se hace nada.
    if ($FORM{'fotow'} && $FORM{'fotoh'}) {
        my ($binfoto, $anchofinal, $altofinal) = &lib_thumb::make_resize($FORM{'fotow'}, $FORM{'fotoh'}, $path_img_dst);
        &lib_thumb::write_image($path_img_dst, $binfoto);
    }

    # Agregar nueva imagen al articulo.
    my ($fotonum, $relpath_foto, $wfoto, $hfoto) = &agrega_foto_artic($relpath_img_dst, $nom_orig_foto, $path_img_dst);

    &glib_html_02::print_json_result(1, "$relpath_foto;$fotonum;$wfoto;$hfoto", 'exit=1,ctype=1');

};

sub aplicar_resize {
    my $nom_orig_foto = $_[0];
    my $path_img_dst = $_[1];
    my $relpath_img_dst = $_[2];

    if ($FORM{'fotow'} && $FORM{'fotoh'}) {
        my ($binfoto, $anchofinal, $altofinal) = &lib_thumb::make_resize($FORM{'fotow'}, $FORM{'fotoh'}, $path_img_dst);
        &lib_thumb::write_image($path_img_dst, $binfoto);

        my ($fotonum, $relpath_foto, $wfoto, $hfoto) = &agrega_foto_artic($relpath_img_dst, $nom_orig_foto, $path_img_dst);

        &glib_html_02::print_json_result(1, "$relpath_foto;$fotonum;$wfoto;$hfoto", 'exit=1,ctype=1');
    } else {
        &glib_html_02::print_json_result(0, "Debe indicar las nuevas dimensiones (ancho y alto) de la foto.", 'exit=1,ctype=1');
    }
};

sub agrega_foto_artic {
    my $foto = $_[0];
    my $nom_orig = $_[1];
    my $path_img_dst = $_[2];
    my $artic_obj;

    unless($artic_obj = Artic->new(
                'document_root'     => $prontus_varglb::DIR_SERVER,
                'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                'public_server_name'=> $prontus_varglb::PUBLIC_SERVER_NAME,
                'cpan_server_name'  => $prontus_varglb::IP_SERVER,
                'ts'                => $FORM{'ts'},
                'campos'            => {})) {

        print STDERR "[error] Error inicializando objeto articulo: $Artic::ERR\n";
        unlink $path_img_dst; # se elimina foto generada.
        &glib_html_02::print_json_result(0, "[error] Error inicializando objeto articulo: $Artic::ERR", 'exit=1,ctype=1');
    };

    $artic_obj->{xml_data} = &glib_fildir_02::read_file($artic_obj->{fullpath_xml});

    my $nomfoto = $artic_obj->_add_foto_filesystem($foto, $nom_orig); # en este punto, aun no se escribe el XML, por si hay errores.
    my $fechac;
    my $fotonum;
    my $wfoto;
    my $hfoto;
    my $bufferXML = $artic_obj->{xml_data};

    # Se deduce del TS del articulo.
    if ($FORM{'ts'} =~ /^(\d{8})/) {
        $fechac = $1;
    }

    if (!$fechac) {
        unlink $path_img_dst; # se elimina foto generada.
        &glib_html_02::print_json_result(0, "No se pudo obtener la fecha de creación del artículo (fechac).", 'exit=1,ctype=1');
    }

    my $relbase_path = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . "/$fechac";
    my $relpath_foto = $relbase_path . $prontus_varglb::DIR_IMAG . "/" . $nomfoto;

    if (!-d "$prontus_varglb::DIR_SERVER$relbase_path") {
        unlink $path_img_dst; # se elimina foto generada.
        unlink "$prontus_varglb::DIR_SERVER$relpath_foto"; # foto creada por _add_foto_filesystem.

        &glib_html_02::print_json_result(0, "El directorio base [$relbase_path] no existe.", 'exit=1,ctype=1');
    }

    if (!-f "$prontus_varglb::DIR_SERVER$relpath_foto") {
        unlink $path_img_dst; # se elimina foto generada.
        &glib_html_02::print_json_result(0, "La foto generada por objeto Artic no existe.", 'exit=1,ctype=1');
    }

    if ($nomfoto =~ /^(foto_\d{8}).*/i) {
        $fotonum = $1;
    } else {
        print STDERR "Error al determinar foto_<numero> de la foto [$nomfoto]\n";
        unlink $path_img_dst; # se elimina foto generada.
        unlink "$prontus_varglb::DIR_SERVER$relpath_foto"; # foto creada por _add_foto_filesystem.
        &glib_html_02::print_json_result(0, "Error al determinar foto_<numero> de la foto [$nomfoto]", 'exit=1,ctype=1');
    }

    if ($fotonum) {
        if ($bufferXML =~ /<(_w$fotonum)>(.+?)<\/\1>/i) {
            $wfoto = $2;
        }
        if ($bufferXML =~ /<(_h$fotonum)>(.+?)<\/\1>/i) {
            $hfoto = $2;
        }
    }

    if (!$wfoto || !$hfoto) {
        unlink $path_img_dst; # se elimina foto generada.
        unlink "$prontus_varglb::DIR_SERVER$relpath_foto"; # foto creada por _add_foto_filesystem.
        &glib_html_02::print_json_result(0, "No se pudo obtener del XML el ancho y el alto de la foto.", 'exit=1,ctype=1');
    }

    if (-f $path_img_dst) {
        unlink $path_img_dst;
    }

    # Todo OK. Se escribe el XML.
    $artic_obj->_flush_xml();

    return ($fotonum, $relpath_foto, $wfoto, $hfoto);
};

sub valida_parametros {
    if ($FORM{'srcX'} eq '' || $FORM{'srcY'} eq '') {
        &glib_html_02::print_json_result(0, "Parámetros insuficientes para realizar crop.", 'exit=1,ctype=1');
    }

    if ($FORM{'width'} eq '' || $FORM{'height'} eq '') {
        &glib_html_02::print_json_result(0, "Parámetros insuficientes para realizar crop.", 'exit=1,ctype=1');
    }


    if ($FORM{'rotate'} && $FORM{'rotate'} !~ /[0-9]+/) {
        &glib_html_02::print_json_result(0, "Ángulo de rotación inválido.", 'exit=1,ctype=1');
    }

    if ($FORM{'zoomRatio'} && $FORM{'zoomRatio'} !~ /[0-9]+/) {
        &glib_html_02::print_json_result(0, "Zoom ratio inválido.", 'exit=1,ctype=1');
    }

    if (!$FORM{'ts'}) {
        &glib_html_02::print_json_result(0, "El TS del artículo es obligatorio.", 'exit=1,ctype=1');
    } elsif ($FORM{'ts'} && $FORM{'ts'} !~ /[0-9]+/) {
        &glib_html_02::print_json_result(0, "El TS es inválido.", 'exit=1,ctype=1');
    }
};

sub garbage_work_images {
    my $dir = shift;
    my $segs_antig = 28800; # 8hrs
    # Lee el contenido del directorio.
    my @lisdir = &glib_fildir_02::lee_dir($dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

    # Borra archivos con mas $segs_antig de antiguedad, por fecha de ult modif.
    foreach my $entry (@lisdir) {
        next if (!-f "$dir/$entry");
        my @stats = stat "$dir/$entry";
        # print $stats[10] . ' ';
        if ($stats[9] < (time - $segs_antig)) {
            unlink "$dir/$entry";
        }
    }
};