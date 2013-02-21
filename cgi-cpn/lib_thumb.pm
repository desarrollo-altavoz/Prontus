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
# PROPOSITO.
# -----------
# Funciones para generar thumbnails

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 1.0 - 01/2005 - YCH integra script de ALD
# 1.1 generacion de gif no funciona, asi que los gif los deja como jpg.
# 1.2 ahora los gif se generan como png

# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

package lib_thumb;

use strict;
use lib_prontus;
use glib_fildir_02;

my $JPEG_COMPRESSION = 85;

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

sub make_thumbnail {
    # Genera thumb de la imagen jpg o gif, basandose en el anchomax, altomax o en ambos.
    # Retorna: anchofinal, altofinal, buffer binario de la imagen.

    my $anchomax = $_[0];
    my $altomax = $_[1];
    my $lafoto = $_[2]; # full path
    my $cuadrar = $_[3];

    my $no_hay_gd;
    eval "require GD;";    $no_hay_gd = $@;
    if ($no_hay_gd) { # si no hay gd, no redimensiona
        return ('','','');
    };

    require GD;
    GD::Image->trueColor(1);

    my $proporcionmaxima; # Regla fija para mantener imagenes largas bajo control.
    my $ratio; # Razon de proporcionalidad para el resize.
    my ($ancho,$alto,$tipo,$anchofinal,$altofinal,$offsetx,$offsety); # Ancho, alto y tipo (gif o jpg) de la foto.
    my $imagen; # Objeto GD que contiene la imagen original.
    my $thumb;  # Objeto GD que contiene el thumbnail.
    my ($offsetx, $offsety, $anchocrop, $altocrop);

    # Si no se especifica ni ancho ni alto maximo, no hace nada.
    if ( (($anchomax eq '')||($anchomax == 0))
    && (($altomax eq '')||($altomax == 0)) ){
        # print "Error: No hay indicacion de ancho ni alto maximo.\n"; # debug
        return ('','','');
    };

    # Determina si se trata de un GIF, un JPG u otro.
    $tipo = &get_imag_extension($lafoto);
    if (!$tipo) {
        print STDERR "Error: El tipo de archivo no es valido. Debe ser .jpg  .gif o .png\n";
        return ('','','');
    };

    # Lee la imagen de origen
    open IN, $lafoto || return ('','','');
    if ($tipo eq 'jpg') {
        ref ($imagen = GD::Image->newFromJpeg(*IN)) || return ('','','');
    }elsif ($tipo eq 'png') {
        ref ($imagen = GD::Image->newFromPng(*IN)) || return ('','','');
    }elsif ($tipo eq 'gif') {
        ref ($imagen = GD::Image->newFromGif(*IN)) || return ('','','');
    }else {
        close IN;
        return ('','','');
    };
    close IN;

    # print "Truecolor = " . $imagen->isTrueColor() . "\n"; # debug

    # Se obtienen las dimensiones de la imagen
    ($ancho,$alto) = $imagen->getBounds();

    # Determina el lado que se ajustara.
    if ( ($altomax eq '') || ($altomax == 0) ) {
        # Ajusta el ancho.
        $ratio = $ancho / $anchomax;
        $offsetx = 0;
        $offsety = 0;
        $anchocrop = $ancho;
        $altocrop = $alto;

        if ($ratio == 0) { $ratio = 1; };
        return ('','','') if ($ratio <= 1);
        # print STDERR "RATIO[$ratio]\n;";
        ($anchofinal, $altofinal) = (int $ancho/$ratio, int $alto/$ratio);

    }elsif ( ($anchomax eq '') || ($anchomax == 0) ) {
        # Ajusta el alto.
        $ratio = $alto / $altomax;
        $offsetx = 0;
        $offsety = 0;
        $anchocrop = $ancho;
        $altocrop = $alto;

        if ($ratio == 0) { $ratio = 1; };
        return ('','','') if ($ratio <= 1);
        # print STDERR "RATIO[$ratio]\n;";
        ($anchofinal, $altofinal) = (int $ancho/$ratio, int $alto/$ratio);

    }else{

        if($cuadrar ne 'si') {
            # Ajusta el lado proporcionalmente mayor.
            $proporcionmaxima = $altomax/$anchomax;
            # Si la proporcion de ancho a alto es > proporcionmaxima entonces fija el alto en vez del ancho.
            if ($ancho * $proporcionmaxima < $alto) {
                $ratio = $alto / $altomax;
            }else{
                $ratio = $ancho / $anchomax;
            };
            $offsetx = 0;
            $offsety = 0;
            $anchocrop = $ancho;
            $altocrop = $alto;

            if ($ratio == 0) { $ratio = 1; };
            return ('','','') if ($ratio <= 1);
            # print STDERR "RATIO[$ratio]\n;";
            ($anchofinal, $altofinal) = (int $ancho/$ratio, int $alto/$ratio);

        } else {
            # Ajusta el lado proporcionalmente mayor.
            $proporcionmaxima = $anchomax / $altomax;
            $ratio = $ancho / $alto;
            if($ratio > $proporcionmaxima) {
                $anchocrop = $proporcionmaxima*$alto;
                $altocrop = $alto;
                $offsetx = ($ancho - $anchocrop)/2;
                $offsety = 0;

            } elsif($ratio < $proporcionmaxima) {
                $anchocrop = $ancho;
                $altocrop = $ancho/$proporcionmaxima;
                $offsetx = 0;
                $offsety = ($alto - $altocrop)/2;

            } else {
                $offsetx = 0;
                $offsety = 0;
                $anchocrop = $ancho;
                $altocrop = $alto;
            }
            $anchofinal = $anchomax;
            $altofinal = $altomax;
        }
    }

    if ($tipo eq 'jpg') {
        $thumb = new GD::Image($anchofinal,$altofinal);

    }else{
        # Si el formato es gif o png, usa paleta de 8 bits.
        # $thumb = new GD::Image($anchofinal,$altofinal,0);
        # CVI - Para evitar error con PNG muy complejos
        $thumb = new GD::Image($anchofinal,$altofinal,1);
        $thumb->alphaBlending(0);
        $thumb->saveAlpha(1)
    };

    # Crea el thumbnail.
    $thumb->copyResampled($imagen,0,0,$offsetx,$offsety,$anchofinal,$altofinal,$anchocrop,$altocrop);

    # No graba, sino que retorna el buffer binario de la foto para ser guardada por quien invoco a la funcion.
    my $bin_buffer;

    if ($tipo eq 'jpg') {
        $bin_buffer = $thumb->jpeg($JPEG_COMPRESSION);
    }else{
        $bin_buffer = $thumb->png();
    };

    return ($bin_buffer, $anchofinal, $altofinal);
};

