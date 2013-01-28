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
# Librería usada por los post_procesos de cooperativa
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

package lib_ppart_galeria;

use JSON;

sub list_module {
    my $module = shift;
    no strict 'refs';
    return grep { defined &{"$module\::$_"} } keys %{"$module\::"}
}


# ------------------------------------------------
# Actualiza el campo link_XML
sub genera_xml_media {

  my ($destino, %DATOS_XML) = (@_);
  if($DATOS_XML{'file'} eq "") {
    warn('no iba archivo de audio');
    unlink $destino if(-f $destino);
    return;

  } else {

    my $xmlplayer = "<?xml version='1.0' encoding='iso-8859-1'?>";
    $xmlplayer = $xmlplayer . "\n<media_item>\n";

    foreach my $item (keys %DATOS_XML) {
      $xmlplayer = $xmlplayer . "\t<$item>".$DATOS_XML{$item}."</$item>\n";
    }

    $xmlplayer = $xmlplayer . "</media_item>\n";
    &glib_fildir_02::write_file($destino, $xmlplayer);
  }
}

# ------------------------------------------------
# Actualiza el campo link_XML
sub actualiza_url {

  my ($origen, $destino) = ($_[0], $_[1]);
  my $buffer = &glib_fildir_02::read_file($origen);

  $buffer = &actualizaCampo($buffer, 'link_XML', $destino);
  &glib_fildir_02::write_file($origen, $buffer) if($buffer);
}

# ------------------------------------------------
sub lee_status {
    my ($proctxt) = ($_[0]);
    
    my $jsonstr = &glib_fildir_02::read_file($proctxt);
    my $hash = jsonToObj($jsonstr);
    #~ my $json = new JSON;
    #~ my $hash = $json->decode($jsonstr);
    return $hash;
}

# ------------------------------------------------
sub escribe_status {
    
    my ($proctxt, $tiempo, $msg) = ($_[0], $_[1], $_[2]);
    
    my $hash;
    $hash->{'tiempo'} = $tiempo;
    $hash->{'msg'} = $msg;
    
    #~ my $json = new JSON;
    #~ $json->json_encode($hash);
    my $jsonstr = objToJson($hash);
    &glib_fildir_02::write_file($proctxt, $jsonstr);
}

# ------------------------------------------------
# Actualiza el campo link_XML
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
# Actualiza el campo link_XML
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
# Función que lee XML
sub get_xml_data {
  # Cargar xml del articulo.
  my ($path_final_xml) = $_[0];
  $path_final_xml =~ s/\/pags\/(\w+)(\.\w+)?$/\/xml\/\1\.xml/;

  my $xml = &glib_fildir_02::read_file($path_final_xml);

  my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;

  $xml =~ s/$crlf/\x0a/sg;

  my ($priv, $pub);
  if ($xml =~ /<_PRIVATE>(.*?)<\/_PRIVATE>/isg) {
    $priv = $1;
  }
  if ($xml =~ /<_PUBLIC>(.*?)<\/_PUBLIC>/isg) {
    $pub = $1;
  }
  return "$priv\n$pub";
}

# ------------------------------------------------
# Función que recupera del buffer xml (get_xml_data) uel valor de un campo que esta dentro de CDATA
sub get_xml_cdata_valor{

  my ($xml_data, $campo_nombre) = @_;
  my $campo_valor = '';

    if ($xml_data =~ /<$campo_nombre>(.+?)<\/$campo_nombre>/is) {
        $campo_valor=$1;
        if ($campo_valor =~ /<!\[CDATA\[(.*?)\]\]>/is) {
          $campo_valor = $1;
        }
    }
    return $campo_valor;
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
    my ($nro_foto, $inner, $nro_foto2);
    if($path_foto ne '' && $path_foto =~ /\/([^\/]*?)$/i) {
        $foto = $1;
        if($xml_data =~ /<(foto_\d+)>(.*?$foto.*?)<\/\1>/is) {
            $nrofoto = $1;
            $inner = $2;
            $nrofoto2 = $3;
            if($inner =~ /<_$dim$nrofoto>(\d*?)<\/_$dim$nrofoto>/i) {
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

#   open OUT, ">thumb_nina.$tipo" or die "Could not save ";
#   binmode OUT;
#   if ($tipo eq 'jpg') {
#     print OUT $thumb->jpeg(85);
#   }else{
#     print OUT $thumb->gif();
#   };
#   close OUT;

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
