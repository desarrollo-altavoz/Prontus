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
# Biblioteca de rutinas genericas para Prontus Search.
# ---------------------------------------------------------------

# 1.0    25/06/2005 - Primera version.
# 1.8    05/12/2006 - ALD - Agrega rutina para busqueda binaria.
#                        - Robustece la deteccion de copias de uno mismo.
# 1.12   03/09/2007 - ALD - Compatibiliza para Windows.
# 1.22   12/03/2008 - ALD - Agrega rutina get_dir_server para bajar acoplamiento con Prontus.
# 1.23   05/08/2008 - ALD - Agrega funcion que formatea un entero.
# 1.23.1 04/09/2009 - ALD - Agrega reconocimiento de fechas separadas por '-'.
#                         - Agrega funcion timestamp_iso.
#                         - Valida existencia de archivos antes de abrirlos.
# 1.24   16/12/2010 - ALD - Pasa a UTF-8.
# 1.25   17/12/2010 - YCC - Mejora manejo de guiones en friendly urls

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

package lib_search;

use strict;
use LWP::UserAgent;
use HTTP::Response;

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------

# #############################################
#  Busqueda binaria

# ---------------------------------------------------------------
# 1.8 Busqueda binaria en archivos de texto ordenados. Basado en Search::Dict
#
#  uso: binsearch (path_al_archivo,texto_buscado,tipo_de_busqueda)
#
# Asume que existe una linea por registro, donde el primer item es el indice,
# y la linea es de la forma:
#
# id=data|data|data|...
#
# o de la forma:
#
# id|data|data|data|...
#
# La comparacion es numerica o por string dependiendo de la instruccion de comparacion
# usada en las lineas marcadas 'CMP':
#   ($linea > $key) es para numeros (tipo_de_busqueda = 'num')
#   ($linea gt $key) es para strings (tipo_de_busqueda = 'str')
#
# Retorna '' si la busqueda falla.

sub binsearch {
  my($archivo,$key,$type) = @_;
  if (! -f $archivo) { return ''; }; # 1.23.1
  open DATAFILE, "<$archivo";
  my $fh = *DATAFILE;
  my(@stats,$idx);
  if (!( @stats = stat($fh) )) {
    close $fh;
    return '';
  };
  my($size, $blksize) = @stats[7,11];
  $blksize ||= 8192;   # Largo del bloque a leer
  $key =~ s/[=|]//g; # Excluye el separador, si estuviera.
  $key = lc $key;
  # Escoge el bloque correcto.
  my($min, $max) = (0, int($size / $blksize)); # Se ubica en los extremos del archivo.
  my ($mid,$linea);
  while ($max - $min > 1) {
    # print "debug: min=$min max=$max linea=$linea key=$key<br>\n";
    $mid = int(($max + $min) / 2);
    if (! seek($fh, $mid * $blksize, 0) ) { # Se ubica en el punto medio.
      close $fh;
      return '';
    };
    if ($mid > 0) { <$fh>; }; # Descarta linea por si quedo en la mitad de ella.
    $linea = <$fh>;      # Lee la linea siguiente.
    # print "debug: testing_line=$linea<br>\n";
    chomp $linea;
    last if ($linea eq '');
    $linea =~ s/[=|].*$//s; # Se queda con el primer elemento.
    # print "debug: primer elemento=[$linea] key=$key type=$type<br>\n";
    # if ( (($type eq 'str')&&($linea lt $key)) || (($type eq 'num')&&($linea < $key)) ) { # CMP. Compara y ajusta uno de los limites.
    # CMP. Compara y ajusta uno de los limites.
    if ($type eq 'str') {
      # print "debug: COMPARA STRING<br>\n";
      if ($linea lt $key) {
        $min = $mid;
      }else{
        $max = $mid;
      };
    }else{
      # print "debug: COMPARA NUMERO<br>\n";
      if ($linea < $key) {
        $min = $mid;
      }else{
        $max = $mid;
      };
    };
  }; # while
  # Se posiciona y retorna el bloque correcto. Retrocede uno por si las moscas.
  $min--;
  if ($min < 0) { $min = 0; };
  # print "debug: min=[$min]<br>\n";
  if (! seek($fh, $min * $blksize, 0) ) {
    close $fh;
    return '';
  };
  if ($min > 0) { <$fh>; }; # Descarta linea por si quedo en la mitad de ella.
  while ($linea = <$fh>) {
    chomp $linea;
    $idx = $linea;
    $idx =~ s/[=|].*$//s; # Se queda con el primer elemento.
    # print "debug: linea=[$linea] idx=[$idx] key=[$key]<br>\n";
    # last if ( (($type eq 'str')&&($idx ge $key)) || (($type == 'num')&&($idx >= $key))  ); # CMP.
     # CMP.
    if ($type eq 'str') {
      last if  ($idx ge $key);
    }else{
      last if  ($idx >= $key);
    };
  };
  close $fh;
  # if ( (($type eq 'str')&&($idx eq $key)) || (($type eq 'str')&&($idx == $key)) ) { # CMP.
  if ($idx eq $key) { # CMP.
    # print "debug resultado: linea=[$linea]<br>\n";
    return $linea;
  }else{
    # print "debug resultado: null<br>\n";
    return '';
  };
}; # binsearch


