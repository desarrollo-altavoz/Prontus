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
package lib_captcha;

use strict;
use Digest::SHA  qw(sha1 sha1_hex sha1_base64);
use glib_fildir_02;
use glib_str_02;

# variables globales del paquete
our $MAX_FILES = 2000; # NRO. MAXIMO DE ARCHIVOS QUE PUEDEN EXISTIR SIMULTANEAMENTE
our $MAX_TIME = 600; # Tiempo máximo antes de borra los captcha antiguos -> 10 mins.

our $FORECOLOR = '0,0,0'; # COLOR LETRAS
our $BACKCOLOR = '255,255,255'; # COLOR FONDO
our $TTF = './fontcaptcha.ttf';
our $ERRCODE = 0;
our %ERRGLOSA = (
    0,'',
    1,'$folder_captcha_files no especificado al setear captcha',
    2,'Nro. de archivos en $lib_captcha::folder_captcha_files excede $lib_captcha::MAX_FILES',
    3,'No se pudo chequear directorio para captcha files',
    4,'No se especifico string captcha a validar',
    5,'No se especifico carpeta de captcha files al validar captcha',
    6,'No se encontro la libreria perl GD en el sistema',
    7,'No se encontro archivo TTF'
);
our $DIR_CGI_CPAN;


# --------------------------------------------------------------------#
sub set_captcha {
  # Implementa captcha de 4 caracteres case-insens, para lo cual simula manejo de sesion.
  # Detalles:
  # Obtiene str de 4 chars aleatorio y lo codifica en sha1_base64 y lo mete dentro de un archivo cuyo nombre es el pid en sha1_hex
  # Para que el proceso que valida pueda componer el nombre del archivo donde se guardo el cpatcha, este se guarda
  # en una cookie cuyo nombre es la ip del request mas el nombre del dir pasado por param., la cookie se encripta en sha1_hex

  # param1: nombre del dir donde guardar el archivo con el captcha codificado.
  # Este directorio quedara dentro de cgi-cpn/prontus_temp

  # Retorna:
  # 0) buffer binario de la imagen


  # Uso:
  # En el script que setea e imprime el captcha:
  #  $lib_captcha::TTF = $ENV{'DOCUMENT_ROOT'} . "/$DIR_CGI_CPAN/fontcaptcha.ttf"; # OBLIGATORIO para los scripts que estan fuera del cgi-cpn, OPTATIVO para los del cgi-cpn
  #  $lib_captcha::MAX_FILES = 10; # OPTATIVO
  #  $lib_captcha::FORECOLOR = '0,61,122'; # OPTATIVO, Color azul prontus.
  #  $lib_captcha::BACKCOLOR = '227,241,251'; # OPTATIVO, Color celeste prontus.
  #  my ($img_captcha) = &lib_captcha::set_captcha('captcha_posting');
  #  die "no se pudo setear captcha [$lib_captcha::ERRCODE][$lib_captcha::ERRGLOSA{$lib_captcha::ERRCODE}]" if (!$img_captcha);
  #  &lib_captcha::print_img($img_captcha);

  my ($folder_captcha_files) = $_[0];

  if (!$folder_captcha_files) {
    $ERRCODE = 1;
    return '';
  };


  # nombre de la cookie dentro de la cual se guardara el nombre del archivo
  my $nom_cookie = $ENV{'REMOTE_ADDR'} . $folder_captcha_files;

  $nom_cookie = &Digest::SHA::sha1_hex($nom_cookie);

  # nombre del archivo en el cual se guardará el captcha encriptado
  my $nom_file_captcha;
  # Si ya hay una cookie seteada, se utiliza el nombre de archivo que hay dentro,
  # de manera de no crear otro cuando el perico es el mismo
  my %cookies = &get_cookies();
  if ($cookies{$nom_cookie} ne '') {
    $nom_file_captcha = $cookies{$nom_cookie};
  }
  else {
    $nom_file_captcha = &Digest::SHA::sha1_hex($$);
  };

  # Obtencion del string del captcha y codificacion del mismo
  my $str = &glib_str_02::random_string(4);
  my $str_coded = &Digest::SHA::sha1_base64(lc $str); # captcha es case-insens

  my $path_captcha_file = &get_path_captcha_file($folder_captcha_files, $nom_file_captcha);
  return '' if (!$path_captcha_file);

  # Obtener imagen del captcha
  my $buf_img = &get_captcha_imag($str);
  return '' if (!$buf_img);

  # Grabar archivo con el captcha codificado adentro
  &glib_fildir_02::write_file($path_captcha_file, $str_coded);

  # Setear cookie
  &set_simple_cookie($nom_cookie, $nom_file_captcha);

  return $buf_img;

};
# --------------------------------------------------------------------#
sub print_img {
  my $img_captcha = $_[0];
  return if (!$img_captcha);
  binmode STDOUT;
  print "Content-type: image/jpeg\n\n";
  print $img_captcha;
};
# --------------------------------------------------------------------#
# lanza el borrado de archivos antiguos
sub garbage_collector {
    my ($dir) = $_[0];
    my(@entries,@stats,$entry);
    if (! (-d $dir)) {
        return 0;
    };

    # Intenta leer el contenido del directorio.
    my $num_files;
    if (opendir(DIR, $dir)) {
        closedir DIR;
    } else {
        $ERRCODE = 3;
        return 0;
    };

    # se lanza el garbage collector en segundo plano
    use FindBin '$Bin';
    $Bin =~ s/\/cgi\-\w+$/\/$DIR_CGI_CPAN/;

    my $cmd = "/usr/bin/perl $Bin/prontus_garbage_collector.pl $dir $MAX_TIME $MAX_FILES >/dev/null 2>&1 &";
    system($cmd);

    return 1;
}; # garbage_collector
# --------------------------------------------------------------------------- #

