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
# Desplegar la pagina de filtros de la megalupa.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# No registra.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------

# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------

# ---------------------------------------------------------------

# HISTORIAL DE VERSIONES.
# ---------------------------
# 01 - Viernes 02/06/2000 - Primera Version.

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};
use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use lib_prontus;
use glib_html_02;

use glib_cgi_04;

use DBI;
use glib_dbi_02;
use lib_secc;

# ---------------------------------------------------------------
# MAIN.
# -------------

  my ($BD, %FORM);

  #  print "Content-Type: text/html\n\n"; # debug
  # Rescatar parametros recibidos.
  &glib_cgi_04::new();

  $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

  # print STDERR "BD[$prontus_varglb::NOM_BD]";

  &lib_prontus::load_config($FORM{'_path_conf'});
  $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;


  my $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/prontus_art_megalupa.html";

  my $pagina = &glib_fildir_02::read_file($plantilla);


  # Conectar a BD
  my $msg_err_bd;
  ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
  if (! ref($BD)) {
      &glib_html_02::print_pag_result("Error",$msg_err_bd,1,'exit=1,ctype=1');
  };


  my $arr_tst = &lib_secc::genera_array_temas_subtemas($BD, '');
  $pagina =~ s/%%ARR_TST%%/$arr_tst/;
  $pagina = &lib_secc::parse_seccion($pagina, $BD);
  # CVI - En este caso el onchange se manejara a nivel de jquery
  $pagina =~ s/ onchange=".*?"//is;
  $pagina =~ s/(<\/select>)/<option value="SS">- Art&iacute;culos sin secci&oacute;n -<\/option>\1/is;
  my $tipos_art = &generar_popup_tipos();
  $tipos_art = &lib_secc::add_items_adicionales($tipos_art, '');

  $pagina =~ s/%%TIPART%%/$tipos_art/;

  $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/ig;

  if (! $prontus_varglb::TAXONOMIA_NIVELES ) {
    $pagina =~ s/<!--TAXONOMIA-->.*<!--\/TAXONOMIA-->//s;
  };

  if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS ne 'SI') {
    $pagina =~ s/<!--ALTA-->.*<!--\/ALTA-->//s;
  };

  if ($prontus_varglb::CONTROL_FECHA ne 'SI') {
    $pagina =~ s/<!--CONTROL_FECHA-->.*<!--\/CONTROL_FECHA-->//s;
  };

  $BD->disconnect;



  print "Content-Type: text/html\n\n";
  print $pagina;



# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
# ---------------------------------------------------------------
sub generar_popup_tipos {
# Generar combo de tipos de articulos, obteniendo la informacion desde
# el hash global definido en el arch. de configuracion.
# Retorna : Lista de seleccion con datos, lista para imprimirla.

  my($name_obj) = 'TIPART';
  my($valor_clave) = '';
  my($items_visibles) = '1';
  my($ind_multiple) = '';
  my($javascript) =  "";

  my($lista) = '';


  # print STDERR "FECHA:$FORM{'DIR_FECHA'}";

  my($val_display, $key, $clave);
  my($key2); # 1.11

  # Generar la lista de seleccion en html
  $lista = q{<select name="} . $name_obj . q{" size="} . $items_visibles . q{" } . $ind_multiple . ' ' . $javascript . q{>};

  # 8.0
  my (%sort_tipos, $tipo_glosa);
  foreach $key (keys %prontus_varglb::FORM_PLTS) {
    # El valor a mostrar esta despues de los 2 puntos en la clave.
    $tipo_glosa = $key;
    $tipo_glosa =~ s/^.*://;
    $sort_tipos{$key} = lc $tipo_glosa;
  };


  # foreach $key (keys %prontus_varglb::FORM_PLTS) {    # 8.0 se ordena popup por glosa de tipos de articulos.
  foreach $key (sort {$sort_tipos{$a} cmp $sort_tipos{$b}} keys %prontus_varglb::FORM_PLTS) {
    # print "<br>key:$key"; # debug
    $val_display = $key;
    # El valor a mostrar esta despues de los 2 puntos en la clave.
    $val_display =~ s/^.*://;

    # La clave de los items de la combo sera lo que esta antes de los 2 puntos (nombre del arch. html que se usara como ficha).
    $clave = $key;

    $clave =~ s/:.*$//;

    my $seleccionado = '';
    if ( $clave eq $valor_clave ) {
       $seleccionado = 'selected';
    };



    if ( ($prontus_varglb::USERS_PERFIL eq 'P') or ($prontus_varglb::USERS_PERFIL eq 'E') ) { # Periodista o Editor
      # Mostrar solo los tipos de articulos permitidos al usuario conectado.
      foreach $key2 (keys %prontus_varglb::ARTUSERS) {
        my ($tipart, $usr) = split /\|/, $key2;
        if ( ($usr eq $prontus_varglb::USERS_ID) and ($tipart eq $clave) ) {
          $lista = $lista . '<option value="' . $clave . "\" $seleccionado>";
          $val_display = $key;
          # El valor a mostrar esta despues de los 2 puntos en la clave.
          $val_display =~ s/^.*://;
          $lista = $lista . $val_display . '</option>';
        };
      };
    }
    else { # admin
      # Mostrar todos los tipos.
      $lista = $lista . '<option value="' . $clave . "\" $seleccionado>";
      $val_display = $key;
      # El valor a mostrar esta despues de los 2 puntos en la clave.
      $val_display =~ s/^.*://;
      $lista = $lista . $val_display . '</option>';
    };


  };


  $lista = $lista . q{</select>};

  return $lista;

};

# -------------------------------END SCRIPT----------------------
