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
# Regenerar BD de articulos prontus a partir de los archivos html correspondientes a éstos.

# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# No registra.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Directamente de la linea de comandos
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
# 1.0 - 09/2004 - YCH - Primera version.
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
use lib_setbd;
use lib_logproc;

use glib_dbi_02;
use glib_cgi_04;
use glib_fildir_02;

use glib_hrfec_02;


use strict;



my ($LOG_FILE, $PATH_CONF);

# sqlite no requiere esto.
my $NOM_BD_PRONTUS = '';
my $USER_BD = '';
my $PWD_BD = '';
my $SERVER_BD = ''; # asumiendo que los scripts estan instalados en el server Mysql


# ---------------------------------------------------------------
# MAIN.
# -------------


my ($NOMTABLE) = 'ART';

my ($TOT_REGS, $OK_REGS) = '0';
my (%FORM);
my ($MODO_WEB) = 0;
my ($DIRFECHA_INI); # DIR FECHA A PARTIR DEL CUAL EL SCRIPT DEBE PROCESAR
main:{

    if ($ARGV[0]) {
        close STDOUT;
        $PATH_CONF = $ARGV[0];
        $DIRFECHA_INI = $ARGV[1] if ($ARGV[1] =~ /^[0-9]{8}$/);
    }
    else {
        &glib_cgi_04::new(); # Rescata parametros
        $FORM{'path_conf'} = &glib_cgi_04::param('path_conf');

        # Ajusta path_conf para completar path y/o cambiar \ por /
        $PATH_CONF = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});
        $MODO_WEB = 1;
        print "Content-Type: text/html\n\n";
        $| = 1;
    };

    &lib_prontus::load_config($PATH_CONF);

    # Establece log file
    $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/prontus_art_regenbd_log.html";
    $lib_logproc::MODO_WEB = $MODO_WEB;

    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        &finishLoading("ERROR: $msg_err_bd");
        &lib_logproc::handle_error("ERROR: $msg_err_bd");
    };

    # Borra cache de lista de articulos
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");


    &lib_logproc::flush_log();
    &lib_logproc::writeRule();
    &lib_logproc::add_to_log_count("INICIANDO PROCESO DE REGENERACION DE BD");

    # Antes de regenerar, borrar toda la tabla.
    my ($sql, $ret);
    if ($DIRFECHA_INI eq '' ) {
        # ART
        $sql = 'drop table ART';
        $ret = $base->do($sql);
    } else {
        $ret = 1;
    };

    if ($ret) {
        if ($DIRFECHA_INI eq '' ) {
            if ($prontus_varglb::MOTOR_BD eq 'PRONTUS') {
                # Liberar espacio
                $sql = 'VACUUM';
                $base->do($sql);
            };
            &lib_logproc::add_to_log("- Tabla De Articulos Eliminada");

            # Re-crear estructura de la tabla ART
            my ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_art($base, $prontus_varglb::MOTOR_BD);
            &lib_logproc::add_to_log($msg_ret);
            if ($hay_err) {
                &finishLoading("Error creando la estructura de la tabla de artículos, proceso abortado.");
                &lib_logproc::handle_error("Error creando la estructura de la tabla de artículos, proceso abortado.");
            };

            if ($prontus_varglb::FRIENDLY_URLS eq 'SI' && $prontus_varglb::FRIENDLY_URLS_VERSION eq '4') {
                # URL
                $sql = 'drop table URL';
                $ret = $base->do($sql);

                if ($ret) {
                    # Re-crear estructura de la tabla URL
                    my ($msg_ret, $hay_err) = &lib_setbd::crear_tabla_url($base, $prontus_varglb::MOTOR_BD);
                    &lib_logproc::add_to_log($msg_ret);
                    if ($hay_err) {
                        &finishLoading("Error creando la estructura de la tabla de urls, proceso abortado.");
                        &lib_logproc::handle_error("Error creando la estructura de la tabla de urls, proceso abortado.");
                    }
                }
            }
        };

        # Repoblarla
        &lib_logproc::add_to_log("- Repoblando la tabla");
        &lib_logproc::writeRule();

        &regenera_base($base);

        &lib_logproc::writeRule();
        $TOT_REGS = '0' if ($TOT_REGS eq '');
        $OK_REGS = '0' if ($OK_REGS eq '');
        &lib_logproc::add_to_log_count("PROCESO FINALIZADO");
        &lib_logproc::writeRule();
        &lib_logproc::add_to_log("Total Archivos Procesados: $TOT_REGS\nIngresados OK: $OK_REGS");
        &lib_logproc::add_to_log_finish("Operación finalizada");

    } else {
        &finishLoading('Error: No se pudo borrar la tabla de articulos por completo. Proceso abortado.');
        &lib_logproc::handle_error('Error: No se pudo borrar la tabla de articulos por completo. Proceso abortado.');
    };

    &finishLoading('');
    $base->disconnect;

    # Borra cache de lista de articulos
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");


}; # main

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

