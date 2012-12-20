#!/usr/bin/perl


# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Exportar secciones, temas y subtemas a Prontus, hacia un arch. de texto.

# El formato del archivo es el sgte:

# Archivo txt con seis columnas separadas por tabuladores:
# Columna 0: Id de sección.
# Columna 1: Nombre de sección.
# Columna 2: Id de tema.
# Columna 3: Nombre de tema.
# Columna 4: Id de subtema.
# Columna 5: Nombre de subtema.
# Columna 6: Mostrar
# Columna 7: Portada
# Columna 8: Orden en mapa
# Al exportar, se exporta con 'no' o 'si'.

# En cada línea va un solo dato. No se mezclan secciones, temas y subtemas.

# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# No registra.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Via system desde prontus_tax_export.cgi
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
  # Captura STDERR
  use lib_stdlog;
  &lib_stdlog::set_stdlog($0, 51200);
};

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
my ($TOT_REGS, $OK_REGS) = '0';
my (%FORM);
my ($MODO_WEB) = 0;
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
  $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/prontus_tax_export_log.html";
  $lib_logproc::MODO_WEB = $MODO_WEB;

  # Bloqueo
  $LOCK_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/semaforo_tax_export";

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
  my $registros = &tax_export();
  &lib_logproc::add_to_log_count("PROCESO DE EXPORTACION FINALIZADO");
  &lib_logproc::writeRule();

  $TOT_REGS = '0' if ($TOT_REGS eq '');
  # &add_to_log("ready4save"); # debug
  &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/prontus_tax_export.xml", $registros);
  # &add_to_log("saved"); # debug
  sleep 1;
  &lib_logproc::add_to_log("Nro. de registros exportados: $TOT_REGS\nPara bajar el archivo haga click <a href=\"$prontus_varglb::DIR_CPAN/procs/prontus_tax_export.xml\">aqu&iacute;</a>");
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
# rotulos tax
sub tax_export {
    my ($sql);
    my ($salida_s, $salida_t, $salida_st);
    my ($id_s, $id_t, $id_st);
    my ($nom_s, $nom_t, $nom_st, $mostrar, $port, $orden, $nom4vistas);
    my ($nom_envistas);
    my ($registros) = "<?xml version='1.0' encoding='utf-8'?>\n<taxdata>\n";

    &lib_logproc::add_to_log_count("Preparando datos a exportar.");


    $sql = "select SECC_ID, SECC_NOM, SECC_MOSTRAR, SECC_PORT, SECC_ORDEN, SECC_NOM4VISTAS from SECC order by SECC_ORDEN ASC, SECC_ID ASC";

    $salida_s = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id_s, $nom_s, $mostrar, $port, $orden, $nom4vistas));

    &lib_logproc::add_to_log_count("Exportaci&oacute;n iniciada");
    &lib_logproc::writeRule();
    while ($salida_s->fetch) {
        # secciones
        $nom_s = &lib_prontus::escape_xml($nom_s);
        if ($mostrar) { $mostrar = 'SI'; } else { $mostrar = 'NO'; };
        $nom_envistas = &get_nom_envistas($nom4vistas);
        $registros .= "<seccion id='$id_s'>\n"
        . "<nom>$nom_s</nom>\n"
        . $nom_envistas
        . "<mostrar>$mostrar</mostrar>\n"
        . "<port>$port</port>\n"
        . "<posmapa>$orden</posmapa>\n";

        $TOT_REGS++;
        &lib_logproc::add_to_log_count("Nro. de registros exportados: $TOT_REGS.");

        # temas
        $sql = "select TEMAS_ID, TEMAS_NOM, TEMAS_MOSTRAR, TEMAS_PORT, TEMAS_ORDEN, TEMAS_NOM4VISTAS from TEMAS WHERE TEMAS_IDSECC = $id_s order by TEMAS_NOM ASC, TEMAS_ID ASC";
        $salida_t = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id_t, $nom_t, $mostrar, $port, $orden, $nom4vistas));

        while ($salida_t->fetch) {
            if ($mostrar) { $mostrar = 'SI'; } else { $mostrar = 'NO'; };
            $nom_t = &lib_prontus::escape_xml($nom_t);
            $nom_envistas = &get_nom_envistas($nom4vistas);
            $registros .= "<tema id='$id_t'>\n"
            . "<nom>$nom_t</nom>\n"
            . $nom_envistas
            . "<mostrar>$mostrar</mostrar>\n"
            . "<port>$port</port>\n"
            . "<posmapa>$orden</posmapa>\n";

            $TOT_REGS++;
            &lib_logproc::add_to_log_count("Nro. de registros exportados: $TOT_REGS.");

            # subtemas
            $sql = "select SUBTEMAS_ID, SUBTEMAS_NOM, SUBTEMAS_MOSTRAR, SUBTEMAS_PORT, SUBTEMAS_ORDEN, SUBTEMAS_NOM4VISTAS from SUBTEMAS WHERE SUBTEMAS_IDTEMAS = $id_t order by SUBTEMAS_NOM ASC, SUBTEMAS_ID ASC";
            $salida_st = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id_st, $nom_st, $mostrar, $port, $orden, $nom4vistas));

            while ($salida_st->fetch) {
                if ($mostrar) { $mostrar = 'SI'; } else { $mostrar = 'NO'; };
                $nom_st = &lib_prontus::escape_xml($nom_st);
                $nom_envistas = &get_nom_envistas($nom4vistas);
                $registros .= "<subtema id='$id_st'>\n"
                . "<nom>$nom_st</nom>\n"
                . $nom_envistas
                . "<mostrar>$mostrar</mostrar>\n"
                . "<port>$port</port>\n"
                . "<posmapa>$orden</posmapa>\n"
                . "</subtema>\n";

                $TOT_REGS++;
                &lib_logproc::add_to_log_count("Nro. de registros exportados: $TOT_REGS.");
            };
            $salida_st->finish;
            $registros .= "</tema>\n";

        };
        $salida_t->finish;
        $registros .= "</seccion>\n";

    };
    $salida_s->finish;
    $registros .= "</taxdata>";

    return ($registros);


};

# ------------------------------------------------------------------------------
sub get_nom_envistas {
    my ($nom4vistas) = shift;
    my $nombres;
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        my $nom = &lib_prontus::get_nomtax_envista($mv, $nom4vistas);
        $nom = &lib_prontus::escape_xml($nom);
        $nombres .= "<nom-$mv>" . $nom . "</nom-$mv>\n";
    };
    return $nombres;
};

# ------------------------------------------------------------------------------
sub finishLoading {

    my $msg = $_[0];
    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_tax_export.js";
    my $msg = '{"status":1, "msg":"'.$msg.'"}';
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
};

# -------------------------END SCRIPT----------------------