#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# Funciones para utilizar captcha sin utilizar sesiones.
package lib_captcha2;

use strict;
use Digest::SHA  qw(sha1 sha1_hex sha1_base64);
use glib_fildir_02;
use glib_str_02;

our $MAX_FILES = 2000; # NRO. MAXIMO DE ARCHIVOS QUE PUEDEN EXISTIR SIMULTANEAMENTE
our $TIME_OLD_FILES = 600; # 600 segundos, 10 minutos.
our $FORECOLOR = '0,0,0'; # COLOR LETRAS
our $BACKCOLOR = '255,255,255'; # COLOR FONDO
our $ERRCODE = 0;

our $TTF = './fontcaptcha.ttf';

our %ERR_MSGS = (
    'MSG_CAPTCHA_SYSTEM' => 'Error interno del sistema',
    'MSG_CAPTCHA_VOID' => 'Debe ingresar el c&oacute;digo de seguridad',
    'MSG_CAPTCHA_INVALID' => 'El c&oacute;digo de seguridad no es v&aacute;lido',
    'MSG_CAPTCHA_EXPIRED' => 'El c&oacute;digo de seguridad ha expirado',
    'MSG_CAPTCHA_TYPE' => 'Petición invalida, especifique el tipo de captcha',
    'MSG_CAPTCHA_BADTYPE' => 'El tipo de captcha, no es v&aacute;lido',
    'MSG_CAPTCHA_BUSY' => 'Servidor ocupado, no se pudo generar la imagen del captcha',
    'MSG_CAPTCHA_BLOCKED' => 'Petición invalida, usuario restringido'
);

our $DOCUMENT_ROOT;
our $PATH_CAPTCHA_IMG;
our $DIR_CGI_CPAN;

#--------------------------------------------------------------------------------------------------#
sub init {
    my ($DOC_ROOT, $DIR_CGI) = @_;

    # Se cargan las variables generales
    $DOCUMENT_ROOT = $DOC_ROOT;
    $PATH_CAPTCHA_IMG = "/imag/prontus_captcha";
    $TTF = "$lib_captcha2::DOCUMENT_ROOT/$DIR_CGI/fontcaptcha.ttf";

    # faltaria cargar un arreglo con mensajes segun idioma
};
#--------------------------------------------------------------------------------------------------#
sub validar_tipo {
    my $captcha_type = $_[0];
    if ($captcha_type !~ /^(form|posting|enviar|cpan)$/) {
        return 0;
    } else {
        return 1;
    }
}
#--------------------------------------------------------------------------------------------------#
sub valida_captcha {
    my ($captcha_input, $captcha_code, $captcha_type, $captcha_img) = @_;
    $captcha_input =~ s/[^\w]//sg;

    if(! &validar_tipo($captcha_type)) {
        print STDERR "Captcha no valido captcha_type[$captcha_type]\n";
        return $ERR_MSGS{'MSG_CAPTCHA_BADTYPE'};
    };

    if($captcha_img && $captcha_code) {

        # Se revisa que los datos de la librería hayan sido iniciados
        unless($lib_captcha2::PATH_CAPTCHA_IMG && $lib_captcha2::DOCUMENT_ROOT) {
            print STDERR "lib_captcha2 no ha sido inicializada\n";
            return $ERR_MSGS{'MSG_CAPTCHA_SYSTEM'};
        }

        # Si no hay gd, No se valida nada, arroja error de sistema
        my $no_hay_gd;
        eval "require GD;";    $no_hay_gd = $@;
        if ($no_hay_gd) { # si no hay gd, no redimensiona
            print STDERR "No se encontro la libreria perl GD en el sistema\n";
            return $ERR_MSGS{'MSG_CAPTCHA_SYSTEM'};
        };

        # El codigo de validacion no puede ser vacio
        if($captcha_input eq '') {
            print STDERR "No venia el codigo de seguridad: captcha_input[$captcha_input]\n";
            return $ERR_MSGS{'MSG_CAPTCHA_VOID'};
        }

        # Se revisa que la imagen exista
        if(! -f "$lib_captcha2::DOCUMENT_ROOT$lib_captcha2::PATH_CAPTCHA_IMG/$captcha_type/$captcha_img") {
            print STDERR "La imagen no existe: $lib_captcha2::DOCUMENT_ROOT$lib_captcha2::PATH_CAPTCHA_IMG/$captcha_type/$captcha_img\n";
            return $ERR_MSGS{'MSG_CAPTCHA_EXPIRED'};
        } else {
            # Si la imagen existe, se borra para evitar nueva invocacion
            &lib_captcha2::delete_captcha_img($captcha_type, $captcha_img);
        }

        # Finalemente se valida todo
        my $encoded = &make_hash($captcha_input);
        if($encoded ne $captcha_code) {
            print STDERR "Los codigos de validacion son distintos: encoded[$encoded] - captcha_code[$captcha_code]\n";
            return $ERR_MSGS{'MSG_CAPTCHA_INVALID'};
        }
        return '';

    } else {
        # Captcha antiguo con sesiones
        my $msg_err_captcha = &lib_captcha::check_captcha_prontus($captcha_input, $captcha_type);
        return $msg_err_captcha;
    };
};