# #############################################
#  Especiales del buscador

# --------------------------------------------------------------- #
# Obtiene una pagina via http.
sub getHTML {
  # Lee y retorna la pagina web pasada como parametro.
  my ($url) = $_[0];
  my ($ua) = new LWP::UserAgent;
  my ($request) = new HTTP::Request('GET', $url);
  my ($response) = $ua->request($request);
  if ($response->is_success) {
    return $response->content;
  }else{
    return '';
  };
}; # getHTML.

# --------------------------------------------------------------- #
# Retorna un hash con el indice de palabras.
sub get_palabras {
  my ($palabras_idx,$p_ref) = @_;
  my ($id,$palabra);
  if (! -f $palabras_idx) { return; }; # 1.23.1
  open IN, "<$palabras_idx";
  while (<IN>) {
    chomp;
    ($palabra,$id) = split(/=/,$_);
    $$p_ref{$palabra} = $id;
  };
  close IN;
}; # get_palabras

# --------------------------------------------------------------- #
# Retorna un hash con las variables relevantes del cfg.
sub get_config {
  my($configfile) = $_[0];
  my(@lines,$name,$value,$line);
  my(%pairs) = ();
  my($buffer) = &lee_archivo($configfile);
  @lines = split(/[\r\n]/,$buffer);
  foreach $line (@lines) {
    if ( ($line ne '') && ($line !~ /^\s*#/) && ($line =~ /=/)) { # 1.3
      $line =~ s/#.*$//; # Elimina comentarios.
      ($name,$value) = split(/=/,$line);
      $name = &trim2($name);
      $value = &trim2($value);
      if ($name ne '') { $pairs{$name} = $value; };
    };
  };
  return %pairs;
}; # get_config

# -------------------------------------------------------------------------#
# Genera un friendly URL a partir del titular, del prontus_id y del ts.
sub friendlyUrl {
  my ($prontus_id,$ts,$titular,$ext) = @_;
  # 1.24 $titular = &notildes($titular);
  $titular = &notildesUtf8($titular); # 1.24
  $titular = lc $titular;
  $titular =~ s/[^a-z0-9]/-/sg;
  $titular =~ s/-+/-/sg; # 1.25
  $titular =~ s/^-//sg;
  $titular =~ s/-$//sg;
  my $fecha;
  my $hora;
  if ($ts =~ /^(\d{4})(\d{2})(\d{2})(\d{6})/) {
    $fecha = $1 . '-' . $2 . '-' . $3;
    $hora = $4;
  };
  return "/$titular/$prontus_id/$fecha/$hora.$ext";
}; # friendlyUrl

# -------------------------------------------------------------------------#
# Lee un archivo por completo. Si el archivo no existe retorna ''.
sub lee_archivo {
  my($archivo) = $_[0];
  my($buffer) = '';

  if (-e $archivo) {
    open (ARCHIVO,"<$archivo");
    binmode ARCHIVO;
    read ARCHIVO,$buffer,-s $archivo;
    close ARCHIVO;
  };
  # 1.2 Elimina los \r.
  $buffer =~ s/\r//isg;
  return $buffer;

}; # lee_archivo

# ------------------------------------------------------------------------#
# Escribe un archivo. Si no puede retorna un mensaje de error.
# 1.1 Si el directorio no existe, intenta crearlo.

sub escribe_archivo {
  my($archivo,$buffer) = ($_[0],$_[1]);
  my($dir);

  if ($archivo =~ /^(.+?)\/[^\/]+$/) {
    $dir = $1;
    if (! (&crea_dir($dir))) {
      return "Fail writing file $archivo $!";
    };
  };
  if (open (ARCHIVO,">$archivo") ) {
    binmode ARCHIVO;
    print ARCHIVO $buffer; # Escribe buffer completo
    close ARCHIVO;
    return '';
  }else{
    return "Fail writing file $archivo $!";
  };

}; # escribe_archivo

# -----------------------------------------------------------------------#
# Detecta si un directorio no existe. Si no existe, intenta crearlo
# recursivamente.

sub crea_dir {
  my($dir) = $_[0];
  if (-d $dir) { return 1; }; # Si el archivo existe, retorna de inmediato.
  my(@dirs) = split(/[\/\\]/,$dir); # 1.12
  my($i,$thedir);
  for ($i=0;$i<=$#dirs;$i++) {
    if ( $dirs[$i] =~ /[A-Z]:/) { # 1.12
      $thedir = $dirs[$i]; # Caso Windows.
    }else{
      $thedir .= '/' . $dirs[$i]; # Caso UNIX.
    };
    if (! ( -d $thedir)) {
      # print "<br>crea_dir $thedir\n"; # debug
      if (! (mkdir $thedir, 493)) {
        # print "<br>Falla crea_dir $thedir\n"; # debug
        return 0;
      };
    };
  };
  return 1;
}; # crea_dir

# -----------------------------------------------------------------------#
# Lee un directorio y entrega la lista de entries en bruto.
# Si no puede entrega mensaje de error.

sub lee_dir {
  my($eldir) = $_[0];
  my(@entries);
  # Abre directorio.
  if (opendir(DIR, $eldir)) {
    @entries = readdir(DIR);
    closedir DIR;
  };
  return @entries; # 1.23.1
}; # lee_dir

# #############################################
#  Utilitarios para el manejo de strings

# -------------------------------------------------------------------------#
# Extrae todo caracter de control de un string.

sub no_controls {
  my($txt) = @_;
  $txt =~ s/[\x00-\x1f]//sg;
  return $txt;
}; # no_controls

# -------------------------------------------------------------------------#
# Extrae todo caracter no alfanumerico de un string.

sub solo_alfa {
  my($txt) = @_;
  $txt =~ s/[^0-9a-z]//sig;
  return $txt;
}; # solo_alfa

# -------------------------------------------------------------------------#
# Extrae todo caracter no alfanumerico o guiones o punto de un string.

sub solo_alfa2 {
  my($txt) = @_;
  $txt =~ s/[^0-9a-z\-\_\.]//sig;
  return $txt;
}; # solo_alfa2

# -------------------------------------------------------------------------#
# Extrae todo caracter no hexadecimal de un string.

sub solo_hex {
  my($txt) = @_;
  $txt =~ s/[^0-9a-f]//sig;
  return $txt;
}; # solo_hex

# -------------------------------------------------------------------------#
# Recorta espacios antes y despues de un valor.

sub trim2 {
  my($string) = $_[0];
  $string =~ s/^\s*//;
  $string =~ s/\s*$//;
  return $string;
}; # trim2

# -------------------------------------------------------------------------#
# Reemplaza tildes por letras normales.
sub notildes {
  my($toencode) = @_;

  $toencode =~ tr/áéíóúÁÉÍÓÚüÜñÑ/aeiouaeiouuunn/; # Destilda ISO.

  $toencode =~ s/&(.)acute;/$1/g;
  $toencode =~ s/&(.)tilde;/$1/g;
  $toencode =~ s/&(.)uml;/$1/g;
  $toencode =~ s/&(.)circ;/$1/g;
  $toencode =~ s/&(.)grave;/$1/g;

  $toencode =~ s/&[^;]+;//g; # Elimina toda otra entidad.

  $toencode=~s/\xC0/A/g;
  $toencode=~s/\xC1/A/g;
  $toencode=~s/\xC2/A/g;
  $toencode=~s/\xC3/A/g;
  $toencode=~s/\xC4/A/g;
  $toencode=~s/\xC5/A/g;
  $toencode=~s/\xC6/A/g;
  $toencode=~s/\xC7/C/g;
  $toencode=~s/\xC8/E/g;
  $toencode=~s/\xC9/E/g;
  $toencode=~s/\xCA/E/g;
  $toencode=~s/\xCB/E/g;
  $toencode=~s/\xCC/I/g;
  $toencode=~s/\xCD/I/g;
  $toencode=~s/\xCE/I/g;
  $toencode=~s/\xCF/I/g;
  $toencode=~s/\xD1/N/g;
  $toencode=~s/\xD2/O/g;
  $toencode=~s/\xD3/O/g;
  $toencode=~s/\xD4/O/g;
  $toencode=~s/\xD5/O/g;
  $toencode=~s/\xD6/O/g;

  $toencode=~s/\xD8/O/g;
  $toencode=~s/\xD9/U/g;
  $toencode=~s/\xDA/U/g;
  $toencode=~s/\xDB/U/g;
  $toencode=~s/\xDC/U/g;
  $toencode=~s/\xDD/Y/g;
  $toencode=~s/\xE0/a/g;
  $toencode=~s/\xE1/a/g;
  $toencode=~s/\xE2/a/g;
  $toencode=~s/\xE3/a/g;
  $toencode=~s/\xE4/a/g;
  $toencode=~s/\xE5/a/g;
  $toencode=~s/\xE6/a/g;
  $toencode=~s/\xE7/c/g;
  $toencode=~s/\xE8/e/g;
  $toencode=~s/\xE9/e/g;
  $toencode=~s/\xEA/e/g;
  $toencode=~s/\xEB/e/g;
  $toencode=~s/\xEC/i/g;
  $toencode=~s/\xED/i/g;
  $toencode=~s/\xEE/i/g;
  $toencode=~s/\xEF/i/g;
  $toencode=~s/\xF1/n/g;
  $toencode=~s/\xF2/o/g;
  $toencode=~s/\xF3/o/g;
  $toencode=~s/\xF4/o/g;
  $toencode=~s/\xF5/o/g;
  $toencode=~s/\xF6/o/g;
  $toencode=~s/\xF8/o/g;
  $toencode=~s/\xF9/u/g;
  $toencode=~s/\xFA/u/g;
  $toencode=~s/\xFB/u/g;
  $toencode=~s/\xFC/u/g;
  $toencode=~s/\xFF/y/g;

  return $toencode;
}; # notildes

# -------------------------------------------------------------------------#
# Reemplaza tildes UTF-8 por letras normales.
sub notildesUtf8 {
  my($toencode) = $_[0];

  $toencode =~ s/\xC3\xA1/a/sg;
  $toencode =~ s/\xC3\x81/A/sg;
  $toencode =~ s/\xC3\xA0/a/sg;
  $toencode =~ s/\xC3\x80/A/sg;
  $toencode =~ s/\xC3\xA2/a/sg;
  $toencode =~ s/\xC3\x82/A/sg;
  $toencode =~ s/\xC3\xA4/a/sg;
  $toencode =~ s/\xC3\x84/A/sg;

  $toencode =~ s/\xC3\xA9/e/sg;
  $toencode =~ s/\xC3\x89/E/sg;
  $toencode =~ s/\xC3\xA8/e/sg;
  $toencode =~ s/\xC3\x88/E/sg;
  $toencode =~ s/\xC3\xAA/e/sg;
  $toencode =~ s/\xC3\x8A/E/sg;
  $toencode =~ s/\xC3\xAB/e/sg;
  $toencode =~ s/\xC3\x8B/E/sg;

  $toencode =~ s/\xC3\xAD/i/sg;
  $toencode =~ s/\xC3\x8D/I/sg;
  $toencode =~ s/\xC3\xAC/I/sg;
  $toencode =~ s/\xC3\x8C/i/sg;
  $toencode =~ s/\xC3\xAE/I/sg;
  $toencode =~ s/\xC3\x8E/i/sg;
  $toencode =~ s/\xC3\xAF/I/sg;
  $toencode =~ s/\xC3\x8F/i/sg;

  $toencode =~ s/\xC3\xB3/o/sg;
  $toencode =~ s/\xC3\x93/O/sg;
  $toencode =~ s/\xC3\xB2/o/sg;
  $toencode =~ s/\xC3\x92/O/sg;
  $toencode =~ s/\xC3\xB4/o/sg;
  $toencode =~ s/\xC3\x94/O/sg;
  $toencode =~ s/\xC3\xB6/o/sg;
  $toencode =~ s/\xC3\x96/O/sg;

  $toencode =~ s/\xC3\xBA/u/sg;
  $toencode =~ s/\xC3\x9A/U/sg;
  $toencode =~ s/\xC3\xB9/u/sg;
  $toencode =~ s/\xC3\x99/U/sg;
  $toencode =~ s/\xC3\xBB/u/sg;
  $toencode =~ s/\xC3\x9B/U/sg;
  $toencode =~ s/\xC3\xBC/u/sg;
  $toencode =~ s/\xC3\x9C/U/sg;

  $toencode =~ s/\xC3\xB1/n/sg;
  $toencode =~ s/\xC3\x91/N/sg;
  $toencode =~ s/\xC3\xA7/c/sg;
  $toencode =~ s/\xC3\x87/C/sg;

  $toencode =~ s/&(.)acute;/$1/g;
  $toencode =~ s/&(.)tilde;/$1/g;
  $toencode =~ s/&(.)uml;/$1/g;
  $toencode =~ s/&(.)circ;/$1/g;
  $toencode =~ s/&(.)grave;/$1/g;

  $toencode =~ s/&[^;]+;//g; # Elimina toda otra entidad.

  return $toencode;
}; # notildesUtf8
# -----------------------------------------------------------------------#
# Escapea caracteres para formar queries html.
sub escapehtml {
  my($toencode) = $_[0];
  $toencode =~ s/([^a-zA-Z0-9!, ])/sprintf('%%%02x',ord($1))/ge;
  $toencode =~ tr/ /+/;       # Transforma los espacios en mas.
  return $toencode;
}; # escapehtml

# -------------------------------------------------------------------------#
# 1.23 Formatea un valor entero.
sub formatInteger {
  my($real) = $_[0];
  my($i,$d,$out);
  $real =~ s/\..*$//;
  # Agrega los puntos en los miles.
  $out = '';
  my @real = split(//,$real);
  $d = 0;
  for ($i=$#real; $i >= 0; $i--) {
    $out = $real[$i] . $out;
    $d++;
    if (($d % 3 == 0) &&
        ($i > 0) &&
        ($real[$i-1] =~ /[0-9]/)
       ) { $out = '.' . $out; };
  };
  return $out;
}; # formatInteger

# #############################################
# Fechas

# -------------------------------------------------------------- #
# Retorna la fecha de hoy en formato ISO aaaammdd.
sub fecha_iso {
  # (0: $sec, 1: $min, 2: $hour, 3: $mday, 4: $mon, 5: $year, 6: $wday, 7: $yday, 8: $isdst)
  my(@fecha) = localtime(time);
  my($ano,$mes,$dia) = ($fecha[5],$fecha[4],$fecha[3]);
  if ($ano < 2000) { $ano += 1900; };
  $mes = sprintf('%02d',($mes + 1));
  $dia = sprintf('%02d',$dia);
  return "$ano$mes$dia";
}; # fecha_iso

# -------------------------------------------------------------- #
# 1.23.1 Retorna la fecha y hora de hoy en formato ISO aaaammdd.
sub timestamp_iso {
  # (0: $sec, 1: $min, 2: $hour, 3: $mday, 4: $mon, 5: $year, 6: $wday, 7: $yday, 8: $isdst)
  my(@fecha) = localtime(time);
  my($ano,$mes,$dia,$hra,$min,$seg) = ($fecha[5],$fecha[4],$fecha[3],$fecha[2],$fecha[1],$fecha[0]);
  if ($ano < 2000) { $ano += 1900; };
  $mes = sprintf('%02d',($mes + 1));
  $dia = sprintf('%02d',$dia);
  $hra = sprintf('%02d',$hra);
  $min = sprintf('%02d',$min);
  $seg = sprintf('%02d',$seg);
  return "$ano$mes$dia$hra$min$seg";
}; # timestamp_iso

# -------------------------------------------------------------- #
# Toma una fecha d/m/a y la retorna en formato ISO aaaammdd.
sub fecha2iso {
	my $fecha = $_[0];
	my($dia,$mes,$ano);
	# 1.24
	if ($fecha =~ /\//) { # Separador = /
	  $fecha =~ s/[^0-9\/]//g;
    ($dia,$mes,$ano) = split(/\//,$_[0]);
  }elsif($fecha =~ /\-/) { # Separador = -
    $fecha =~ s/[^0-9\-]//g;
    ($dia,$mes,$ano) = split(/\-/,$_[0]);
  }else{
    return '';
  };
  if (($ano < 2000) && ($ano < 100)) { $ano += 2000; }; # Asume solo anos despues del ano 2000.
  $mes = sprintf('%02d',$mes);
  $dia = sprintf('%02d',$dia);
  $ano = sprintf('%04d',$ano);
  return "$ano$mes$dia";
}; # fecha2iso

# -------------------------------------------------------------- #
# Toma una fecha ISO y la retorna en formato dd/mm/aaaa.
sub iso2fechacorta {
	my $fecha = $_[0];
	return substr($fecha,6,2) . '/' . substr($fecha,4,2) . '/' . substr($fecha,0,4);
}; # iso2fechacorta

##########################################################################
# Rutinas de Prontus copiadas aqui para mantener bajo acoplamiento.

#------------------------------------------------------------------------#
sub get_dir_server {
  # DIR_SERVER:
  #   En unix queda algo asi como /sites/misitio.cl/web
  #   En win queda algo asi como c:/sites/misitio.cl/web
  my $dir_server = $ENV{'DOCUMENT_ROOT'};  # Unix y Abyss
  if ($dir_server eq '') {
    $dir_server = $ENV{'PATH_TRANSLATED'}; # ej: PATH_TRANSLATED = C:\sites\casapiedra_rva
    $dir_server =~ s/\\/\//g;
    $dir_server =~ s/\/cgi-\w+.*$//g; # a veces viene el path cgi metido
  };
  $dir_server =~ s/\\/\//g; # cambia \ por /
  return $dir_server;
}; # get_dir_server


return 1;
