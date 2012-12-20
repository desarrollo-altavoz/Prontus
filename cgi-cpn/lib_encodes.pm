#!/usr/bin/perl

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Funciones para transformar texto html a formato compatible para ser tomado por flash.

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 01 - 06/2004 - YCH - Basado en /sites/armada.cl/cgi-cpn/prontus2xml.pl by ALD

# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------
use URI::Escape;
package lib_encodes;

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
# Extrae el texto relevante desde el html.
sub html2flash($texto) {
  $aux = $_[0];
  # Transforma saltos de linea.
  $aux =~ s/^<p[^>]*?>//isg; # El primero no cuenta.
  $aux =~ s/<p[^>]*?>/\n/isg;
  $aux =~ s/<br *\/?>/\n/isg;
  # Elimina toda clase de tags, excepto bold e italica.
  $aux =~ s/<(\/)?([biIB])>/##\1\2##/sg;
  $aux =~ s/<[^>]*?>/ /sg;
  $aux =~ s/##(\/)?([biIB])##/<\1\2>/sg;

  # Elimina caracteres invisibles a las orillas
  $aux = &trim($aux);

  # Comprime espacios entre medio
  $aux =~ s/\s+/ /sg;

  # Cambia entidades html a texto
  $aux = &entity2text($aux);

  # Codifica en UTF8
  utf8::encode($aux);

  # Codifica como URL
  $aux = &URI::Escape::uri_escape($aux); # codif de url de Perl

  # Cambia espacios por +, para que el str quede mas corto.
  $aux =~ s/(%20)/+/sg;


  return $aux;
}; # html2text

# -------------------------------------------------------------------------#
# Transforma un string codificado en formato url+unicode estilo Flash a texto normal.
sub flash2html {
  my($str) = $_[0];
  # %E2%80%9C

  $str = &URI::Escape::uri_unescape($str); # decodif de url de Perl

  # Aplica decodificacion de URL a MANOPLA
  # $str =~ s/\%([A-Fa-f0-9]{2})/pack('C', hex($1))/seg;

  # cambia + por espacios
  $str =~ s/\+/ /g;

  # decodifica utf8
  utf8::decode($str);

  return $str;
};
# -------------------------------------------------------------------------#
# Recorta espacios antes y despues de un valor.

sub trim {
  my($string) = $_[0];
  $string =~ s/^[\s\n\r]*//;
  $string =~ s/[\s\n\r]*$//;
  return $string;
}; # trim2


# -------------------------------------------------------------------------#
# Detecta y pone en ISO los caracteres escapeados en html.

