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
# PROPOSITO.
# -----------
# Muestra pagina de confirmacion de los pasos anteriores.
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------
# No registra, imprime directamente al browser.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Via location desde wizard_paso6.cgi sin parametros.
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------------
# - Informacion de paso anterior para verificacion:
# /wizard_prontus/data/inf.txt

# - Plantilla: /wizard_prontus/core/confirm.html

# - Cada modelo es descrito por un cfg:
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
# 1.0 - 12/2005 - YCH - Primera Version.
# p10.11 - 04/02/2008 - CVI - Correciones al wizard. Manejo de extensión via cfg del modelo.

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
my ($INF_DIR) = "$prontus_varglb::DIR_SERVER/wizard_prontus/_data";
my ($INF_FILE) = "$INF_DIR/inf.txt";


main:{

  # Valida informacion de paso anter.
  my ($msg_err,
        $prontus_id,
        $extension,
        $smtp,
        $model_nom,
        $new_title_site_name,
        $server_bd,
        $nom_bd,
        $user_bd,
        $pwd_bd,
        $superuser_bd,
        $superpwd_bd) = &check_paso_anterior();

  if ($msg_err) {

    $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
    &glib_html_02::print_pag_result('Error', $msg_err, 0, "exit=1, ctype=1");

  };

  my $buffer = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER/wizard_prontus/core/confirm.html");

  $buffer =~ s/%%PRONTUS_ID%%/$prontus_id/ig;
  $smtp = 'No especificado' if (!$smtp);
  $buffer =~ s/%%SERVER_SMTP%%/$smtp/ig;
  $buffer =~ s/%%PRONTUS_EXTENSION%%/$extension/ig;
  $buffer =~ s/%%MODEL_NOM%%/$model_nom/ig;
  $buffer =~ s/%%NEW_TITLE_SITE_NAME%%/$new_title_site_name/ig;

  $buffer =~ s/%%server_bd%%/$server_bd/ig;
  $buffer =~ s/%%nom_bd%%/$nom_bd/ig;
  $buffer =~ s/%%user_bd%%/$user_bd/ig;
  $buffer =~ s/%%pwd_bd%%/$pwd_bd/ig;
  $buffer =~ s/%%superuser_bd%%/$superuser_bd/ig;
  $buffer =~ s/%%superpwd_bd%%/$superpwd_bd/ig;


  print "Content-Type: text/html\n\n";
  print $buffer;


};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub check_paso_anterior {
# Chequea que se haya pasado por el paso 1

  if (! -f $INF_FILE) {
    return "[errInfFile] Solicitud de ejecución no válida.";
  };

  # Leer y cargar y validar contenido del INF.
  my $buffer = &glib_fildir_02::read_file($INF_FILE);
  my ($prontus_id, $extension, $smtp);

 my ($server_bd, $nom_bd, $user_bd,$pwd_bd,$superuser_bd,$superpwd_bd);


  my $new_title_site_name;
  if ($buffer =~ /(\[PRONTUS\].*\[\/PRONTUS\]\n\n)/s) {
    my $buffer_prontus = $1;
    # Validar id
    if ($buffer_prontus !~ /PRONTUS_ID=(\w+)\n/) {
      return 'Información de paso 1 está corrupta.';
    }
    else {
      $prontus_id = $1;
    };


    # smtp
    if ($buffer_prontus =~ /SERVER_SMTP=([\w\.\-]+)\n/) {
      $smtp = $1;
    };

    if ($buffer_prontus !~ /NEW_TITLE_SITE_NAME=(.+?)\n/) {
      return 'Información de paso 1 está corrupta.';
    }
    else {
      $new_title_site_name = $1;
    };


    $server_bd = $1 if ($buffer_prontus =~ /server_bd=(.*?)\n/i);
    $nom_bd = $1 if ($buffer_prontus =~ /nom_bd=(.*?)\n/i);
    $user_bd = $1 if ($buffer_prontus =~ /user_bd=(.*?)\n/i);
    $pwd_bd = $1 if ($buffer_prontus =~ /pwd_bd=(.*?)\n/i);
    $superuser_bd = $1 if ($buffer_prontus =~ /superuser_bd=(.*?)\n/i);
    $superpwd_bd = $1 if ($buffer_prontus =~ /superpwd_bd=(.*?)\n/i);


  }
  else {
    return 'Información de paso 1 está corrupta';
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

  # valida q se haya pasado por paso2
  my $model_nom;
  if ($buffer =~ /(\[MODEL\].*\[\/MODEL\]\n\n)/s) {
    my $buffer_model = $1;

    # CVI - Para definir la extensión en el CFG del modelo
    if ($buffer_model !~ /MODEL_EXT=(\w+)\n/) {
      return 'Información de paso 1 está corrupta.';
    }
    else {
      $extension = $1;
    };


    # Validar id
    if ($buffer_model !~ /MODEL_NOM=(\w+)\n/) {
      return 'Información de paso 2 está corrupta.';
    }
    else {
      $model_nom = $1;
    };
  }
  else {
    return 'Información de paso 2 está corrupta';
  };

  return ('', $prontus_id, $extension, $smtp, $model_nom, $new_title_site_name, $server_bd, $nom_bd, $user_bd,$pwd_bd,$superuser_bd,$superpwd_bd);

};
# -------------------------------END SCRIPT----------------------

