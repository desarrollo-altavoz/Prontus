#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

#-------------------------------COMENTARIO GLOBAL---------------
#---------------------------------------------------------------
# PROPOSITO.
#-----------
# Codigo HTML : generación y manipulacion.

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 01 : Primera version at 04/feb/2000.
# 01a: Agrega funcion 'lee_head_text'. 02/06/2000
# 01b: Agrega funcion 'generar_popup_from_dir'. 02/06/2000
# 01c: Correcciones rutina 'imprimir_celdas' para que incluya estilo css en el TD. 05/07/2000
# 01d: Agrega funcion 'generar_celdas'. 17/07/2000
# 01e: Correcciones en el parseo de tablas. 01/09/2000
# 01f: Mas correcciones en el parseo de tablas referentes a la alineacion. 11/09/2000
# 01g: Mas correcciones en el parseo de tablas. 27/09/2000
# 01h : Modificacion para NT
# 01i : Se agrega el finde tag </option> que faltaba. 05/03/2001

# 02 : Cambio a segunda version, congelada para prontus 5 - 17/04/2001
# 2.1 : modificacion a lee_tit_file 10/08/2001 (exclusiva para prontus)
# 2.2 - 08/01/2003 - Declara var. $entry en 'generar_popup_from_dir'
# 2.3 - 09/04/2003 - en rellenar_..., convierte ret. de carro mac a unix style.
#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package glib_html_02;
use JSON;