# ---------------------------------------------------------------
sub make_resize {
    # Genera thumb de la imagen jpg o gif, basandose en el anchomax, altomax o en ambos.
    # Retorna: anchofinal, altofinal, buffer binario de la imagen.

    my $anchomax = $_[0];
    my $altomax = $_[1];
    my $lafoto = $_[2]; # full path

    my $no_hay_gd;
    eval "require GD;";    $no_hay_gd = $@;
    if ($no_hay_gd) { # si no hay gd, no redimensiona
        return ('','','');
    };

    require GD;
    GD::Image->trueColor(1);

    my $proporcionmaxima; # Regla fija para mantener imagenes largas bajo control.
    my $ratio; # Razon de proporcionalidad para el resize.
    my ($ancho,$alto,$tipo,$anchofinal,$altofinal); # Ancho, alto y tipo (gif o jpg) de la foto.
    my $imagen; # Objeto GD que contiene la imagen original.
    my $thumb;  # Objeto GD que contiene el thumbnail.

    # Si no se especifica ni ancho ni alto maximo, no hace nada.
    if ( (($anchomax eq '')||($anchomax == 0))
    && (($altomax eq '')||($altomax == 0)) ){
        # print "Error: No hay indicacion de ancho ni alto maximo.\n"; # debug
        return ('','','');
    };

    # Determina si se trata de un GIF, un JPG u otro.
    $tipo = &get_imag_extension($lafoto);
    if (!$tipo) {
        print STDERR "Error: El tipo de archivo no es valido. Debe ser .jpg  .gif o .png\n";
        return ('','','');
    };

    # Lee la imagen de origen
    open IN, $lafoto || return ('','','');
    if ($tipo eq 'jpg') {
        ref ($imagen = GD::Image->newFromJpeg(*IN)) || return ('','','');
    }elsif ($tipo eq 'png') {
        ref ($imagen = GD::Image->newFromPng(*IN)) || return ('','','');
    }elsif ($tipo eq 'gif') {
        ref ($imagen = GD::Image->newFromGif(*IN)) || return ('','','');
    }else {
        close IN;
        return ('','','');
    };
    close IN;

    # print "Truecolor = " . $imagen->isTrueColor() . "\n"; # debug

    ($ancho,$alto) = $imagen->getBounds();


    # print "Ancho y Alto = [$ancho] [$alto]\n"; # debug

    # print STDERR "RATIO[$ratio]\n;";
    ($anchofinal, $altofinal) = ($anchomax, $altomax);

    if ($tipo eq 'jpg') {
        $thumb = new GD::Image($anchofinal,$altofinal);
    }else{
        # Si el formato es gif o png, usa paleta de 8 bits.
        # $thumb = new GD::Image($anchofinal,$altofinal,0);
        # CVI - Para evitar error con PNG muy complejos
        $thumb = new GD::Image($anchofinal,$altofinal,1);
        $thumb->alphaBlending(0);
        $thumb->saveAlpha(1)
    };

    # Crea el thumbnail.
    $thumb->copyResampled($imagen,0,0,0,0,$anchofinal,$altofinal,$ancho,$alto);


    # No graba, sino que retorna el buffer binario de la foto para ser guardada por quien invoco a la funcion.
    my $bin_buffer;

    if ($tipo eq 'jpg') {
        $bin_buffer = $thumb->jpeg($JPEG_COMPRESSION);
    }else{
        $bin_buffer = $thumb->png();
    };

    return ($bin_buffer, $anchofinal, $altofinal);
};

