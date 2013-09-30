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
#

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 01   : 28/11/2001 - MCO - Primera version.
# 01.1 : 11/01/2002 - MCO - Nueva funcion 'gen_arch_bitac', recibe texto y lo graba en archivo de bitacora
#                           junto con hora y usuario que hizo la accion (cookie). Devuelve nada.
#                           Si el archivo no existe lo crea, sino agrega en una nueva fila la informacion.
#                           Guarda archivo con nombre dd.log en directorio aaaamm (si directorio no existe, lo crea).

#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package lib_secc;

use glib_dbi_02;
use glib_html_02;
use glib_fildir_02;

use strict;

#---------------------------------------------------------------
# SUB-RUTINAS.
#--------------------------------------------------------------------#
sub print_pag_html {
# Imprime pagina con reporte de resultado o mensajes.

# Param :
# 0) Plantilla mensajes
# 1) Titulo del mensaje
# 2) Mensaje a imprimir
# 3) Si se llama desde una ventana (popup) o de una pagina.

  my ($plantilla) = $_[0];
  my ($tit) = $_[1];
  my ($result) = $_[2];
  my ($tipo) = $_[3];
  my ($pagina, $size_arch, $link);

# Abrir y cargar ARCHIVO corresp. a la plantilla
#   open (ARCHIVO, $plantilla) || die "$!\n";
#   $size_arch = (-s $plantilla);
#   read ARCHIVO, $pagina, $size_arch;
#   close ARCHIVO;

  if ($tipo eq 'ventana') {
    $tipo = 'window.close();opener.focus();';
    $link = 'Cerrar';
  }
  elsif ($tipo eq 'pagina') {
    $tipo = 'history.back()';
    $link = 'Volver';
  };

  $pagina = &glib_html_02::rellenar_plantilla(4, '%%TITLE%%', $tit ,'','',
                                                '%%MENSAJE%%', $result, '', '',
                                                '%%LINK%%', $link, '', '',
                                                '%%TIPO_LINK%%', $tipo, '', '',
                                                  $plantilla);
  $pagina =~ s/%%REL_PATH_PRONTUS%%/$prontus_varglb::RELDIR_BASE\/$prontus_varglb::PRONTUS_ID/isg;
  print $pagina;

};

