#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO .
# -----------
# Guardar del editor de imagenes
#
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------

# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 02/2010 - YCC - Primera Version

# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ---------------------------------------------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_fildir_02;
use glib_str_02;
use glib_cgi_04;
use lib_prontus;
use lib_thumb;
use File::Copy;

use strict;


# ---------------------------------------------------------------
# MAIN.
# -------------
my (%COOKIES, %FORM);


# esta cgi opera con una imagen de trabajo en tmp.
# La primera vez, viene el path original, por lo tanto debo COPIARLA y ahi modificarla.
# Cuando se termina de editar, desde el editor de
# imagen es se invoca al submit de artic con param new_foto_edit = <path>, entonces se toma la imagen
# del tmp y con esa se crea una nueva prontus.
main: {


    # Rescatar parametros recibidos
    &glib_cgi_04::new();

    # Param comunes
    &glib_cgi_04::set_formvar('path_conf', \%FORM);
    &glib_cgi_04::set_formvar('image_path', \%FORM); # por ejemplo /prontus_toolbox/site/artic/20101021/imag/foto_1320101021175254.jpg
                                                     # o bien, /prontus_toolbox/cpan/procs/imgedit/foto_1320101021175254_<random>.jpg

    # Si viene crop y resize, hacer el crop y luego el resize.
    # Las demas operaciones siempre son individuales.

    # Param crop
    &glib_cgi_04::set_formvar('crop', \%FORM);  # 1|0
    &glib_cgi_04::set_formvar('crop_w', \%FORM);
    &glib_cgi_04::set_formvar('crop_h', \%FORM);
    &glib_cgi_04::set_formvar('crop_x', \%FORM);
    &glib_cgi_04::set_formvar('crop_y', \%FORM);

    # Resize
    &glib_cgi_04::set_formvar('resize', \%FORM); # 1|0
    &glib_cgi_04::set_formvar('resize_w', \%FORM);
    &glib_cgi_04::set_formvar('resize_h', \%FORM);

    # Flips
    &glib_cgi_04::set_formvar('fliph', \%FORM);  # 1|0
    &glib_cgi_04::set_formvar('flipv', \%FORM);  # 1|0

    # Rotar
    &glib_cgi_04::set_formvar('rotar', \%FORM);  # 90, 180, 270 (0 = no hay rotación).

    # warn "invocado con fliph[$FORM{'fliph'}] crop[$FORM{'crop'}] path_conf[$FORM{'path_conf'}]";

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'path_conf'});  # Prontus 6.0
    $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # user check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    # valida imag
    if(!(-f $prontus_varglb::DIR_SERVER . $FORM{'image_path'})) {
        &glib_html_02::print_json_result(0, 'La imagen no es válida', 'exit=1,ctype=1');
    };



    # Dir de trabajo
    my $prontus_id = $prontus_varglb::PRONTUS_ID;
    my $reldir_imgedit = "/$prontus_id/cpan/procs/imgedit";
    &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$reldir_imgedit");
    # garbage
    &garbage_work_images("$prontus_varglb::DIR_SERVER$reldir_imgedit");

    # Determinar si la imagen es la original o una tmp y segun eso determinar el path de la imagen de trabajo
    my $relpath_img_dst;
    if ($FORM{'image_path'} =~ /^\/$prontus_id\/site\/artic\/[0-9]{8}\/imag\/foto_([0-9]+)\.(\w+)$/) {

        my $random = &glib_str_02::random_string(12);
        my $ts = $1;
        my $ext = $2; # sin punto
        $relpath_img_dst = "$reldir_imgedit/foto_$ts" . '_' . "$random.$ext";
        while (-f "$prontus_varglb::DIR_SERVER$relpath_img_dst") {
            $random = &glib_str_02::random_string(12);
            $relpath_img_dst = "$reldir_imgedit/foto_$ts" . '_' . "$random.$ext";
        };
        # genera imagen nueva tmp para trabajar sobre ella
        &File::Copy::copy($prontus_varglb::DIR_SERVER . $FORM{'image_path'}, "$prontus_varglb::DIR_SERVER$relpath_img_dst");
    } else {
        if ($FORM{'image_path'} =~ /^\/$prontus_id\/cpan\/procs\/imgedit\/foto_([0-9]+)_[a-zA-Z0-9]{12}\.(\w+)$/) {
            $relpath_img_dst = $FORM{'image_path'};
        } else {
            &glib_html_02::print_json_result(0, "image_path[$FORM{'image_path'}] no es válido", 'exit=1,ctype=1');
        };
    };

    &procesar_imagen("$prontus_varglb::DIR_SERVER$relpath_img_dst"); # imagen temporal de trabajo

    # si la imagen era gif, la resultante quedo como png
    $relpath_img_dst =~ s/\.gif$/\.png/i if($relpath_img_dst =~ /\.gif$/i);

    # medir la img resultante (en realidad ya se mide antes, pero es mas q nada para simplificar el codigo)
    my ($msg_size, $w_final, $h_final) = &lib_prontus::dev_tam_img("$prontus_varglb::DIR_SERVER$relpath_img_dst");
    if ($msg_size) {
        warn "Error: $msg_size foto[$prontus_varglb::DIR_SERVER$relpath_img_dst] - dim[$w_final, $h_final]\n";
        &glib_html_02::print_json_result(0, 'No fue posible determinar las dimensiones de la imagen resultante', 'exit=1,ctype=1');
    };

    &glib_html_02::print_json_result(1, "url:$relpath_img_dst,w:$w_final,h:$h_final", 'exit=1,ctype=1');

};



# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub procesar_imagen {
    my $path_img_dst = shift;
    my $msg_err = '';
    if ($FORM{'crop'}) {
        $msg_err = 'crop_x no es válido' if (!&glib_str_02::is_digit($FORM{'crop_x'}));
        $msg_err = 'crop_y no es válido' if (!&glib_str_02::is_digit($FORM{'crop_y'}));
        $msg_err = 'crop_w no es válido' if (!&glib_str_02::is_digit($FORM{'crop_w'}));
        $msg_err = 'crop_h no es válido' if (!&glib_str_02::is_digit($FORM{'crop_h'}));
        &glib_html_02::print_json_result(0, $msg_err, 'exit=1,ctype=1') if ($msg_err);

        &do_crop($FORM{'crop_x'}, $FORM{'crop_y'}, $FORM{'crop_w'}, $FORM{'crop_h'}, $path_img_dst);

        if ($FORM{'resize'}) {
            $msg_err = 'resize_w no es válido' if (!&glib_str_02::is_digit($FORM{'resize_w'}));
            $msg_err = 'resize_h no es válido' if (!&glib_str_02::is_digit($FORM{'resize_h'}));
            &glib_html_02::print_json_result(0, $msg_err, 'exit=1,ctype=1') if ($msg_err);

            &do_resize($FORM{'resize_w'}, $FORM{'resize_h'}, $path_img_dst);
        };
    } elsif ($FORM{'resize'}) {
        $msg_err = 'resize_w no es válido' if (!&glib_str_02::is_digit($FORM{'resize_w'}));
        $msg_err = 'resize_h no es válido' if (!&glib_str_02::is_digit($FORM{'resize_h'}));
        &glib_html_02::print_json_result(0, $msg_err, 'exit=1,ctype=1') if ($msg_err);

        &do_resize($FORM{'resize_w'}, $FORM{'resize_h'}, $path_img_dst);
    } elsif ($FORM{'fliph'}) {
        &do_flip('horizontal', $path_img_dst);
    } elsif ($FORM{'flipv'}) {
        &do_flip('vertical', $path_img_dst);
    } elsif ($FORM{'rotar'}) {
        &glib_html_02::print_json_result(0, 'rotar no es válido', 'exit=1,ctype=1') if ($FORM{'rotar'} !~ /^(90|180|270)$/);
        &do_rotate($FORM{'rotar'}, $path_img_dst);
    } else {
        &glib_html_02::print_json_result(0, 'Acción requerida no es válida', 'exit=1,ctype=1');
    };
};
# ---------------------------------------------------------------
sub do_crop {
    my ($srcX, $srcY, $width, $height, $path_img_dst) = @_;
    my ($binfoto, $final_dimx, $final_dimy) = &lib_thumb::make_crop($srcX, $srcY, $width, $height, $path_img_dst);
    $path_img_dst =~ s/\.gif$/\.png/i if($path_img_dst =~ /\.gif$/i);
    &lib_thumb::write_image($path_img_dst, $binfoto);
};
# ---------------------------------------------------------------
sub do_resize {
    my ($width, $height, $path_img_dst) = @_;
    my ($binfoto, $anchofinal, $altofinal) = &lib_thumb::make_resize($width, $height, $path_img_dst);
    $path_img_dst =~ s/\.gif$/\.png/i if($path_img_dst =~ /\.gif$/i);
    &lib_thumb::write_image($path_img_dst, $binfoto);
};
# ---------------------------------------------------------------
sub do_flip {
    my ($sentido) = shift; # vertical | horizontal
    my ($path_img_dst) = shift;
    my $binfoto = &lib_thumb::make_flip($sentido, $path_img_dst);
    $path_img_dst =~ s/\.gif$/\.png/i if($path_img_dst =~ /\.gif$/i);
    &lib_thumb::write_image($path_img_dst, $binfoto);
};

# ---------------------------------------------------------------
sub do_rotate {
    my ($degrees) = shift; # 90 | 180 | 270
    my ($path_img_dst) = shift;
    my $binfoto = &lib_thumb::make_rotate($degrees, $path_img_dst);
    $path_img_dst =~ s/\.gif$/\.png/i if($path_img_dst =~ /\.gif$/i);
    &lib_thumb::write_image($path_img_dst, $binfoto);
};

# --------------------------------------------------------------------#
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
        };
    };
};

# -------------------------------END SCRIPT----------------------