# ---------------------------------------------------------------
sub make_crop {
    my ($srcX, $srcY, $width, $height, $path_foto) = @_;


    # Determina si se trata de un GIF, un JPG u otro.
    my $tipo = &get_imag_extension($path_foto);
    if (!$tipo) {
        print STDERR "Error: El tipo de archivo no es valido. Debe ser .jpg  .gif o .png\n";
        return ('','','');
    };

    # valida archivo original
    if ((! -f $path_foto) || (! -s $path_foto)) {
        print STDERR "Error: Archivo origen para el crop no es valido\n";
        return ('','','');
    };


    # Carga GD
    my $no_hay_gd;
    eval "require GD;";    $no_hay_gd = $@;
    if ($no_hay_gd) { # si no hay gd, no redimensiona
        return ('','','');
    };

    require GD;
    GD::Image->trueColor(1);

    # Lee la imagen de origen
    my $srcImage;
    open IN, $path_foto || return ('','','');
    if ($tipo eq 'jpg') {
        ref ($srcImage = GD::Image->newFromJpeg(*IN)) || return ('','','');
    }elsif ($tipo eq 'png') {
        ref ($srcImage = GD::Image->newFromPng(*IN)) || return ('','','');
    }elsif ($tipo eq 'gif') {
        ref ($srcImage = GD::Image->newFromGif(*IN)) || return ('','','');
    }else {
        close IN;
        return ('','','');
    };
    close IN;

    # Dimensiones del arch origen
    my ($ancho, $alto) = $srcImage->getBounds();

    # valida dimensiones del crop solicitado
    if (($srcX !~ /^[0-9]+$/) || ($srcY !~ /^[0-9]+$/) || ($width !~ /^[0-9]+$/) || ($height !~ /^[0-9]+$/)) {
        print STDERR "Error: Dimensiones del crop solicitado no son validas\n";
        return ('','','');
    };
    if ((($srcX + $width) > $ancho) || (($srcY + $height) > $alto)) {
        print STDERR "Error: Dimensiones del crop solicitado se encuentran fuera de rango.\n";
        return ('','','');
    };

    # Crea Imagen destino
    my $dstImage;
    if ($tipo eq 'jpg') {
        $dstImage = new GD::Image($width, $height);
    }else{
        # Si el formato es gif o png, usa paleta de 8 bits.
        # $dstImage = new GD::Image($width, $height, 0);
        # CVI - Para evitar error con PNG muy complejos
        $dstImage = new GD::Image($width, $height,1);
        $dstImage->alphaBlending(0);
        $dstImage->saveAlpha(1)
    };

    # Crea el crop
    # $image->copy($sourceImage,$dstX,$dstY,$srcX,$srcY,$width,$height)
    $dstImage->copy($srcImage, 0, 0, $srcX, $srcY, $width, $height);

    # No graba, sino que retorna el buffer binario de la foto para ser guardada por quien invoco a la funcion.
    my $bin_buffer;
    if ($tipo eq 'jpg') {
        $bin_buffer = $dstImage->jpeg($JPEG_COMPRESSION);
    } else {
        $bin_buffer = $dstImage->png();
    };

    return ($bin_buffer, $width, $height);

};

