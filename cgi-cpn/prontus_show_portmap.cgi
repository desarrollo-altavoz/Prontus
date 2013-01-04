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
# Desplegar pagina con imagen de mapa de portada.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------

# ---------------------------------------------------------------

# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 03/07/2006 - Primera Version.

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
  $FORM{'nomport'} = &glib_cgi_04::param('nomport'); # onda portada.html
  $FORM{'path_conf'} = &glib_cgi_04::param('path_conf');
  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

  # print STDERR "BD[$prontus_varglb::NOM_BD]";

  &lib_prontus::load_config($FORM{'path_conf'});
  $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  my $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/prontus_show_portmap.html";

  my $pagina = &glib_fildir_02::read_file($plantilla);

  my $port_solonom = $FORM{'nomport'};
  $port_solonom =~ s/\..+$//; # saca extension
  $pagina =~ s/%%nomport%%/$port_solonom/g;
  $pagina =~ s/%%REL_PATH_PRONTUS%%/$prontus_varglb::RELDIR_BASE\/$prontus_varglb::PRONTUS_ID/g;
  $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/ig;

  $port_solonom .= '.gif';
  my $relpath_portmap = "$prontus_varglb::DIR_CPAN/port_map/$port_solonom";
  if (! -f "$prontus_varglb::DIR_SERVER$relpath_portmap") {
    $pagina =~ s/<!--img-->.*<!--\/img-->//is;
  }
  else {
    $pagina =~ s/<!--msg-->.*<!--\/msg-->//is;
    $pagina =~ s/%%_relpath_portmap%%/$relpath_portmap/ig;

  };


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
  $lista = q{<SELECT NAME="} . $name_obj . q{" SIZE="} . $items_visibles . q{" } . $ind_multiple . ' ' . $javascript . q{>};

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
       $seleccionado = 'SELECTED';
    };



    if ( ($prontus_varglb::USERS_PERFIL eq 'P') or ($prontus_varglb::USERS_PERFIL eq 'E') ) { # Periodista o Editor
      # Mostrar solo los tipos de articulos permitidos al usuario conectado.
      foreach $key2 (keys %prontus_varglb::ARTUSERS) {
        my ($tipart, $usr) = split /\|/, $key2;
        if ( ($usr eq $prontus_varglb::USERS_ID) and ($tipart eq $clave) ) {
          $lista = $lista . '<OPTION VALUE="' . $clave . "\" $seleccionado>";
          $val_display = $key;
          # El valor a mostrar esta despues de los 2 puntos en la clave.
          $val_display =~ s/^.*://;
          $lista = $lista . $val_display . '</OPTION>';
        };
      };
    }
    else { # admin
      # Mostrar todos los tipos.
      $lista = $lista . '<OPTION VALUE="' . $clave . "\" $seleccionado>";
      $val_display = $key;
      # El valor a mostrar esta despues de los 2 puntos en la clave.
      $val_display =~ s/^.*://;
      $lista = $lista . $val_display . '</OPTION>';
    };


  };


  $lista = $lista . q{</SELECT>};

  return $lista;

};

# -------------------------------END SCRIPT----------------------