# ---------------------------------------------------------------
sub salir {
  my $msg = $_[0];
  print "Content-Type: text/html\n\n";
  print $msg;
  exit;
};
# ---------------------------------------------------------------
sub basic_escape_html {
  my $toencode = $_[0];
  $toencode=~s/&([^#][^0-9]+)/&amp;\1/g;             # Antes que nada, traduce los ampersands. # 1.19 correccion a e.r.
  $toencode=~s/>/&gt;/g;              # >
  $toencode=~s/"/&quot;/g;            # " # 8.0
  $toencode=~s/'/&#39;/g;
  $toencode=~s/</&lt;/g;              # <
  return $toencode;
};
# ---------------------------------------------------------------
sub genera_array_temas_subtemas {
  my ($bd, $opcion) = ($_[0], $_[1]);
  my ($only_enabled) = $_[2];
  my ($sql, $salida, $array_texto_temas, $array_valor_temas, $array_texto_subtemas, $array_valor_subtemas, $aux_idseccion, $aux_idtemas);
  my ($seccion_id, $temas_id, $temas_nom, $subtemas_id, $subtemas_nom);
  my ($array_texto_temas2, $array_valor_temas2, $array_texto_subtemas2, $array_valor_subtemas2);



  # Genera arreglos, considerando secciones con temas

  if ($only_enabled) { # solo las habilitadas
    $sql = "select SECC_ID, TEMAS_ID, TEMAS_NOM from TEMAS, SECC where SECC_ID = TEMAS_IDSECC and TEMAS_MOSTRAR = '1'  order by SECC_ID, TEMAS_ORDEN";
  }
  else {
    $sql = "select SECC_ID, TEMAS_ID, TEMAS_NOM from TEMAS, SECC where SECC_ID = TEMAS_IDSECC  order by SECC_ID, TEMAS_ORDEN";
  };
  $salida = &glib_dbi_02::ejecutar_sql_bind($bd, $sql, \($seccion_id, $temas_id, $temas_nom));

  $array_texto_temas = "\r\n// Arreglos de texto de las combo de temas. ";
  $array_valor_temas = "\r\n// Arreglos de valores (id) de las combo de temas. ";
  $aux_idseccion = 0;
  my $and_sin_temas;
  while ($salida->fetch) {
    if ($seccion_id != $aux_idseccion) {
      $and_sin_temas .= " and SECC_ID <> $seccion_id ";
      $array_texto_temas = substr($array_texto_temas, 0, length($array_texto_temas) - 1); # Eliminacion de la ultima coma.
      $array_valor_temas = substr($array_valor_temas, 0, length($array_valor_temas) - 1); # Eliminacion de la ultima coma.

      $array_texto_temas .= ");" if $aux_idseccion > 0; # Termino del arreglo.
      $array_valor_temas .= ");" if $aux_idseccion > 0; # Termino del arreglo.

      $array_texto_temas .= "\r\nvar arreglo_temas_$seccion_id\_texto = new Array("; # Inicio del arreglo.
      $array_valor_temas .= "\r\nvar arreglo_temas_$seccion_id\_valor = new Array("; # Inicio del arreglo.

      if ($opcion eq 'todos') {
        $array_texto_temas .= "'Todos',";
        $array_valor_temas .= "'0',";
      };
    };
    # $temas_nom = &basic_escape_html($temas_nom);
    $array_texto_temas .= "'$temas_nom',";
    $array_valor_temas .= "'$temas_id',";

    $aux_idseccion = $seccion_id;
  };

  $salida->finish;


  # Completa arreglo, considerando secciones sin temas
#  $sql = "select SECC_ID from SECC where SECC_ID <> '0'  $and_sin_temas order by SECC_ORDEN";
  if ($only_enabled) { # solo las habilitadas
    $sql = "select distinct(SECC_ID) from TEMAS, SECC where SECC_ID <> TEMAS_IDSECC  and TEMAS_MOSTRAR = '1' $and_sin_temas order by SECC_ID, TEMAS_ORDEN";
  }
  else {
    $sql = "select distinct(SECC_ID) from TEMAS, SECC where SECC_ID <> TEMAS_IDSECC  $and_sin_temas order by SECC_ID, TEMAS_ORDEN";
  };
  # warn "sql[$sql]";



  $salida = &glib_dbi_02::ejecutar_sql_bind($bd, $sql, \($seccion_id));

  $array_texto_temas2 = "\r\n// Arreglos de texto de las combo de temas. ";
  $array_valor_temas2 = "\r\n// Arreglos de valores (id) de las combo de temas. ";
  $aux_idseccion = 0;
  $temas_nom = '';
  $temas_id = '0';
  while ($salida->fetch) {
    if ($seccion_id != $aux_idseccion) {
      $array_texto_temas2 = substr($array_texto_temas2, 0, length($array_texto_temas2) - 1); # Eliminacion de la ultima coma.
      $array_valor_temas2 = substr($array_valor_temas2, 0, length($array_valor_temas2) - 1); # Eliminacion de la ultima coma.

      $array_texto_temas2 .= ");" if $aux_idseccion > 0; # Termino del arreglo.
      $array_valor_temas2 .= ");" if $aux_idseccion > 0; # Termino del arreglo.

      $array_texto_temas2 .= "\r\nvar arreglo_temas_$seccion_id\_texto = new Array("; # Inicio del arreglo.
      $array_valor_temas2 .= "\r\nvar arreglo_temas_$seccion_id\_valor = new Array("; # Inicio del arreglo.

      if ($opcion eq 'todos') {
        $array_texto_temas2 .= "'Todos',";
        $array_valor_temas2 .= "'0',";
      };
    };

    # $temas_nom = &basic_escape_html($temas_nom);
    $array_texto_temas2 .= "'$temas_nom',";
    $array_valor_temas2 .= "'$temas_id',";

    $aux_idseccion = $seccion_id;
  };

  $salida->finish;






  $array_texto_temas = substr($array_texto_temas, 0, length($array_texto_temas) - 1); # Eliminacion de la ultima coma.
  $array_valor_temas = substr($array_valor_temas, 0, length($array_valor_temas) - 1); # Eliminacion de la ultima coma.

  $array_texto_temas .= ");\r\n"; # Termino del arreglo.
  $array_valor_temas .= ");\r\n"; # Termino del arreglo.

  $array_texto_temas .= "\r\nvar arreglo_temas_0\_texto = new Array("; # Inicio del arreglo.
  $array_valor_temas .= "\r\nvar arreglo_temas_0\_valor = new Array("; # Inicio del arreglo.

  $array_texto_temas .= "'Todas'" if $opcion eq 'todos';
  $array_texto_temas .= "'--Seleccione niv. subtemas--'" if $opcion eq 'seleccione';

  $array_valor_temas .= "'0'";

  $array_texto_temas .= ");\r\n"; # Termino del arreglo.
  $array_valor_temas .= ");\r\n"; # Termino del arreglo.



  $array_texto_temas2 = substr($array_texto_temas2, 0, length($array_texto_temas2) - 1); # Eliminacion de la ultima coma.
  $array_valor_temas2 = substr($array_valor_temas2, 0, length($array_valor_temas2) - 1); # Eliminacion de la ultima coma.

  $array_texto_temas2 .= ");\r\n"; # Termino del arreglo.
  $array_valor_temas2 .= ");\r\n"; # Termino del arreglo.

  $array_texto_temas2 .= "\r\nvar arreglo_temas_0\_texto = new Array("; # Inicio del arreglo.
  $array_valor_temas2 .= "\r\nvar arreglo_temas_0\_valor = new Array("; # Inicio del arreglo.

  $array_texto_temas2 .= "'Todas'" if $opcion eq 'todos';
  $array_texto_temas2 .= "'--Seleccione niv. subtemas--'" if $opcion eq 'seleccione';

  $array_valor_temas2 .= "'0'";

  $array_texto_temas2 .= ");\r\n"; # Termino del arreglo.
  $array_valor_temas2 .= ");\r\n"; # Termino del arreglo.

  # ------------------------

  # Genera arreglos considerando temas con subtemas.

  if ($only_enabled) { # solo las habilitadas
    $sql = "select TEMAS_ID, SUBTEMAS_ID, SUBTEMAS_NOM from SUBTEMAS, TEMAS where TEMAS_ID = SUBTEMAS_IDTEMAS and TEMAS_ID > 0 and SUBTEMAS_ID > 0 and SUBTEMAS_MOSTRAR = '1' order by TEMAS_ID, SUBTEMAS_ORDEN";
  }
  else {
    $sql = "select TEMAS_ID, SUBTEMAS_ID, SUBTEMAS_NOM from SUBTEMAS, TEMAS where TEMAS_ID = SUBTEMAS_IDTEMAS and TEMAS_ID > 0 and SUBTEMAS_ID > 0 order by TEMAS_ID, SUBTEMAS_ORDEN";
  };

  # warn "sql_temas_subtemas[$sql]";

  $salida = &glib_dbi_02::ejecutar_sql_bind($bd, $sql, \($temas_id, $subtemas_id, $subtemas_nom));

  $array_texto_subtemas = "\r\n// Arreglos de texto de las combo de subtemas. ";
  $array_valor_subtemas = "\r\n// Arreglos de valores (id) de las combo de subtemas. ";

  $aux_idtemas = 0;
  my $and_sin_subtemas;
  while ($salida->fetch) {
    if ($temas_id != $aux_idtemas) {
      $and_sin_subtemas .= " and TEMAS_ID <> $temas_id ";
      $array_texto_subtemas = substr($array_texto_subtemas, 0, length($array_texto_subtemas) - 1); # Eliminacion de la ultima coma.
      $array_valor_subtemas = substr($array_valor_subtemas, 0, length($array_valor_subtemas) - 1); # Eliminacion de la ultima coma.

      $array_texto_subtemas .= ");" if $aux_idtemas > 0; # Termino del arreglo.
      $array_valor_subtemas .= ");" if $aux_idtemas > 0; # Termino del arreglo.

      $array_texto_subtemas .= "\r\nvar arreglo_subtemas_$temas_id\_texto = new Array("; # Inicio del arreglo.
      $array_valor_subtemas .= "\r\nvar arreglo_subtemas_$temas_id\_valor = new Array("; # Inicio del arreglo.

      if ($opcion eq 'todos') {
        $array_texto_subtemas .= "'Todos',";
        $array_valor_subtemas .= "'0',";
      };
    };

    # $subtemas_nom = &basic_escape_html($subtemas_nom);

    $array_texto_subtemas .= "'$subtemas_nom',";
    $array_valor_subtemas .= "'$subtemas_id',";

    $aux_idtemas = $temas_id;
  };

  $salida->finish;

  $array_texto_subtemas = substr($array_texto_subtemas, 0, length($array_texto_subtemas) - 1); # Eliminacion de la ultima coma.
  $array_valor_subtemas = substr($array_valor_subtemas, 0, length($array_valor_subtemas) - 1); # Eliminacion de la ultima coma.

  $array_texto_subtemas .= ");\r\n"; # Termino del arreglo.
  $array_valor_subtemas .= ");\r\n"; # Termino del arreglo.

  $array_texto_subtemas .= "\r\nvar arreglo_subtemas_0\_texto = new Array("; # Inicio del arreglo.
  $array_valor_subtemas .= "\r\nvar arreglo_subtemas_0\_valor = new Array("; # Inicio del arreglo.

  $array_texto_subtemas .= "'Todos'" if $opcion eq 'todos';
  $array_texto_subtemas .= "'--------Seleccione subtema--------'" if $opcion eq 'seleccione';
  $array_valor_subtemas .= "'0'";

  $array_texto_subtemas .= ");\r\n"; # Termino del arreglo.
  $array_valor_subtemas .= ");\r\n"; # Termino del arreglo.




  # Genera arreglos considerando temas sin subtemas.
  $sql = "select distinct(TEMAS_ID) from TEMAS where TEMAS_ID <> '0' $and_sin_subtemas order by TEMAS_ID";


  $salida = &glib_dbi_02::ejecutar_sql_bind($bd, $sql, \($temas_id));

  $array_texto_subtemas2 = "\r\n// Arreglos de texto de las combo de subtemas. ";
  $array_valor_subtemas2 = "\r\n// Arreglos de valores (id) de las combo de subtemas. ";

  $aux_idtemas = 0;
  $subtemas_nom = ' ';
  $subtemas_id = '0';
  while ($salida->fetch) {
    if ($temas_id != $aux_idtemas) {
      $array_texto_subtemas2 = substr($array_texto_subtemas2, 0, length($array_texto_subtemas2) - 1); # Eliminacion de la ultima coma.
      $array_valor_subtemas2 = substr($array_valor_subtemas2, 0, length($array_valor_subtemas2) - 1); # Eliminacion de la ultima coma.

      $array_texto_subtemas2 .= ");" if $aux_idtemas > 0; # Termino del arreglo.
      $array_valor_subtemas2 .= ");" if $aux_idtemas > 0; # Termino del arreglo.

      $array_texto_subtemas2 .= "\r\nvar arreglo_subtemas_$temas_id\_texto = new Array("; # Inicio del arreglo.
      $array_valor_subtemas2 .= "\r\nvar arreglo_subtemas_$temas_id\_valor = new Array("; # Inicio del arreglo.

      if ($opcion eq 'todos') {
        $array_texto_subtemas2 .= "'Todos',";
        $array_valor_subtemas2 .= "'0',";
      };
    };

    # $subtemas_nom = &basic_escape_html($subtemas_nom);

    $array_texto_subtemas2 .= "'$subtemas_nom',";
    $array_valor_subtemas2 .= "'$subtemas_id',";

    $aux_idtemas = $temas_id;
  };

  $salida->finish;

  $array_texto_subtemas2 = substr($array_texto_subtemas2, 0, length($array_texto_subtemas2) - 1); # Eliminacion de la ultima coma.
  $array_valor_subtemas2 = substr($array_valor_subtemas2, 0, length($array_valor_subtemas2) - 1); # Eliminacion de la ultima coma.

  $array_texto_subtemas2 .= ");\r\n"; # Termino del arreglo.
  $array_valor_subtemas2 .= ");\r\n"; # Termino del arreglo.

  $array_texto_subtemas2 .= "\r\nvar arreglo_subtemas_0\_texto = new Array("; # Inicio del arreglo.
  $array_valor_subtemas2 .= "\r\nvar arreglo_subtemas_0\_valor = new Array("; # Inicio del arreglo.

  $array_texto_subtemas2 .= "'Todos'" if $opcion eq 'todos';
  $array_texto_subtemas2 .= "'--------Seleccione subtema--------'" if $opcion eq 'seleccione';
  $array_valor_subtemas2 .= "'0'";

  $array_texto_subtemas2 .= ");\r\n"; # Termino del arreglo.
  $array_valor_subtemas2 .= ");\r\n"; # Termino del arreglo.

  return $array_texto_temas . $array_valor_temas . $array_texto_temas2 . $array_valor_temas2 . "\r\n\r\n" . $array_texto_subtemas . $array_valor_subtemas . $array_texto_subtemas2 . $array_valor_subtemas2;
}; # genera_array_temas_subtemas.



# ---------------------------------------------------------------
sub parse_seccion {
  my ($pag) = $_[0];
  my ($base) = $_[1];
  my ($only_enabled) = $_[2];
  my ($sql, $combo, $i, $combo_aux);
  # Generar las combos.
  if ($only_enabled) { # solo las habilitadas
    $sql = "select SECC_ID, SECC_NOM from SECC where SECC_MOSTRAR = '1' order by SECC_ORDEN";
  }
  else { # todas
    $sql = "select SECC_ID, SECC_NOM from SECC order by SECC_ORDEN";
  };
  $combo = &gen_popup_from_sql_escaped($base, $sql, '_SECCION%%i%%', 1, '', '');
  $combo =~ s/<(select .*?)>/<\1 class="P-DATATABLA" onchange="CombosTax.generaTemas(%%i%%);">/is;
  $combo = &add_items_adicionales($combo, 'Secci&oacute;n');

  $combo_aux = $combo;
  for ($i=1;$i<=3;$i++) {
    $combo =~ s/%%i%%/$i/g;
    $pag =~ s/%%_?SECCION$i%%/$combo/;
    $combo = $combo_aux;
  };
  return $pag;
};
#---------------------------------------------------------------
sub gen_popup_from_sql_escaped {
# Genera un objeto de lista de seleccion con la info suministrada

# Parametros :
# 0)sentencia sql. El orden de los campos requeridos es primero el del value y luego el de display
# 1)base de datos abierta
# 2)nombre que se le dara al objeto generado
# 3)nro. de items visibles
# 4)indicador de seleccion multiple ('' o 'MULTIPLE')
# 5)valor del VALUE en el cual se deberá posicionar el cursor

# Retorna : Lista de seleccion con datos, lista para imprimirla.

  my($base) = $_[0];        # 02.1
  my($sentencia) = $_[1];
  my($name_obj) = $_[2];
  my($items_visibles) = $_[3];
  my($ind_multiple) = $_[4];
  my($valor_clave) = $_[5];

  my($tab_output);
  my($campo_value);
  my($campo_display);


  $tab_output = &glib_dbi_02::ejecutar_sql($base, $sentencia);
  $tab_output->bind_columns(undef, \(
                                     $campo_value,
                                     $campo_display
                                       ));

  # Generar la lista de seleccion en html
  my $lista = q{<select name="} . $name_obj . q{" size="} . $items_visibles . q{" } . $ind_multiple . q{>};
  my $seleccionado;
  while($tab_output->fetch){
    $seleccionado = '';
    if ( $campo_value eq $valor_clave ) {
       $seleccionado = 'selected="selected"';
    }
    $campo_display = &basic_escape_html($campo_display);
    $lista .= "\n" . '<option value="' . $campo_value . '" ' . $seleccionado . ' title="'.$campo_display.'">';
    $lista .= "$campo_display</option>";
  };
  $lista = $lista . q{</select>};
  return $lista;
};

# ---------------------------------------------------------------
sub add_items_adicionales {
  my ($combo, $entidad) = ($_[0], $_[1]);

  # $combo =~ s/<\/select>/<option value="" selected>\-\- Selecc $entidad\-\-<\/option><\/select>/is;
  $combo =~ s/<option /<option value="" selected><\/option><option /is;
  return $combo;
};




return 1;

# -------------------------------END LIBRERIA--------------------
