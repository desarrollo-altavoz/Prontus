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
# Librería usada por los post_procesos de carga de imagenes en
# galeria para chilevision
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 1.0   26/05/2008  CVI
#
# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# TODO:
#   - Eliminar actualiza_url y cambiarla por una función que agregue
#       todos los parámetros de un %hash al xml.
#
# DECLARACIONES GLOBALES.
# ------------------------

package lib_galeria;

use JSON;
use strict;

sub list_module {
    my $module = shift;
    no strict 'refs';
    return grep { defined &{"$module\::$_"} } keys %{"$module\::"}
}

# ------------------------------------------------
# conviernte un hash en json
sub generaJson {
    my $hash = $_[0];
    if ($JSON::VERSION =~ /^1\./) {
        my $json = new JSON;
        return $json->objToJson($hash);
    } else {
        return &JSON::to_json($hash);
    }
}

# ------------------------------------------------
# Actualiza el campo en el xml
sub actualizaCampo {
  my ($buffer, $campo, $valor) = ($_[0], $_[1], $_[2]);

  if($buffer =~ /(<$campo>\s*<!\[CDATA\[).*?(\]\]>\s*<\/$campo>)/igs) {
    $buffer =~ s/(<$campo>\s*<!\[CDATA\[).*?(\]\]>\s*<\/$campo>)/$1$valor$2/igs

  } elsif($buffer =~ /(<$campo>\s*).*?(\s*<\/$campo>)/igs) {
    $buffer =~ s/(<$campo>\s*).*?(\s*<\/$campo>)/$1$valor$2/igs

  } else {
    my $new_field = "<$campo>\n<![CDATA[$valor]]>\n</$campo>\n";
    if($buffer =~ /<\/_PUBLIC>/) {
      $buffer =~ s/(<\/_PUBLIC>)/$new_field$1/igs;
    } else {
      print STDERR "No se pudo actualizar el XML [$campo] [$valor]\n";
      return $buffer;
    }
  }

  return $buffer;
}

# ------------------------------------------------
# Elimina el campo del xml
sub eliminaCampo {
  my ($buffer, $campo) = ($_[0], $_[1]);

  if($buffer =~ /(<$campo>\s*<!\[CDATA\[).*?(\]\]>\s*<\/$campo>)/igs) {
    $buffer =~ s/(<$campo>\s*<!\[CDATA\[).*?(\]\]>\s*<\/$campo>)//igs

  } elsif($buffer =~ /(<$campo>\s*).*?(\s*<\/$campo>)/igs) {
    $buffer =~ s/(<$campo>\s*).*?(\s*<\/$campo>)//igs

  }
  return $buffer;
}

# ------------------------------------------------
sub get_ancho_foto {
    my ($xml_data, $path_foto) = @_;
    return &get_dim_foto($xml_data, $path_foto, 'w');
};
# ------------------------------------------------
sub get_altura_foto {
    my ($xml_data, $path_foto) = @_;
    return &get_dim_foto($xml_data, $path_foto, 'h');
};

# ------------------------------------------------
sub get_dim_foto {
    my ($xml_data, $path_foto, $dim) = @_;
    my $foto;
    my ($nro_foto, $inner);
    if($path_foto ne '' && $path_foto =~ /\/([^\/]*?)$/i) {
        $foto = $1;
        if($xml_data =~ /<(foto_\d+)>(.*?$foto.*?)<\/\1>/is) {
            $nro_foto = $1;
            $inner = $2;
            if($inner =~ /<_$dim$nro_foto>(\d*?)<\/_$dim$nro_foto>/i) {
                return $1;
            }
        }
    }
    return '';
}

