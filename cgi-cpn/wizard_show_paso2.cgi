#!/usr/bin/perl

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Muestra pagina a traves de la cual se escoge el modelo en base al que se generara el sitio prontus.
# Cada modelo tendra un cfg que permitira al motor del wizard desplegar al
# usuario lo que corresponda.
# Cada modelo tendra ademas una imagen representativa de éste y un link
# a descripción y observaciones del mismo.
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------
# No registra, imprime directamente al browser.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Via location desde wizard_paso1.cgi sin parametros.
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------------
# - Informacion de paso1 para verificacion:
# /wizard_prontus/data/inf.txt

# - Plantilla: /wizard_prontus/core/paso2.html

# - Informacion de modelos disponibles. Cada modelo es descrito por un cfg:
# /wizard_prontus/models/<nom_model>/<nom_model>.cfg
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ----------------------------
# No registra.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# No utiliza.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 01 - 11/2005 - YCH - Primera Version.


# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use strict;
use lib_prontus;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%PRONTUS);
my ($INF_DIR) = "$prontus_varglb::DIR_SERVER/wizard_prontus/data";
my ($INF_FILE) = "$INF_DIR/inf.txt";


main:{

  # Valida informacion de paso 1.
  my $msg_err = &check_paso1();
  if ($msg_err) {

    $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
    &glib_html_02::print_pag_result('Error', $msg_err, 0, "exit=1, ctype=1");
  };


  my $buffer = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER/wizard_prontus/core/paso2.html");
  $msg_err = '';
  ($msg_err, $buffer) = &carga_modelos($buffer);
  if ($msg_err) {

    $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
    &glib_html_02::print_pag_result('Error', $msg_err, 0, "exit=1, ctype=1");

  };

  print "Content-Type: text/html\n\n";
  print $buffer;



};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub check_paso1 {
# Chequea que se haya pasado por el paso 1

  if (! -f $INF_FILE) {
    return "[errInfFile] Solicitud de ejecución no válida.";
  };

  # Leer y cargar y validar contenido del paso1.
  my $buffer = &glib_fildir_02::read_file($INF_FILE);
  my $prontus_id;
  if ($buffer =~ /(\[PRONTUS\].*\[\/PRONTUS\]\n\n)/s) {
    my $buffer_prontus = $1;
    # Validar id
    if ($buffer_prontus !~ /PRONTUS_ID=(\w+)\n/) {
      return 'Información de paso previo está corrupta. Para poder continuar debe volver al paso anterior.';
    }
    else {
      $prontus_id = $1;
    };
  }
  else {
    return 'Información de paso previo está corrupta. Para poder continuar debe volver al paso anterior.';
  };

  # Validar que no exista el dir destino del prontus.
  # Esto ya se chequea en el paso 1 pero se hace nuevamente por seguridad.
  my $dir_prontus = "$prontus_varglb::DIR_SERVER/$prontus_id";

  if (-d $dir_prontus) {
    return "El directorio prontus ya existe. Para continuar con el proceso de instalación Ud. debe cambiar el nombre especificado para el publicador, o bien, <br>eliminar manualmente el directorio existente que genera el conflicto.";
  }
  else {
    # Lo creo y luego lo borro para verificar que este ok.
    if (&glib_fildir_02::check_dir($dir_prontus)) {
      &glib_fildir_02::borra_dir($dir_prontus);
    }
    else {
      return "No se puede crear el directorio destino del publicador. No es posible continuar con la instalación.";
    };
  };


  return '';

};
# ---------------------------------------------------------------
sub carga_modelos {
# Valida y carga modelos prontus disponibles.
  my $buffer = $_[0];
  my $models_dir = "$prontus_varglb::DIR_SERVER/wizard_prontus/models";
  my @lisdir = &glib_fildir_02::lee_dir($models_dir);
  @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
  my $k;
  my $nro_models;
  my ($loop_tpl, $loop_out, $loop_item);
  if ($buffer =~ /<!--LOOP_MODELS-->(.*?)<!--\/LOOP_MODELS-->/is) {
    $loop_tpl = $1;
  }
  else {
    return 'Error en plantilla wizard. No es posible continuar.';
  };
  foreach $k (@lisdir) {
    # localiza cfg descriptor del modelo,
    # si lo encuentra asume q se trata de un modelo.
    print STDERR "K[$k]\n";
    if (-f "$models_dir/$k/$k.cfg") {
      # valida icono
      if (! -f "$models_dir/$k/$k.gif") {
        return "En Modelo [$k] falta icono $k/$k.gif";
      };

      # valida q este el arch de obs del modelo
      if (! -f "$models_dir/$k/descripcion/index.html") {
        return "En Modelo [$k] falta $k/descripcion/index.html";
      };
      $nro_models++;
      $loop_item = $loop_tpl;
      $loop_item =~ s/%%MODEL_NOM%%/$k/isg;
      # Deja el primero como seleccionado por defecto
      if ($nro_models == 1) {
        $loop_item =~ s/%%checked%%/checked/isg;
      }
      else {
        $loop_item =~ s/%%checked%%//isg;
      };
      $loop_out .= $loop_item;
    };
  };

  # Debe haber por lo menos 1 modelo.
  if (! $nro_models) {
    return "No hay Modelos Prontus disponibles.<br>No es posible continuar.";
  }
  else {
    $buffer =~ s/<!--LOOP_MODELS-->.*?<!--\/LOOP_MODELS-->/$loop_out/is;
    return ('', $buffer);
  };

};

# -------------------------------END SCRIPT----------------------