sub regenera_base {
    # Recorre todos los articulos via file system y repobla la BD.
    my $base = $_[0];
    my ($ruta_dir) = $prontus_varglb::DIR_SERVER
                   . $prontus_varglb::DIR_CONTENIDO
                   . $prontus_varglb::DIR_ARTIC;

    my @lisdir = &glib_fildir_02::lee_dir($ruta_dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    @lisdir = grep !/edic/, @lisdir; # Elimina directorios edic

    @lisdir = sort {$a <=> $b} (@lisdir);

    # Para cada dirfecha
    foreach my $dirfecha (@lisdir) {
        if ($DIRFECHA_INI ne '' ) {
            next if ($dirfecha < $DIRFECHA_INI);
        };
        print STDERR "Procesando artics de [$dirfecha/xml]\n";
        if (-d "$ruta_dir/$dirfecha") {
            &lib_logproc::add_to_log_count("Procesando artics de [$dirfecha/xml]");
            &procesa_files("$ruta_dir/$dirfecha/xml", $base);
        };
        # while (<STDIN> !~ /\n/) {}; # debug
    };
};

# ---------------------------------------------------------------
sub procesa_files {
    # Lee todos los articulos del directorio y agrega la info a la bd.
    my ($ruta_dir_xml) = $_[0];
    my ($base) = $_[1];

    # CVI - Se agrega validación por si el directorio no existe
    return unless(-d $ruta_dir_xml);
    my @lisfile = &glib_fildir_02::lee_dir($ruta_dir_xml);
    @lisfile = grep !/^\./, @lisfile; # Elimina directorios . y ..

    foreach my $k_xml (@lisfile) {
        if ((-s "$ruta_dir_xml/$k_xml") && ($k_xml =~ /^(\d{14})\.(xml)$/) && (! -d "$ruta_dir_xml/$k_xml")) {
            my $ts = $1;

            my $artic_obj = Artic->new(
                            'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                            'public_server_name'=> $prontus_varglb::PUBLIC_SERVER_NAME,
                            'cpan_server_name'  => $prontus_varglb::IP_SERVER,
                            'document_root'     => $prontus_varglb::DIR_SERVER,
                            'ts'                => $ts,
                            'campos'=>{}) || &registra_artic_error("Error inicializando objeto articulo: $Artic::ERR TS[$ts]");

            next if (!ref($artic_obj));

            my $regenerar_registro = 1;
            my $ret = $artic_obj->art_insert_bd($base, $regenerar_registro);
            if ($ret) {
                $artic_obj->tags2bd($base, 0) || return $Artic::ERR;

                if ($prontus_varglb::FRIENDLY_URLS eq 'SI' && $prontus_varglb::FRIENDLY_URLS_VERSION eq '4') {
                    $artic_obj->friendly_v4_2bd($base, 0) || return $Artic::ERR;
                }
                $OK_REGS++;  # Total de reg. insertados normalmente
            }
            else {
                &lib_logproc::add_to_log("\t\t\tError: $Artic::ERR");
            };

            $TOT_REGS++;  # Total de archivos procesados.
        };
    };
};

# ---------------------------------------------------------------
sub registra_artic_error {
    my $msg = $_[0];
    &lib_logproc::add_to_log($msg);
};

# ---------------------------------------------------------------
sub finishLoading {

    my $msg = $_[0];
    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_bd_regen.js";
    $msg = '{"status":1, "msg":"'.$msg.'"}';
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
};

# -------------------------END SCRIPT----------------------