# ------------------------------------------------
sub html_to_text {
    my($toencode) = $_[0];
    $toencode =~ s/\r\n/ /sg;
    $toencode =~ s/\n/ /sg;
    $toencode =~ s/\r/ /sg;
    $toencode =~ s/<.*?>/ /sg;
    $toencode =~ s/ {2,}/ /sg;
    $toencode =~ s/ $//sg;
    $toencode =~ s/^ //sg;
    $toencode =~ s/'/\x92/sg; # cambia comilla vertical por comilla inclinada, para compatib. JS
    $toencode =~ s/&#39;/\xB4/sg; # cambia comilla vertical por comilla inclinada, para compatib. JS
    return $toencode;
}
# ------------------------------------------------
sub make_square_thumbnail {
  # Genera thumb de la imagen jpg o gif, basandose en el anchomax, altomax o en ambos.
  # Retorna: anchofinal, altofinal, buffer binario de la imagen.

  my $dim = $_[0]; # full path
  my $lafoto = $_[1]; # full path

  my $anchofinal = $dim;
  my $altofinal = $dim;

  my $no_hay_gd;
  eval "require GD;";    $no_hay_gd = $@;
  if ($no_hay_gd) { # si no hay gd, no redimensiona
    warn('si no hay gd, no redimensiona');
    return ('','','');
  };

  require GD;
  GD::Image->trueColor(1);

  my $proporcionmaxima; # Regla fija para mantener imagenes largas bajo control.
  my $ratio; # Razon de proporcionalidad para el resize.
  my ($ancho,$alto,$tipo,$anchosquare,$altosquare); # Ancho, alto y tipo (gif o jpg) de la foto.
  my $imagen; # Objeto GD que contiene la imagen original.
  my $thumb;  # Objeto GD que contiene el thumbnail.

  # Si no se especifica ni ancho ni alto maximo, no hace nada.
  if (($dim eq '')||($dim == 0)){
    # print "Error: No hay indicacion de ancho ni alto maximo.\n"; # debug
    warn('No hay indicacion de ancho ni alto maximo');
    return ('','','');
  };

  # Determina si se trata de un GIF, un JPG u otro.
  if ($lafoto =~ /\.jpe?g?$/i) {
    $tipo = 'jpg';
  }elsif ($lafoto =~ /\.gif$/i) {
    $tipo = 'gif';
  }elsif ($lafoto =~ /\.png$/i) {
    $tipo = 'png';
  }else{
    # print "Error: El tipo de archivo no es valido. Debe ser .jpg o .gif\n"; # debug
    warn('Error: El tipo de archivo no es valido. Debe ser .jpg o .gif');
    return ('','','');
  };

  # Lee la imagen.
  open IN, $lafoto || return ('','','');
  if ($tipo eq 'jpg') {
    ref ($imagen = GD::Image->newFromJpeg(*IN)) || return ('','','');
  }elsif ($tipo eq 'png') {
    ref ($imagen = GD::Image->newFromPng(*IN)) || return ('','','');
  }elsif ($tipo eq 'gif') {
    ref ($imagen = GD::Image->newFromGif(*IN)) || return ('','','');
  }else {
    close IN;
    warn('Error: No se pudo leer la imagen');
    return ('','','');
  };
  close IN;

  # print "Truecolor = " . $imagen->isTrueColor() . "\n"; # debug
  ($ancho,$alto) = $imagen->getBounds();

  # print "Ancho y Alto = [$ancho] [$alto]\n"; # debug

  # Determina el lado que se ajustara.
  my ($offsetx, $offsety);
  if ($ancho > $alto) {
    # Ajusta el ancho.
    $offsetx = ($ancho - $alto)/2;
    $offsety = 0;
    $anchosquare = $alto;
    $altosquare = $alto;
  } elsif ($ancho < $alto) {
    # Ajusta el alto.
    $offsetx = 0;
    $offsety = ($alto - $ancho)/2;
    $anchosquare = $ancho;
    $altosquare = $ancho;
  } else {
    # No ajusta nada
    $offsetx = 0;
    $offsety = 0;
    $anchosquare = $ancho;
    $altosquare = $alto;
  };

  if ($tipo eq 'jpg') {
    $thumb = new GD::Image($anchofinal,$altofinal);
  }else{
    # Si el formato es gif o png, usa paleta de 8 bits.
    $thumb = new GD::Image($anchofinal,$altofinal,0);
  };
  # warn("$offsetx, $offsety, $anchofinal, $altofinal, $anchosquare, $altosquare");
  # Crea el thumbnail.
  $thumb->copyResampled($imagen,0,0,$offsetx,$offsety,$anchofinal,$altofinal,$anchosquare,$altosquare);

  # No graba, sino que retorna el buffer binario de la foto para ser guardada por quien invoco a la funcion.
  my $bin_buffer;

  if ($tipo eq 'jpg') {
    $bin_buffer = $thumb->jpeg(85);
  }else{
    $bin_buffer = $thumb->png();
  };

  return ($bin_buffer, $anchofinal, $altofinal);
};

# ------------------------------------------------
return 1;
