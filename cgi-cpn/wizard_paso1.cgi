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
# Procesar paso 1 del wizard : Configuracion del Publicador,
# grabando la info. en la seccion [PRONTUS]...[/PRONTUS] de /wizard_prontus/data/inf.txt
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Al termino del script se invoca via location a wizard_show_paso2.cgi sin parametros.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Via submit desde /wizard_prontus/core/paso1.html
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# No utiliza.
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
# p10.11 - 04/02/2008 - CVI - Correciones al wizard. Manejo de extensi�n via cfg del modelo.
# ---------------------------------------------------------------


# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200, 'wizard_error_log');

use glib_cgi_04;
use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use strict;
use lib_prontus;

# ---------------------------------------------------------------
# MAIN.
# ------

my (%FORM, %PRONTUS);
my ($INF_DIR) = "$prontus_varglb::DIR_SERVER/wizard_prontus/_data";
my ($INF_FILE) = "$INF_DIR/inf.txt";

main:{

  &glib_cgi_04::new();

  $FORM{'PRONTUS_ID'} = &glib_cgi_04::param('PRONTUS_ID');
  $FORM{'SERVER_BD'} = &glib_cgi_04::param('SERVER_BD');
  $FORM{'NOM_BD'} = &glib_cgi_04::param('NOM_BD');
  $FORM{'USER_BD'} = &glib_cgi_04::param('USER_BD');
  $FORM{'PWD_BD'} = &glib_cgi_04::param('PWD_BD');
  $FORM{'SUPERUSER_BD'} = &glib_cgi_04::param('SUPERUSER_BD');
  $FORM{'SUPERPWD_BD'} = &glib_cgi_04::param('SUPERPWD_BD');
  $FORM{'PRONTUS_SMTP'} = &glib_cgi_04::param('PRONTUS_SMTP');
  $FORM{'NEW_TITLE_SITE_NAME'} = &glib_cgi_04::param('NEW_TITLE_SITE_NAME');

  $FORM{'Sbm_ACCION'} = &glib_cgi_04::param('Sbm_ACCION');

  my $msg_err = &validar_datos();
  if ($msg_err) {
    $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
    &glib_html_02::print_pag_result('Error', $msg_err, 0, "exit=1, ctype=1");
  };

  &grabar_datos();

  print "Location: wizard_show_paso2.cgi\n\n";
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub grabar_datos {
# Graba la info del paso 1 en el arch. de texto /wizard_prontus/data/inf.txt, seccion [PRONTUS]...[/PRONTUS]
# creando el dir. inf si no existe.

my ($buffer);


  my $key_custom = uc "$FORM{'PRONTUS_KEY1'}-$FORM{'PRONTUS_KEY2'}-$FORM{'PRONTUS_KEY3'}-$FORM{'PRONTUS_KEY4'}";
  my $key_localhost_name = 'PPXN-3CWA-STK5-W964';
  my $key_localhost_ip = '3SPD-DX2A-EV55-ZTXG';

  $buffer = "[PRONTUS]\n"
          . "PRONTUS_ID=$FORM{'PRONTUS_ID'}\n"

          . "SERVER_BD=$FORM{'SERVER_BD'}\n"
          . "NOM_BD=$FORM{'NOM_BD'}\n"
          . "USER_BD=$FORM{'USER_BD'}\n"
          . "PWD_BD=$FORM{'PWD_BD'}\n"
          . "PRONTUS_ID=$FORM{'PRONTUS_ID'}\n"

          . "NEW_TITLE_SITE_NAME=$FORM{'NEW_TITLE_SITE_NAME'}\n";


  $buffer .= "SERVER_SMTP=$FORM{'PRONTUS_SMTP'}\n" if ($FORM{'PRONTUS_SMTP'});

  if (($FORM{'SUPERUSER_BD'} ne '') && ($FORM{'SUPERPWD_BD'} ne '')) {
    $buffer .= "SUPERUSER_BD=$FORM{'SUPERUSER_BD'}\n";
    $buffer .= "SUPERPWD_BD=$FORM{'SUPERPWD_BD'}\n";
  };

  $buffer .= "[/PRONTUS]\n\n";

  if ( ! (&glib_fildir_02::check_dir($INF_DIR)) ) {

    $prontus_varglb::DIR_CORE = '/wizard_prontus/core'; # solo para efectos de la plantilla de mensaje
    &glib_html_02::print_pag_result('Error', 'No se pudo crear directorio [INF_DIR]', 0, "exit=1, ctype=1");


  };


  &glib_fildir_02::write_file($INF_FILE, $buffer);

};
# ---------------------------------------------------------------
sub validar_datos {
# Valida datos provenientes del formulario paso1.
# Retorna msg de error si lo hay o nada si todo ok.

  if (! &lib_prontus::valida_prontus($FORM{'PRONTUS_ID'})) {
    return 'Nombre de publicador no v�lido.';
  };

  my $dir_prontus = "$prontus_varglb::DIR_SERVER/$FORM{'PRONTUS_ID'}";

  if (-d $dir_prontus) {
    return "El directorio prontus ya existe. Para continuar con el proceso de instalaci�n Ud. debe cambiar el nombre especificado para el publicador, o bien, <br>eliminar manualmente el directorio existente que genera el conflicto.";
  }
  else {
    # Lo creo y luego lo borro para verificar que este ok.
    if (&glib_fildir_02::check_dir($dir_prontus)) {
      &glib_fildir_02::borra_dir($dir_prontus);
    }
    else {
      return "No se puede crear el directorio destino del publicador. No es posible continuar con la instalaci�n.";
    };
  };


  if ($FORM{'SERVER_BD'} !~ /^[\w\-\.]{1,128}$/) {
    return 'Servidor de BD no v�lido.';
  };

  if ($FORM{'NOM_BD'} !~ /^[\w\-]{1,64}$/) {
    return 'Nombre de BD no v�lido.';
  };

  if ($FORM{'USER_BD'} !~ /^[\w\-]{1,16}$/) {
    return 'User de BD no v�lido.';
  };

  if ($FORM{'PWD_BD'} !~ /^[\w\-\.\@\:\$%!]{1,64}$/) {
    return 'Password de BD no v�lido.';
  };

  if ($FORM{'SUPERUSER_BD'} !~ /^[\w\-]{1,16}$/) {
    return 'User para creaci�n de BD no v�lido.';
  };

  if ($FORM{'SUPERPWD_BD'} !~ /^[\w\-\.\@\:\$%!]{1,64}$/) {
    return 'Password para creaci�n de BD no v�lido.';
  };


  if ($FORM{'PRONTUS_SMTP'} ne '') {
    if ($FORM{'PRONTUS_SMTP'} !~ /^[A-Z\.a-z\_\-0-9]+$/) {
      return "SMTP no v�lido.";
    };
  };

  if ($FORM{'NEW_TITLE_SITE_NAME'} eq '') {
    return "Debe ingresar nombre del sitio para ser inclu�do en etiquetas 'title' de las p�ginas.";
  };

  if ($FORM{'Sbm_ACCION'} !~ /siguiente/i) {
    return "Solicitud de ejecuci�n no v�lida.";
  };

  return '';
};

# -------------------------------END SCRIPT----------------------