# ---------------------------------------------------------------
sub make_flip {
    my ($sentido, $path_foto) = @_;

    # Determina si se trata de un GIF, un JPG u otro.
    my $tipo = &get_imag_extension($path_foto);
    if (!$tipo) {
        print STDERR "Error: El tipo de archivo no es valido, path_foto[$path_foto]. Debe ser .jpg  .gif o .png\n";
        return '';
    };

    # valida archivo original
    if ((! -f $path_foto) || (! -s $path_foto)) {
        print STDERR "Error: Archivo origen para el flip no es valido[$path_foto]\n";
        return '';
    };


    # Carga GD
    my $no_hay_gd;
    eval "require GD;";    $no_hay_gd = $@;
    if ($no_hay_gd) { # si no hay gd, no redimensiona
        return '';
    };

    require GD;
    GD::Image->trueColor(1);

    # Lee la imagen de origen
    my $srcImage;
    open IN, $path_foto || return ('','','');
    if ($tipo eq 'jpg') {
        ref ($srcImage = GD::Image->newFromJpeg(*IN)) || return '';
    }elsif ($tipo eq 'png') {
        ref ($srcImage = GD::Image->newFromPng(*IN)) || return '';
    }elsif ($tipo eq 'gif') {
        ref ($srcImage = GD::Image->newFromGif(*IN)) || return '';
    }else {
        close IN;
        return '';
    };
    close IN;


    # Aplica la transformacion
    $srcImage->flipHorizontal() if ($sentido eq 'horizontal');
    $srcImage->flipVertical()   if ($sentido eq 'vertical');

    # No graba, sino que retorna el buffer binario de la foto para ser guardada por quien invoco a la funcion.
    my $bin_buffer;
    if ($tipo eq 'jpg') {
        $bin_buffer = $srcImage->jpeg($JPEG_COMPRESSION);
    } else {
        $bin_buffer = $srcImage->png();
    };

    return $bin_buffer;

};

# ---------------------------------------------------------------
sub make_rotate {
    my ($degrees, $path_foto) = @_;

    # Determina si se trata de un GIF, un JPG u otro.
    my $tipo = &get_imag_extension($path_foto);
    if (!$tipo) {
        print STDERR "Error: El tipo de archivo no es valido, path_foto[$path_foto]. Debe ser .jpg  .gif o .png\n";
        return '';
    };

    # valida archivo original
    if ((! -f $path_foto) || (! -s $path_foto)) {
        print STDERR "Error: Archivo origen para el rotate no es valido[$path_foto]\n";
        return '';
    };


    # Carga GD
    my $no_hay_gd;
    eval "require GD;";    $no_hay_gd = $@;
    if ($no_hay_gd) { # si no hay gd, no redimensiona
        return '';
    };

    require GD;
    GD::Image->trueColor(1);

    # Lee la imagen de origen
    my $srcImage;
    open IN, $path_foto || return ('','','');
    if ($tipo eq 'jpg') {
        ref ($srcImage = GD::Image->newFromJpeg(*IN)) || return '';
    }elsif ($tipo eq 'png') {
        ref ($srcImage = GD::Image->newFromPng(*IN)) || return '';
    }elsif ($tipo eq 'gif') {
        ref ($srcImage = GD::Image->newFromGif(*IN)) || return '';
    }else {
        close IN;
        return '';
    };
    close IN;



    # Crea Imagen destino (del mismo porte que la original)
    my ($width,$height) = $srcImage->getBounds();
    my $dstImage;
    if ($tipo eq 'jpg') {
        $dstImage = new GD::Image($width, $height);
    }else{
        # Si el formato es gif o png, usa paleta de 8 bits.
        # $dstImage = new GD::Image($width, $height, 0);
        # CVI - Para evitar error con PNG muy complejos
        $dstImage = new GD::Image($width, $height,1);
        $dstImage->alphaBlending(0);
        $dstImage->saveAlpha(1)
    };

    # Aplica la transformacion
    $dstImage = $srcImage->copyRotate90() if ($degrees == 90);
    $dstImage = $srcImage->copyRotate180() if ($degrees == 180);
    $dstImage = $srcImage->copyRotate270() if ($degrees == 270);

    # No graba, sino que retorna el buffer binario de la foto para ser guardada por quien invoco a la funcion.
    my $bin_buffer;
    if ($tipo eq 'jpg') {
        $bin_buffer = $dstImage->jpeg($JPEG_COMPRESSION);
    } else {
        $bin_buffer = $dstImage->png();
    };

    return $bin_buffer;

};