sub entity2text {
    my($toencode) = $_[0];

    $toencode=~s/&quot;/\"/g;
    $toencode=~s/&Yacute;/\x86/g;
    $toencode=~s/&brvbar;/\x87/g;
    $toencode=~s/&eth;/\x8B/g;
    $toencode=~s/&middot;/\x95/g;
    $toencode=~s/&shy;/\x96/g;


    $toencode=~s/&#166;/\xA6/g;
    $toencode=~s/&#175;/\xAF/g;
    $toencode=~s/&#178;/\xB2/g;
    $toencode=~s/&#179;/\xB3/g;
    $toencode=~s/&#185;/\xB9/g;
    $toencode=~s/&#188;/\xBC/g;
    $toencode=~s/&#189;/\xBD/g;
    $toencode=~s/&#190;/\xBE/g;
    $toencode=~s/&#215;/\xD7/g;

    $toencode=~s/&nbsp;/\xA0/g;
    $toencode=~s/&iexcl;/\xA1/g;
    $toencode=~s/&cent;/\xA2/g;
    $toencode=~s/&pound;/\xA3/g;
    $toencode=~s/&curren;/\xA4/g;
    $toencode=~s/&yen;/\xA5/g;
    $toencode=~s/&sect;/\xA7/g;
    $toencode=~s/&uml;/\xA8/g;
    $toencode=~s/&copy;/\xA9/g;
    $toencode=~s/&ordf;/\xAA/g;
    $toencode=~s/&laqno/\xAB;/g;
    $toencode=~s/&not;/\xAC/g;
    $toencode=~s/&shy;/\xAD/g;
    $toencode=~s/&reg;/\xAE/g;
    $toencode=~s/&deg;/\xB0/g;
    $toencode=~s/&plusmn;/\xB1/g;
    $toencode=~s/&acute;/\xB4/g;
    $toencode=~s/&micro;/\xB5/g;
    $toencode=~s/&para;/\xB6/g;
    $toencode=~s/&middot;/\xB7/g;
    $toencode=~s/&cedil;/\xB8/g;
    $toencode=~s/&ordm;/\xBA/g;
    $toencode=~s/&raquo;/\xBB/g;
    $toencode=~s/&iquest;/\xBF/g;
    $toencode=~s/&Agrave;/\xC0/g;
    $toencode=~s/&Aacute;/\xC1/g;
    $toencode=~s/&Acirc;/\xC2/g;
    $toencode=~s/&Atilde;/\xC3/g;
    $toencode=~s/&Auml;/\xC4/g;
    $toencode=~s/&Aring;/\xC5/g;
    $toencode=~s/&AElig;/\xC6/g;
    $toencode=~s/&Ccedil;/\xC7/g;
    $toencode=~s/&Egrave;/\xC8/g;
    $toencode=~s/&Eacute;/\xC9/g;
    $toencode=~s/&Ecirc;/\xCA/g;
    $toencode=~s/&Euml;/\xCB/g;
    $toencode=~s/&Igrave;/\xCC/g;
    $toencode=~s/&Iacute;/\xCD/g;
    $toencode=~s/&Icirc;/\xCE/g;
    $toencode=~s/&Iuml;/\xCF/g;
    $toencode=~s/&Ntilde;/\xD1/g;
    $toencode=~s/&Ograve;/\xD2/g;
    $toencode=~s/&Oacute;/\xD3/g;
    $toencode=~s/&Ocirc;/\xD4/g;
    $toencode=~s/&Otilde;/\xD5/g;
    $toencode=~s/&Ouml;/\xD6/g;

    $toencode=~s/&Oslash;/\xD8/g;
    $toencode=~s/&Ugrave;/\xD9/g;
    $toencode=~s/&Uacute;/\xDA/g;
    $toencode=~s/&Ucirc;/\xDB/g;
    $toencode=~s/&Uuml;/\xDC/g;
    $toencode=~s/&Yacute;/\xDD/g;
    $toencode=~s/&THORN;/\xDE/g;
    $toencode=~s/&szlig;/\xDF/g;
    $toencode=~s/&agrave;/\xE0/g;
    $toencode=~s/&aacute;/\xE1/g;
    $toencode=~s/&acirc;/\xE2/g;
    $toencode=~s/&atilde;/\xE3/g;
    $toencode=~s/&auml;/\xE4/g;
    $toencode=~s/&aring;/\xE5/g;
    $toencode=~s/&aelig;/\xE6/g;
    $toencode=~s/&ccedil;/\xE7/g;
    $toencode=~s/&egrave;/\xE8/g;
    $toencode=~s/&eacute;/\xE9/g;
    $toencode=~s/&ecirc;/\xEA/g;
    $toencode=~s/&euml;/\xEB/g;
    $toencode=~s/&igrave;/\xEC/g;
    $toencode=~s/&iacute;/\xED/g;
    $toencode=~s/&icirc;/\xEE/g;
    $toencode=~s/&iuml;/\xEF/g;
    $toencode=~s/&eth;/\xF0/g;
    $toencode=~s/&ntilde;/\xF1/g;
    $toencode=~s/&ograve;/\xF2/g;
    $toencode=~s/&oacute;/\xF3/g;
    $toencode=~s/&ocirc;/\xF4/g;
    $toencode=~s/&otilde/\xF5;/g;
    $toencode=~s/&ouml;/\xF6/g;
    $toencode=~s/&divide;/\xF7/g;
    $toencode=~s/&oslash;/\xF8/g;
    $toencode=~s/&ugrave/\xF9;/g;
    $toencode=~s/&uacute;/\xFA/g;
    $toencode=~s/&ucirc;/\xFB/g;
    $toencode=~s/&uuml;/\xFC/g;
    $toencode=~s/&brvbar;/\xFD/g;
    $toencode=~s/&thorn;/\xFE/g;
    $toencode=~s/&yuml;/\xFF/g;


    $toencode=~s/&#131;/\x83/g;

    $toencode=~s/&#133;/\x85/g;

    $toencode=~s/&#136;/\x88/g;
    $toencode=~s/&#137;/\x89/g;
    $toencode=~s/&#138;/\x8A/g;

    $toencode=~s/&#140;/\x8C/g;
    $toencode=~s/&#141;/\x8D/g;
    $toencode=~s/&#142;/\x8E/g;
    $toencode=~s/&#143;/\x8F/g;
    $toencode=~s/&#144;/\x90/g;
    $toencode=~s/&#145;/\x91/g;
    $toencode=~s/&#146;/\x92/g;

    $toencode=~s/&#151;/\x97/g;

    $toencode=~s/&#153;/\x99/g;
    $toencode=~s/&#154;/\x9A/g;

    $toencode=~s/&#156;/\x9C/g;
    $toencode=~s/&#157;/\x9D/g;
    $toencode=~s/&#158;/\x9E/g;
    $toencode=~s/&#159;/\x9F/g;

    $toencode=~s/&amp;/&/g;  # Al final, traduce los ampersands.

    return $toencode;
}; # unescape_html

# ---------------------------------------------------------------
1;
# -------------------------------END LIBRERIA--------------------