#---------------------------------------------------------------
# SUB-RUTINAS.
#-------------
sub text2html {
  # Escapea texto para ponerlo en pag html.
  my $toencode = $_[0];
  $toencode=~s/&([^#][^0-9]+)/&amp;\1/g;             # Antes que nada, traduce los ampersands. # 1.19 correccion a e.r.
  $toencode=~s/>/&gt;/g;              # >
  $toencode=~s/"/&quot;/g;            # " # 8.0
  $toencode=~s/'/&#39;/g;
  $toencode=~s/</&lt;/g;              # <
  return $toencode;
};

#---------------------------------------------------------------
sub imprimir_celdas {
# Imprime celdas contiguas en una fila de una tabla HTML, con la info suministrada.
# Necesita apetura de la TR y cerrado de TR y de TD.

# Parametros :
# 0) nro. de campos
# 1) tripletas valor_campo,width_col, link, target
# 2) estilo de css a aplicar a TD   # 01c



  my ($nro_campos, $valor_campo, $width_col, $i, $link, $alto_fila, $target);

  $nro_campos = $_[0];
  $estilo = $_[$#_];      # 01c


  for ($i=1; $i <= $nro_campos*4; $i=$i+4) {
      $valor_campo = $_[$i];
      $width_col = $_[$i+1];
      $link = $_[$i+2];
      $target = $_[$i+3];
      # Se imprime la fila.
      print	q{<td width="};
      print $width_col;
      print q{%" class="};   # 01c
      print $estilo;         # 01c
      print q{">};
  	  print q{&nbsp;};

      # Si el link no es nulo, se imprime.
      if ( $link ne '' ) {
        print q{<a href="};
        print $link;
        if ( $target ne '' ) {
          print '" target ="' . $target .'">';
        }
        else {
  		    print '">';
  		  }
        print $valor_campo;
        print q{</a></td>};
      }
      # Sino, imprimir sin link.
      else {
        print "$valor_campo</TD>";
      };
  };

};

#---------------------------------------------------------------
# 01d:
sub generar_celdas {
# Variante de imprimir_celdas().
# Genera celdas contiguas en una fila de una tabla HTML, con la info suministrada.
# Necesita apetura de la TR y cerrado de TR.

# Parametros :
# 0) nro. de campos
# 1) tripletas valor_campo,width_col, link, target
# 2) estilo de css a aplicar a TD


  my ($celdas, $nro_campos, $valor_campo, $width_col, $i, $link, $alto_fila, $target);

  $nro_campos = $_[0];
  $estilo = $_[$#_];


  for ($i=1; $i <= $nro_campos*4; $i=$i+4) {
      $valor_campo = $_[$i];
      $width_col = $_[$i+1];
      $link = $_[$i+2];
      $target = $_[$i+3];
      # Se imprime la fila.
      $celdas .= q{<td width="};
      $celdas .= $width_col;
      $celdas .= q{%" class="};
      $celdas .= $estilo;
      $celdas .= q{">};
  	  $celdas .= q{&nbsp;};

      # Si el link no es nulo, se genera.
      if ( $link ne '' ) {
        $celdas .= q{<a href="};
        $celdas .= $link;
        if ( $target ne '' ) {
          $celdas .= '" target ="' . $target .'">';
        }
        else {
  		    $celdas .= '">';
  		  }
        $celdas .= $valor_campo;
        $celdas .= q{</a></td>};
      }
      # Sino, imprimir sin link.
      else {
        $celdas .= "$valor_campo</td>";
      };
  };

  return $celdas;

};

#---------------------------------------------------------------
sub rellenar_plantilla {
# Reemplaza en la plantilla html dada las marcas de campo por los
# valores corespondientes.
# Además soporta aplicacion de expresiones regulares de sustitucion global
# sobre los valores (para eliminacion de hasta 2 cadenas especificas en cada
# uno), antes de hacer el reemplazo de la marca.

# Parametros :
# 0) nro. de marcas a reemplazar.
# 1) Cuartetas Marca,Valor,er_elim1,er_elim2
# 2) nombre con path completo de la pag html, con extension, que sera usada como plantilla.

# Retorna : string con la pag. completa para imprimirla.

  my ($nro_marcas, $marca, $valor_marca, $er_elim1, $er_elim2, $plantilla);
  my ($pagina, $size_arch, $i);


  $nro_marcas = $_[0];
  $plantilla  = $_[$#_];

  # Abrir y cargar archivo corresp. a la plantilla
  open (archivo,$plantilla) || die "$!\n";
	$size_arch = (-s $plantilla);
  read archivo, $pagina, $size_arch;
  close archivo;
  if ($pagina !~ /\n/) { # 2.3
    $pagina =~ s/\r/\n/sg;
  };

	# Realizar el reemplazo de las marcas en la variable $pagina.
  for ($i=1; $i <= $nro_marcas*4; $i=$i+4) {
      $marca = $_[$i];
      $valor_marca = $_[$i+1];
      $er_elim1 = $_[$i+2];
      $er_elim2 = $_[$i+3];

      # Eliminacion de cadenas no deseadas en el valor del campo.
      #$valor_marca =~ s/$er_elim1//g; # interfieren en nt #01h
      #$valor_marca =~ s/$er_elim2//g;  # interfieren en nt #01h

      # Reemplazo de marca por valor.
    	$pagina =~ s/$marca/$valor_marca/g;
  };
  return $pagina;
};

#---------------------------------------------------------------
sub get_datos_desde_html {

# En un arch. HTML, obtiene los valores ubicados entre dos delimitadores
# al estilo html :,
#   <!--DC__NNNNN--> y <!--/DC__NNNN-->

# Parametros :
# 0) Nro. de valores a rescatar.
# 1) Nombres de campos, de la forma NNNNN.
# 2) Archivo html con path completo y extension.

# Retorna : Un hash con los valores obtenidos y cuyas claves seran
# los caracteres NNNNN.

  my ($nro_valores, $nombre_campo, $arch_html);
  my ($size_arch, $str_arch, $i, $valor_campo);
  my ($delimitador_inicio, $delimitador_fin);
  my (%hash_valores) = ();

  $nro_valores = $_[0];
  $arch_html = $_[$#_];

  # Abrir y cargar archivo en la variable $str_arch.
  open (archivo,$arch_html) || die "$!\n";
	$size_arch = (-s $arch_html);
  binmode archivo;
  read archivo, $str_arch, $size_arch;
  close archivo;

  # Obtener valores entre delimitadores y cargar el hash.
  %hash_valores = ();
  for ($i=1; $i <= $nro_valores; $i=$i+1) {
      $nombre_campo = $_[$i];
      $delimitador_inicio = '<!--DC__' . $nombre_campo . '-->';
	    $delimitador_fin = '<!--/DC__' . $nombre_campo . '-->';

      # Sacar contenido.
	   	$str_arch =~ /$delimitador_inicio(.*)?$delimitador_fin/sg;
      $valor_campo = $1;

      # Cargar hash.
      $hash_valores{$nombre_campo} = $valor_campo;
  };

  return %hash_valores;

};
#--------------------------------------------------------------------#
sub print_json_result {
    # Imprime ajax con reporte de resultado.
    my ($status) = $_[0];  # 0 | 1
    my ($msg) = $_[1];  # mensaje
    my ($options) = $_[2]; # exit=1|0, ctype=1|0

    my ($exit, $ctype);
    $exit = 1 if ($options =~ /(^|,) *exit *= *1 *(,|$)/);
    $ctype = 1 if ($options =~ /(^|,) *ctype *= *1 *(,|$)/);

    binmode(STDOUT, ":utf8");

    my $resp;
    $resp->{'status'} = $status;
    $resp->{'msg'} = $msg;
    print "Content-Type: text/html\n\n" if ($ctype);
    my $json = new JSON;
    # print $json->to_json($resp);
    print &JSON::to_json($resp);
    exit if ($exit);
}
#--------------------------------------------------------------------#
sub print_json_result_hash {
    # Imprime ajax con reporte de resultado.
    my ($hash) = $_[0];  # 0 | 1
    my ($options) = $_[1]; # exit=1|0, ctype=1|0

    my ($exit, $ctype);
    $exit = 1 if ($options =~ /(^|,) *exit *= *1 *(,|$)/);
    $ctype = 1 if ($options =~ /(^|,) *ctype *= *1 *(,|$)/);

    binmode(STDOUT, ":utf8");
       
    print "Content-Type: text/html\n\n" if ($ctype);
    my $json = new JSON;
    # print $json->to_json($resp);
    print &JSON::to_json($hash);
    exit if ($exit);
};

#--------------------------------------------------------------------#
sub print_pag_result {
# Imprime pagina con reporte de resultado.

# Param :
# 0) Titulo del mensaje
# 1) Mensaje a imprimir

  my ($tit) = $_[0];
  my ($result) = $_[1];
  my ($cerrar) = $_[2]; # 1 | 0: si no viene, se asume 'volver'
  my ($options) = $_[3]; # exit=1|0, ctype=1|0, link=nolink

  my ($exit, $ctype, $link);
  $exit = 1 if ($options =~ /(^|,) *exit *= *1 *(,|$)/);
  $ctype = 1 if ($options =~ /(^|,) *ctype *= *1 *(,|$)/);
  $link = $2 if ($options =~ /(^|,) *link *= *(\w+) *(,|$)/);

  binmode(STDOUT, ":utf8");

  # Abrir y cargar archivo corresp. a la plantilla
  my $plantilla = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/prontus_msg.html";
  my $pagina;
  if (-f $plantilla) {
    open (archivo,$plantilla) || die "$!\n";
  	my $size_arch = (-s $plantilla);

  	binmode archivo;
    read archivo, $pagina, $size_arch;
    close archivo;
    if ($pagina !~ /\n/) { # 2.3
      $pagina =~ s/\r/\n/sg;
    };
    $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/ig;
    $pagina =~ s/%%title%%/$tit/ig;
    $pagina =~ s/%%msg%%/$result/ig;

    if ($link eq 'nolink') {
        $pagina =~ s/<!--volver-->.*?<!--\/volver-->//isg;
        $pagina =~ s/<!--cerrar-->.*?<!--\/cerrar-->//isg;
    } else {
        if ($cerrar) {
          $pagina =~ s/<!--volver-->.*?<!--\/volver-->//isg;
        }
        else {
          $pagina =~ s/<!--cerrar-->.*?<!--\/cerrar-->//isg;
        };
    };

  }
  else {
    $pagina = $result;
  };

  print "Content-Type: text/html\n\n" if ($ctype);
  print $pagina;
  exit if ($exit);
}

#--------------------------------------------------------------------#
sub print_tabladir {
# Lista los archivos HTML | HTM del directorio pasado como parametro
# en una tabla linkeada de paginas ordenadas alfabeticamente, con 3 columnas:
#  - Nombre del archivo y TITLE
#  - Peso en KB
#  - checkboxes para seleccionarlas (chkfile$i y el nombre del archivo como value).
# Requiere apertura y cerrado de tabla y form , de manera externa.

# Param :
# 0) Path real al directorio.
# 1) Path virtual para hacer los links.
# 2) Tipo de entradas del directorio : <digitos>.html o normales ('DIG' | 'NORM')

  my($dir,$lnkdir,$tipo) = ($_[0],$_[1],$_[2]);
  my($i,$totsize,$titulo,$buffer) = (0,0,'','');

  # Abre directorio.
  opendir(DIR, $dir) || die "Can't opendir" . $dir . $!;
  @entries = readdir(DIR);
  closedir DIR;

  #Ordena entries alfabeticamente.
  @entries = sort @entries;

  foreach $entry (@entries) {
    my($thefile) = "$dir/$entry";
    # print "<P> thefile [$thefile]"; # debug
    if ((-f $thefile) and ($entry=~/\w.*\.html?/)) {
      if (($tipo eq 'DIG') && (not($entry =~ /^\d.*?/g))) {
         next;

      }

      my($size) = (-s $thefile);
      $size = int($size / 1000) + 1;
      $totsize += $size;
      $titulo = &lee_tit_file($thefile);
      print "<tr><td bgcolor=\"#ffffff\">"
          . "<a href=\"$lnkdir/$entry\" target=\"_blank\"><font size=-2 FACE=\"Arial\">"
          . "[$entry] </font><font size=-1 FACE=\"Arial\"><b>$titulo</b></font></a></td>\n";
      print "<td bgcolor=\"#ffffff\" align=\"right\">$size k</TD>\n";
      print "<td bgcolor=\"#ffffff\" align=\"center\"><input type=\"checkbox\" name=\"chkfile$i\" value=\"$entry\"></td></tr>\n";
      $i++;
    };
  };
  print "<tr><td align=\"right\">TOTAL</td><td align=\"right\">$totsize k</td><td>&nbsp;</td></tr>\n";

};

#-------------------------------------------------------------------------#
sub lee_tit_text {
# Lee el contenido del tag <TITLE> de un texto.

# Param :
# 0) Texto html al que se le extraera el title

# Retorna : El titulo.


  my($text) = $_[0];

  $text =~ /<TITLE>(.+)<\/TITLE>/isg;
  $text = $1;

  # Retorna el titulo
  return $text;

};

#-------------------------------------------------------------------------#
sub lee_tit_file {
# Lee el contenido del tag <TITLE> de un archivo html.

# Param :
# 0) Archivo html al que se le extraera el title

# Retorna : El titulo.

  my($file) = $_[0];
  my($text, $buffer, $numbytes);

  # Lee archivo.
  open (ARCHIVO,"<$file")
    || die "Fail Open file $archivo \n $!\n";
  binmode ARCHIVO;

  $numbytes = (-s $file);
  read ARCHIVO,$buffer,$numbytes;  # 2.1
  close ARCHIVO;

  $text = &lee_tit_text($buffer);

  return $text;

};

#-------------------------------------------------------------------------#
sub lee_meta_text {
# Lee el contenido del tag <META...> de un texto.

# Param :
# 0) Nombre del metatag
# 1) Texto html donde se encuentra el metatag.

# Retorna : Contenido del metatg especificado.

  my($name,$buffer) = ($_[0],$_[1]);

  if ($buffer =~ /<META\s+NAME="$name"\s+CONTENT="(.*?)"\s*>/isg) {
    return $1;
  }else{
    return '';
  };

};

#-------------------------------------------------------------------------#
sub inserta_meta_text {
# Inserta un tag META en la seccion HEAD de un texto HTML.

# Param :
# 0) Nombre del metatag
# 1) Contenido del metatag
# 2) Texto html donde se desea insertar el metatag.

# Retorna : Contenido del metatg especificado.

  my($name,$content,$buffer) = ($_[0],$_[1],$_[2]);

  my($meta) = '<META NAME="' . $name . '" CONTENT="' . $content . '">';

  $buffer =~ s/<HEAD>/<HEAD>\n$meta/sg;

  return $buffer;

};

#--------------------------------------------------------------------#
sub parsea_tabla {
# Convierte el string pasado como parametro (texto separado por tabuladores
# y retornos de carro) en una tabla HTML.
# Si en vez de venir texto, viene la tabla, la convierte en texto y la reformatea
# para generarla libre de basura.

# Param :
# 0) String a convertir.
# 1) String con la lista de valores (separados por ",") que determinan
# el formato de la tabla :
#($tbl_width,$tbl_padding,$tbl_border,$tbl_spacing,
# $tbl_hcolor,$tbl_vcolor,$tbl_color,$tbl_alin,$tbl_class). $tbl_alin es de la forma
# 'LCRRRLL' donde c/letra indica la alineacion de cada columna de la tabla.
# 2) Valor del atributo ALIGN de la tabla (alineacion de la tabla con respecto a la pag. web.

# Retorna : El cod. html correspondiente a la tabla generada.

  my($theText,$settings,$ali) = ($_[0],$_[1],$_[2]);
  my($TABLA,$celdas,$maxceldas,$first_line,$first_cell,$color,$class,$aux);
  my(@celdas);
  my(%align) = ('L','LEFT',
                   'R','RIGHT',
                   'C','CENTER');
  my($tbl_width,$tbl_padding,$tbl_border,$tbl_spacing,
        $tbl_hcolor,$tbl_vcolor,$tbl_color,$tbl_alin,$tbl_class) = split(/,/,$settings);

  # Si es una tabla html, asi que hay que convertirla a texto.
  if (&table_kind($theText) eq 'HTML') {
    $theText = &table2text($theText);
  };
  my(@lineas) = split(/\r/,$theText);

  # Borra ultimas lineas si es que estan vacias.
  do {
    $aux = $lineas[$#lineas]; # Extrae ultima linea.
    $aux =~ s/\W//sg;         # Borra todo lo que no es alfanumerico.
    if ( length($aux) == 0 ) { $#lineas--; }; # Si no hay contenido, borra la linea.
  } until ((length($aux) > 0) || ($#lineas <= 0));

  $maxceldas = 0;

  # Determina maximo de celdas.
  foreach $linea (@lineas) {
    $celdas = split(/\t/,$linea);
    if ($celdas > $maxceldas) {
      $maxceldas = $celdas;
    };
  };

  # Modificacion 01f
  if ($ali eq '') {
    $ali = $tbl_alin;
  };

  $TABLA = "<table width=\"$tbl_width\" border=\"$tbl_border\" cellspacing=\"$tbl_spacing\" "
         . "cellpadding=\"$tbl_padding\" align=\"$ali\" class=\"$tbl_class\">\r\n";

  $first_line = 1;
  foreach $linea (@lineas) {
    $TABLA .= "<TR>\r\n";
#    print "[$linea]\r\n"; # !!!
    $linea .= "\n"; # Truco para que no anule las celdas vacias.
    @celdas = split(/\t/,$linea);
    $first_cell = 1;
    my($i) = 0;
    foreach $celda (@celdas) {
      my($al) = $align{ substr($tbl_alin,$i,1) };
      $color = $tbl_color;
      $class = 'CLASS=TCELL';
      if ($first_cell) {
        $first_cell = 0;
        $color = $tbl_vcolor;
        $class = 'CLASS=TFCOL';
      };
      if ($first_line) {
        $color = $tbl_hcolor;
        $class = 'CLASS=TFLIN';
      };
      $celda =~ s/[\r\n]$//g;  # Borra los line-feeds o CRs que puedan haberse colado al final de la celda.
      $celda =~ s/(.)[\r\n]/$1<BR>\n/sg;  # Cambia los line-feeds o CRs por <BR>.
      $celda =~ s/"//sg;                  # Elimina las comillas.
      if ($celda eq '') { $celda = '&nbsp;'; };
      $al = $align{ substr($tbl_alin,$i,1) };
      my($colspan) = '';
      if ($i==0) {
        $colspan = $maxceldas - (scalar @celdas) + 1;
        if ($colspan > 1) {
          $class = "CLASS=TSPAN$colspan";
        }
        $colspan = "COLSPAN=\"$colspan\"";
      }
      $TABLA .= "<TD $colspan BGCOLOR=\"$color\" VALIGN=\"TOP\" ALIGN=\"$al\">" .
                "<P $class>$celda</P></TD>\r\n";
      $i++;
    };
    $first_line = 0;
    $TABLA .= "</TR>\r\n";
  };
  $TABLA .= '</TABLE>';

  return $TABLA;


};

#------------------------------------------------------------------#
sub table_kind {
# Determina si el string pasado como parametro es una tabla
# HTML o TEXT.

  if (($_[0] =~ s/<TD/<TD/isg) > ($_[0] =~ s/\t/\t/sg)) {  # 01g
    return 'HTML';
  }else{
    return 'TEXT';
  };

};

#------------------------------------------------------------------#
sub table2text {
# Toma una tabla en formato HTML y la transforma en texto separado
# por tabuladores.

# Param :
# 0) Texto html correspondiente a la tabla.

# Retorna : la tabla convertida a texto separado por tabuladores
# y retornos de carro.


  my($html) = $_[0];

  # Transforma en blancos todos los caracteres no visibles.
  $html =~ s/[\x00-\x20]/ /sg;       #Caracteres 1..32 van a blanco.

  # Separa la (primera) tabla contenida en el html.
  $html =~ /<TABLE[^>]*?>(.*?)<\/TABLE[^>]*?>/isg; # 01g
  $html = $1;

  # Separa el texto en lineas.
  my(@lineas) = split(/<TR[^>]*>/i,$html); # Matchea tbn las minusculas. # 01e
  shift(@lineas); # Descarta primera linea.

  # Inicializa variable de salida.
  my($res) = '';

  # Para cada linea, separa las lineas en celdas y las agrega
  # a la salida.
  foreach $linea (@lineas) {
    my(@celdas) = split(/<TD[^>]*>/i,$linea);
    shift(@celdas); # Descarta primera celda.
    # Para cada celda, limpia la basura que agrega Billy y la
    # pone en la salida.
    foreach $celda (@celdas) {
      $res .= &html2text($celda) . "\t";
    };
    chop($res); # Saca ultimo tab
    $res .= "\r";
  };
  chomp($res);  # Saca ultimos retornos de carro o line feeds.

  return $res;

}

#------------------------------------------------------------------#
sub html2text {
# Toma un texto html y lo despulga de todas las basuras que le
# agrega Billy, excepto los <P> y los <BR>, que son transformados
# en \n.
# Los caracteres especiales permanecen tal cual.

# Param :
# 0) Texto html a convertir en texto normal.

# Retorna : texto convertido.

  my($texto) = $_[0];

  $texto =~ s/(<P[^>]*>|<BR[^>]*>)/\n/isg; # Transforma los <P> y los <BR> en \n. # 01e
  $texto =~ s/<[^>]*>//isg;                # Elimina todos los tags. # 01e
  $texto =~ s/^\s*\n//isg;                 # Elimina newline al ppio de la celda. # 01e

  return $texto;

};

#-------------------------------------------------------------------------#
# Modificacion 01a:
sub lee_head_text {
# Lee el contenido del tag <HEAD> de un texto.

# Param :
# 0) Texto html al que se le extraera el HEAD

# Retorna : El texto contenido en el head.


  my($text) = $_[0];

  $text =~ /<HEAD>(.*?)<\/HEAD>/is;
  $text = $1;

  # Retorna el head
  return $text;

};


#-------------------------------------------------------------------------#
# Modificacion 01b:
sub generar_popup_from_dir {
# Genera un objeto de lista de seleccion html con la lista de archivos
# de un directorio dado, ordenados alfabeticamente. No considera subdirectorios.
# La lista generada utiliza el nombre del arch. s/path tanto para el valor de display
# como para los valores clave del combo.

# Parametros :
# 0) Path absoluto al directorio
# 1) Name que se le dara al popup generado
# 2) Valor clave en el que hay que dejar posicionado el combo.
# 3) Nro. de items visibles simultaneamente.
# 4) Indicador de seleccion multiple ('' o 'MULTIPLE')
# 5) Indicador de listar el articulo (en el display) con o sin extension ('SIN_EXT' o 'CON_EXT')
# 6) Registro adicional con clave '', por ej. 'Todos'.
# 7) Codigo javascript a invocar con el objeto.
# 8) Nro. maximo de elementos a cargar.
# 9) Criterio de orden ('NUMASC' | 'STRASC' | 'NUMDESC' | 'STRDESC' | 'NOSORT') si es 'NOSORT', enonces no se aplica ordenamiento.
#    Equivalencias : NUMERICO ASCENDENTE | STRING ASCENDENTE | NUMERICO DESCENDENTE | STRING DESCENDENTE

# Retorna : Lista de seleccion con datos, lista para imprimirla.

  my($path_dir) = $_[0];
  my($name_obj) = $_[1];
  my($valor_clave) = $_[2];
  my($items_visibles) = $_[3];
  my($ind_multiple) = $_[4];
  my($ind_extension) = $_[5];
  my($adicional) = $_[6];
  my($javascript) = $_[7];
  my($max_elem) = $_[8];
  my($criterio_orden) = $_[9];

  my(@entries, $lista, $nom_arch, $seleccionado, $nro_elem, $entry);


  # Abre directorio.
  opendir(DIR, $path_dir) || die "Can't opendir" . $path_dir . $!;
  @entries = readdir(DIR);
  closedir DIR;

  # Ordena entries
  if ($criterio_orden eq 'NUMASC') {
    # Ascendentemente.
    @entries = sort {$a <=> $b} (@entries);
  }
  elsif ($criterio_orden eq 'NUMDESC') {
    # Descendentemente.
    @entries = sort {$b <=> $a} (@entries);
  }
  elsif ($criterio_orden eq 'STRASC') {
    # Descendentemente.
    @entries = sort {$a cmp $b} (@entries);
  }
  elsif ($criterio_orden eq 'STRDESC') {
    # Descendentemente.
    @entries = sort {$b cmp $a} (@entries);
  };


  # Generar la lista de seleccion en html
  $lista = q{<select name="} . $name_obj . q{" size="} . $items_visibles . q{" } . $ind_multiple . ' ' . $javascript . q{>};

  if ($adicional ne '') {
    $lista = $lista . '<option value="" ' . $seleccionado .'">';
    $lista = $lista . $adicional;
  }

  $nro_elem = 0;
  foreach $entry (@entries) {
    if ($entry !~ /^\./g) {
      if ((-f("$path_dir/$entry")) and ($nro_elem < $max_elem)) {
        $nom_arch = $entry;

        $seleccionado = '';
        if ( $nom_arch eq $valor_clave ) {
           $seleccionado = 'selected="selected"';
        }
        $lista = $lista . '<option value="' . $nom_arch . '" ' . $seleccionado .'>';
        if ($ind_extension eq 'SIN_EXT') {
          $nom_arch =~ s/\..*//; # borrar extension en el display.
        }
        $lista = $lista . $nom_arch . '</option>'; # 01.i
        $nro_elem = $nro_elem + 1;
      }
    }
  }


  $lista = $lista . q{</select>};
  return $lista;

}

#-------------------------------------------------------------------------#
# Funcion para generar filas para una tabla generica de prontus
# Parametros:
# 0) arreglo de hash con los valores y labels de los checkbox., por ejemplo:
#my @fidlist;
#foreach my $fid_file (@fids_listado) {
#    if ($fid_file =~ /fid_(.*?)\.html/) {
#        my $fid_name = "fid_$1";
#        if ($cfg_buscador{'FIDS'} =~ /( |^)$fid_file( |$)/) {
#            push @fidlist, {label    => $fid_name, value   => $fid_file, checked => 1};
#        } else {
#            push @fidlist, {label    => $fid_name, value   => $fid_file, checked => 0};
#        };
#    };
#};
# 1) nombre del input del checkbox, se recomienda usar del tipo arreglo.. por ejemplo: valores[]
# Invocacion:
# my $filas_tabla_checkbox = &glib_html_02::generar_filas_tabla_checkbox(\@fidlist, 'INPUT_FIDS[]');

sub generar_filas_tabla_checkbox {
    my $arrayref = $_[0];
    my @itemlist = @$arrayref;
    my $name = $_[1];
    my $ident = $_[2];
    my $buffer;
    my $counter=1;
    foreach my $item (@itemlist) {
        my $checked = '';
        my $id = $name;
        $id =~ s/\[|\]//sig;
        
        if ($item->{checked} == 1) {
            $checked = ' checked="checked"';
        };
        
        $buffer .= '
        <tr>
            <td align="left"><label for="'. $ident . $id . $counter . '">' . $item->{label} . '</label></td>
            <td align="center"><input type="checkbox" id="'. $ident . $id . $counter. '" name="' . $name . '" value="' . $item->{value} . '"' . $checked . '/></td>
        </tr>
        ';
        $counter++;
    };
    
    return $buffer;
    
};

#-------------------------------END LIBRERIA------------------

return 1;