# ---------------------------------------------------------------
sub get_imag_extension {
    # Determina si la extension de la imagen original es valida para ser tratada con las funciones
    # de esta lib.
    my $lafoto = $_[0];
    my $tipo;
    if ($lafoto =~ /\.jpe?g?$/i) {
        $tipo = 'jpg';
    }elsif ($lafoto =~ /\.gif$/i) {
        $tipo = 'gif';
    }elsif ($lafoto =~ /\.png$/i) {
        $tipo = 'png';
    };
    return $tipo;
};

# ---------------------------------------------------------------
sub calcular_proporcion_img {
    # Calculas las medidas proporcionales para redimencionar la imagen sin deformarse.
    my $wfoto  = $_[0];
    my $hfoto   = $_[1];
    my $wmax  = $_[2];
    my $hmax  = $_[3];
    my $percent;

    if ($wfoto > $wmax) {
        $percent = (($wmax * 100) / $wfoto);
        $wfoto = $wmax;
        $hfoto = ($hfoto * ($percent / 100));
    };

    if ($hfoto > $hmax) {
        $percent = (($hmax * 100) / $hfoto);
        $hfoto = $hmax;
        $wfoto = ($wfoto * ($percent / 100));
    };

    return ($wfoto, $hfoto);

};
# ---------------------------------------------------------------
# Para centralizar la escritura de la imagen
sub write_image {

    my ($dst_path, $binfoto) = @_;
    return unless($binfoto);

    my $tipo = &get_imag_extension($dst_path);
    if($tipo eq 'png') {
        #~ &glib_fildir_02::write_file($dst_path.'-orig.png', $binfoto);
        #~ $binfoto = &optimize_png_image($binfoto);
    }

    &glib_fildir_02::write_file($dst_path, $binfoto);

    if($tipo eq 'jpg') {
        &optimize_jpg_image($dst_path);
    }
}

# ---------------------------------------------------------------
# Revisa si existe las libreria App::PNGCrush o Image::JpegTran
# para optimizar con lossless compression los pngs o jpgs, respectivamente
sub optimize_jpg_image {

    my ($filename) = @_;

    #~ http://search.cpan.org/~mons/Image-JpegTran-0.02/lib/Image/JpegTran.pm
    eval "require Image::JpegTran;";  my $no_hay_libreria = $@;
    return if ($no_hay_libreria);
    #~ print STDERR "Modulo Image::JpegTran instalado...\n";
    require Image::JpegTran;

    #~ Creamos archivo temporal para trabajar
    use File::Temp;
    my $fh = File::Temp->new();
    my $fname = $fh->filename;
    Image::JpegTran::jpegtran($filename, $fname, copy => 'none', optimize => 1);
    
    use File::Copy qw(move);
    #~ copy($filename, $filename.'-orig.jpg');
    move($fname, $filename);
    chmod 0644, $filename;

}

# ---------------------------------------------------------------
# Revisa si existe las libreria App::PNGCrush o Image::JpegTran
# para optimizar con lossless compression los pngs o jpgs, respectivamente
sub optimize_png_image {

    my ($binfoto) = @_;

    #~ http://search.cpan.org/~acmcmen/Image-Pngslimmer-0.30/lib/Image/Pngslimmer.pm
    eval "require Image::Pngslimmer;";  my $no_hay_libreria = $@;
    return $binfoto if ($no_hay_libreria);

    #~ print STDERR "Modulo Image::Pngslimmer instalado...";
    require Image::Pngslimmer;

    $binfoto = Image::Pngslimmer::discard_noncritical($binfoto);
    #~ $binfoto = Image::Pngslimmer::filter($binfoto);
    #~ $binfoto = Image::Pngslimmer::zlibshrink($binfoto);
    return $binfoto;
}

# ---------------------------------------------------------------
1;
# -------------------------------END LIBRERIA--------------------