sub get_path_captcha_file {
    my ($folder_captcha_files, $nom_file_captcha) = @_;

    use FindBin '$Bin';
    my $dir = "$Bin/prontus_temp/$folder_captcha_files";

    if (!&glib_fildir_02::check_dir($dir)) {
        $ERRCODE = 3;
        print STDERR "check_dir error en [$dir]\n";
        return '';
    };

    return '' if (!&garbage_collector($dir));
    my $path_captcha_file = $dir . '/' . $nom_file_captcha;

    return $path_captcha_file;
};
# --------------------------------------------------------------------------- #
sub valida_captcha {
  # Uso:
  # my $str = 'ABCDE'; # string ingresado por el user
  # if (&lib_captcha::valida_captcha($str, 'captcha_posting')) {
  #   print "OK";
  # }
  # else {
  #   print "FAIL [$lib_captcha::ERRCODE]"; # code 0 es fail normal
  # };

  # Si no hay gd, valida ok sin chequear nada
  my $no_hay_gd;
  eval "require GD;";    $no_hay_gd = $@;
  if ($no_hay_gd) { # si no hay gd, no redimensiona
    $ERRCODE = 6;
    return 0;
  };

  my ($str_a_validar, $folder_captcha_files) = @_;
  if (!$str_a_validar) {
    $ERRCODE = 4;
    return 0;
  };
  if (!$folder_captcha_files) {
    $ERRCODE = 5;
    return 0;
  };
  # Obtiene nombre de la cookie para poder leerla y sacar de ahi el nombre del archivo donde se encuentra el captcha
  my $nom_cookie = $ENV{'REMOTE_ADDR'} . $folder_captcha_files;
  $nom_cookie = &Digest::SHA::sha1_hex($nom_cookie);
  my %cookies = &get_cookies();
  my $nom_file_captcha = $cookies{$nom_cookie};
  # lee archivo
  my $path_captcha_file = &get_path_captcha_file($folder_captcha_files, $nom_file_captcha);
  return 0 if (!$path_captcha_file);
  my $str_coded = &glib_fildir_02::read_file($path_captcha_file);
  # print STDERR "nom_file_captcha[$nom_file_captcha] path_captcha_file[$path_captcha_file] str_coded[$str_coded] str_a_validar[$str_a_validar]\n";
  if (&Digest::SHA::sha1_base64(lc $str_a_validar) eq $str_coded) {
    unlink $path_captcha_file;
    &set_simple_cookie($nom_cookie, '');
    return 1;
  }
  return 0;

};

# --------------------------------------------------------------------------- #
# Retorna la data correspondiente a una imagen JPEG de 150 x 60 pixeles,
# que contiene dibujado el string pasado como parametro.
sub get_captcha_imag {

  # Si no hay gd, no genera nada
  my $no_hay_gd;
  eval "require GD;";    $no_hay_gd = $@;
  if ($no_hay_gd) { # si no hay gd, no redimensiona
    $ERRCODE = 6;
    return '';
  };

  if (! -f $TTF) { # verfica archivo ttf
    $ERRCODE = 7;
    return '';
  };

  require GD;

  my $string = $_[0]; # String de entrada. Debe ser de 4 letras.
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

  return $salida->jpeg(50); # 0 - 100 = calidad. Esto es para hacer difusa la imagen.

};

#-------------------------------------------------------------------------#
# 1.2
sub set_simple_cookie {
# Setea una cookie temporal para la sesion.
  my($name, $value) = @_;
  print 'Set-Cookie: ';
  print ("$name=$value; path=/; \n"); # 1.10
};

#------------------------------------------------------------------------#
sub get_cookies {
# Get Cookies desde la variable de ambiente ENV.
  # Las cookies estan separadas por ";" y un espacio,
  # esto las esplitea y retorna un hash de cookies.

  my(@rawCookies) = split (/; /,$ENV{'HTTP_COOKIE'});
  my(%cookies);
  my($key, $val); # 1.3

  foreach(@rawCookies){
      ($key, $val) = split (/=/,$_);
      $cookies{$key} = $val;
  };

  return %cookies;
};

#------------------------------------------------------------------------#
sub check_captcha_prontus {
    # Funcion que gestiona la invocacion a la rutina que valida el captcha.
    # Se puede utilizar para no tener que escribir todo esto cada vez en los programas que chequean captcha.
    my ($captcha_input, $captcha_type) = @_;
    $captcha_input =~ s/[^\w]//sg;
    if (!&lib_captcha::valida_captcha($captcha_input, "captcha_$captcha_type")) {
        print STDERR "Captcha no es valido o bien no fue posible verificarlo ERRCODE[$lib_captcha::ERRCODE][$lib_captcha::ERRGLOSA{$lib_captcha::ERRCODE}]\n";
        # Si no se logra validar el captcha, solo se acepta code 6 q significa q no hay GD
        if ($lib_captcha::ERRCODE != 6) {
            return 'El c&oacute;digo de verificaci&oacute;n ingresado no es v&aacute;lido.';
        };
    };
    return ''; # todo ok
};

#-------------------------------------------------------------------------#
return 1;
