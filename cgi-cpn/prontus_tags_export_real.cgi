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
# Exportar tags de Prontus, hacia un arch. XML.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# No registra.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Via system desde prontus_tags_export.cgi
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# No utiliza.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# ART (BD prontus)
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 12/2004 - YCH - Primera version.
# ---------------------------------------------------------------

# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use DBI;

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use glib_dbi_02;
use glib_fildir_02;
use glib_cgi_04;
use lib_lock;
use glib_hrfec_02;
use lib_logproc;

use strict;

my ($LOG_FILE, $PATH_CONF);

# sqlite no requiere esto.
my $NOM_BD_PRONTUS = '';
my $USER_BD = '';
my $PWD_BD = '';
my $SERVER_BD = ''; # asumiendo que los scripts estan instalados en el server Mysql

# ------------------------------------------------------------------------------
# MAIN.
# -------------

my ($BD, $LOCK_FILE);
my ($TOT_REGS, $OK_REGS) = (0, 0);
my %FORM;
my $MODO_WEB = 0;
main:{

  # &libprontus::setUtf8();
  if ($ARGV[0] && $ARGV[1]) {
    close STDOUT;
    $prontus_varglb::DIR_SERVER = $ARGV[0];
    $PATH_CONF = $ARGV[1];
    print STDERR "DIR_SERVER: [$prontus_varglb::DIR_SERVER]\n";
    print STDERR "PATH_CONF: [$PATH_CONF]\n";

  } else {
    &glib_cgi_04::new(); # Rescata parametros
    $FORM{'path_conf'} = &glib_cgi_04::param('path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});
    $PATH_CONF = $FORM{'path_conf'};
    $MODO_WEB = 1;
    print "Content-Type: text/html\n\n";
    $| = 1;
  };

  if (! -d $prontus_varglb::DIR_SERVER) {
    print STDERR "ERROR: DIR_SERVER no válido[$prontus_varglb::DIR_SERVER]\n";
    exit;
  };

  &lib_prontus::load_config($PATH_CONF);

  # Para el manejo del log de procesamiento
  $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/prontus_tags_export_log.html";
  $lib_logproc::MODO_WEB = $MODO_WEB;

  # Bloqueo
  $LOCK_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/semaforo_tags_export";

  # Detecta semaforo.
  my ($lock_obj) = &lib_lock::lock_file($LOCK_FILE);
  if (!ref $lock_obj) { # si ya tiene un bloqueo anterior, aborta.
    &finishLoading("Proceso en ejecución. Por favor espere hasta que la importación anterior termine.");
    &lib_logproc::handle_error("Proceso en ejecución. Por favor espere hasta que la importación anterior termine.");
  };

  # Mysql
  my ($msg_err_bd);
  ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
  if (! ref($BD)) {
      &finishLoading("ERROR: $msg_err_bd");
      &lib_logproc::handle_error("ERROR: $msg_err_bd");
  };

  # Se realiza el proceso y se escribe al Log
  &lib_logproc::flush_log();
  &lib_logproc::writeRule();
  &lib_logproc::add_to_log_count("INICIANDO PROCESO DE EXPORTACION");
  my $registros = &tags_export();
  &lib_logproc::add_to_log_count("PROCESO DE EXPORTACION FINALIZADO");
  &lib_logproc::writeRule();

  &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/prontus_tags_export.xml", $registros);
  sleep 1;
  &lib_logproc::add_to_log("Nro. de registros exportados: $TOT_REGS\nPara bajar el archivo haga click <a href=\"$prontus_varglb::DIR_CPAN/procs/prontus_tags_export.xml\">aqu&iacute;</a>");
  &lib_logproc::add_to_log_finish("Operaci&oacute;n finalizada.");

  $BD->disconnect;

  # Elimina el bloqueo y termina ejecucion.
  &lib_lock::unlock_file($lock_obj, $LOCK_FILE);

  # Se termina + el link para descargar
  &finishLoading('');

}; # main

# ------------------------------------------------------------------------------
# SUB-RUTINAS.
# ------------------------------------------------------------------------------
# rotulos tags
sub tags_export {
    my ($sql);
    my ($salida);
    my ($id, $nom, $count, $mostrar, $nom4vistas);
    my ($nom_envistas);
    my ($registros) = "<?xml version='1.0' encoding='utf-8'?>\n<tagsdata>\n";

    &lib_logproc::add_to_log_count("Preparando datos a exportar.");


    $sql = "select TAGS_ID, TAGS_TAG, TAGS_COUNT, TAGS_MOSTRAR, TAGS_NOM4VISTAS from TAGS order by TAGS_ID ASC";
    $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id, $nom, $count, $mostrar, $nom4vistas));

    &lib_logproc::add_to_log_count("Exportaci&oacute;n iniciada");
    &lib_logproc::writeRule();
    while ($salida->fetch) {
        # secciones
        $nom = &lib_prontus::escape_xml($nom);
        if ($mostrar) { $mostrar = 'SI'; } else { $mostrar = 'NO'; };
        $nom_envistas = &get_nom_envistas($nom4vistas);
        $registros .= "<tag id='$id'>\n"
        . "  <nom>$nom</nom>\n"
        . $nom_envistas
        . "  <count>$count</count>\n"
        . "  <mostrar>$mostrar</mostrar>\n"
        . "</tag>\n";
        $TOT_REGS++;
        &lib_logproc::add_to_log_count("Nro. de registros exportados: $TOT_REGS.");
    };
    $salida->finish;
    $registros .= "</tagsdata>";

    return ($registros);


};

# ------------------------------------------------------------------------------
sub get_nom_envistas {
    my ($nom4vistas) = shift;
    my $nombres;
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        my $nom = &lib_prontus::get_nomtax_envista($mv, $nom4vistas);
        $nom = &lib_prontus::escape_xml($nom);
        $nombres .= "  <nom-$mv>" . $nom . "</nom-$mv>\n";
    };
    return $nombres;
};

# ------------------------------------------------------------------------------
sub finishLoading {
    my $msg = $_[0];
    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_tags_export.js";
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", '{"status":1, "msg":"'.$msg.'"}');
};