#--------------------------------------------------------------------------------------------------#
sub make_hash {
    my $str = $_[0];
    my $pass1 = &Digest::SHA::sha1_hex($str);
    my $pass2 = &Digest::SHA::sha1_base64($pass1) . $str;
    my $pass3 = &Digest::SHA::sha1_hex($pass2);
    return $pass3;

};

#--------------------------------------------------------------------------------------------------#
sub get_img_name {
    my $hash = $_[0];

    my $str_parts = join ' ', unpack '(A4)*', $hash;
    my @parts = split(" ", $str_parts);
    my @new_order = (9,6,3,0,5,8,2,7,1,4);
    my $new_str;

    foreach my $num (@new_order) {
        $new_str .= $parts[$num];
    };

    return $new_str.".jpg";
};

#--------------------------------------------------------------------------------------------------#
sub delete_captcha_img {

    my ($captcha_type, $captcha_img) = @_;

    # Se revisa que los datos de la librería hayan sido iniciados
    unless($lib_captcha2::PATH_CAPTCHA_IMG && $lib_captcha2::DOCUMENT_ROOT) {
        print STDERR "lib_captcha2 no ha sido inicializada\n";
        return $ERR_MSGS{'MSG_CAPTCHA_SYSTEM'};
    }

    &glib_fildir_02::check_dir("$lib_captcha2::DOCUMENT_ROOT$lib_captcha2::PATH_CAPTCHA_IMG/$captcha_type");
    if(-f "$lib_captcha2::DOCUMENT_ROOT$lib_captcha2::PATH_CAPTCHA_IMG/$captcha_type/$captcha_img") {
        unlink "$lib_captcha2::DOCUMENT_ROOT$lib_captcha2::PATH_CAPTCHA_IMG/$captcha_type/$captcha_img";
    }
};

#--------------------------------------------------------------------------------------------------#
sub make_captcha_img {

    # Si no hay gd, no genera nada
    my $no_hay_gd;
    eval "require GD;";    $no_hay_gd = $@;
    if ($no_hay_gd) { # si no hay gd, no redimensiona
        print STDERR "No se encontro la libreria perl GD en el sistema\n";
        return $ERR_MSGS{'MSG_CAPTCHA_SYSTEM'};
    };

    if (! -f $TTF) { # verfica archivo ttf
        print STDERR "No se encontro el archivo de fuente para generar la imagen[$TTF]\n";
        return $ERR_MSGS{'MSG_CAPTCHA_SYSTEM'};
    };

    require GD;

    my $string = $_[0]; # String de entrada. Debe ser de 4 letras.
    my $filename_path = $_[1];
    my $forecolor = $FORECOLOR; # en rgb (por defecto es negro)
    my $backcolor = $BACKCOLOR; # en rgb (por defecto es blanco)
    my $trueTypeFont = $TTF; # Ubicacion del archivo ttf.
    my @string = split(//,$string);
    my $imgHeight = 45; # Alto de las imagene de trabajo.
    my $imgWidth = 85;  # Ancho de las imagenes de trabajo.
    my $salidaHeight = 35; # Alto de la imagen de salida.
    my $salidaWidth = 80; # Alto de la imagen de salida.
    my $fontSize = 18; # Tamano del font en puntos.
    my $posMargin = 2; # Margen que se le da a la posicion de la letra.
    my $maxAngle = 0.2; # Maxima inclinacion, en radianes.
    my $letra = GD::Image->new($imgWidth,$imgHeight,1); # Imagen para dibujar cada letra.
    my $image = GD::Image->new($imgWidth,$imgHeight,1); # La imagen de trabajo.
    my $salida = GD::Image->new($salidaWidth,$salidaHeight,1); # La imagen de salida.

    $forecolor =~ s/[^\d\,]//g;
    $backcolor =~ s/[^\d\,]//g;
    $forecolor = '0,0,0' if (!$forecolor) || ($forecolor !~ /^\d{1,3}\,\d{1,3}\,\d{1,3}$/);
    $backcolor = '255,255,255' if (!$backcolor) || ($backcolor !~ /^\d{1,3}\,\d{1,3}\,\d{1,3}$/);
    my ($r1, $g1, $b1) = split(/\,/, $forecolor);
    my ($r2, $g2, $b2) = split(/\,/, $backcolor);
    my $black = $image->colorAllocate($r1, $g1, $b1);
    my $white = $image->colorAllocate($r2, $g2, $b2);

    my ($dstX,$dstY,$srcX,$srcY,$width,$height,$miny,$maxy,$percent,$ancho,$i);
    my (@bounds);
    # Limpia imagen de trabajo.
    # $image->filledRectangle($x1,$y1,$x2,$y2,$color)
    $image->filledRectangle(0,0,$imgWidth+1,$imgHeight+1,$white);
    # Lugar de copiado de la letra en la imagen de trabajo.
    $dstX = 1;
    # Coordenadas Y minima y maxima.
    $miny = $salidaHeight;
    $maxy = 0;
    for($i=0; $i<=$#string; $i++) {
        # Escribe una letra en la imagen para escribir letras.
        # Primero, borra la imagen.
        $letra->filledRectangle(0,0,$imgWidth+1,$imgHeight+1,$white);
        # @bounds = $image->stringFT($fgcolor,$fontname,$ptsize,$angle,$x,$y,$string)
        # @bounds[0,1]  Lower left corner (x,y)
        # @bounds[2,3]  Lower right corner (x,y)
        # @bounds[4,5]  Upper right corner (x,y)
        # @bounds[6,7]  Upper left corner (x,y)
        # Dibuja la letra. x e y se aumentan en $posMargin para compensar el efecto de la inclinacion aleatoria.
        @bounds = $letra->stringFT($black,$trueTypeFont,$fontSize,$maxAngle*2*(0.5-rand),$posMargin,$fontSize+$posMargin,$string[$i]);
        $ancho = $bounds[2] - $bounds[0];
        # Copia la letra en la imagen de salida.
        $dstY = 1 + int(rand($posMargin*2));
        $srcX = 1;
        $srcY = 1;
        $width = $salidaWidth;
        $height = $salidaHeight;
        $percent = 40 + int(rand(20)); # % de merge es 50 en promedio.
        $image->copyMerge($letra,$dstX,$dstY,$srcX,$srcY,$width,$height,$percent);
        $dstX += $ancho + int(rand(int($posMargin/2))) - $posMargin;
        if (($bounds[7]+$dstY) < $miny) { $miny = $bounds[7] + $dstY; };
        if (($bounds[1]+$dstY) > $maxy) { $maxy = $bounds[1] + $dstY; };
    };
    # Borra imagen de salida.
    $salida->filledRectangle(0,0,$salidaWidth+1,$salidaHeight+1,$white);
    # $image->copy($sourceImage,$dstX,$dstY,$srcX,$srcY,$width,$height);
    # Calcula parametros para centrar la imagen en la salida.
    $width = $dstX + $posMargin*2;
    $dstX = int(($salidaWidth - $dstX - $posMargin)/2);
    $dstY = int(($salidaHeight - ($maxy - $miny))/2) + 2;
    $srcX = 1;
    $srcY = $miny;
    $height = $salidaHeight;
    $salida->copy($image,$dstX,$dstY,$srcX,$srcY,$width,$height);
    # print "dstX=$dstX dstY=$dstY srcX=$srcX srcY=$srcY width=$width height=$height\n"; # denug

    open (FILE, ">$filename_path");
    binmode FILE;
    print FILE $salida->jpeg(50);
    close FILE;
    return '';
};

#--------------------------------------------------------------------------------------------------#
sub check_max_files {
    my $path = $_[0];
    my $ret = `ls -f $path*.jpg | wc -l`;
    $ret =~ s/[\n\r\t]//;
    return $ret;
};

#--------------------------------------------------------------------------------------------------#
sub garbage_collector {
    my $path = $_[0];
    use FindBin '$Bin';
    $Bin =~ s/\/cgi\-\w+$/\/$DIR_CGI_CPAN/;
    my $cmd = "/usr/bin/perl $Bin/prontus_garbage_collector.pl $path $TIME_OLD_FILES $MAX_FILES >/dev/null 2>&1 &";
    system($cmd);
};

#--------------------------------------------------------------------------------------------------#
sub print_response {

    my ($img, $path, $code, $msg) = @_;

    my $resp;
    #~ my $json = new JSON;
    $resp->{'img'} = $img;
    $resp->{'path'} = $path;
    $resp->{'code'} = $code;
    $resp->{'msg'} = $msg;

    print &JSON::to_json($resp);
    exit;
};

return 1;
