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
# Via system desde prontus_update.cgi
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
use Update;
use lib_mail;
use lib_loading;
use lib_quota;

use strict;

my ($LOG_FILE, $PATH_CONF);

# sqlite no requiere esto.
my $NOM_BD_PRONTUS = '';
my $USER_BD = '';
my $PWD_BD = '';
my $SERVER_BD = ''; # asumiendo que los scripts estan instalados en el server Mysql

my $EMAIL_SOPORTE_PRONTUS = 'area_prontus@altavoz.net';

# ------------------------------------------------------------------------------
# MAIN.
# -------------

my ($BD, $LOCK_FILE);
my ($TOT_REGS, $OK_REGS) = '0';
my (%FORM);
my ($MODO_WEB) = 0;

main:{

    close STDOUT;
    $prontus_varglb::DIR_SERVER = $ARGV[0];
    $PATH_CONF = $ARGV[1];
    print STDERR "DIR_SERVER: [$prontus_varglb::DIR_SERVER]\n";
    print STDERR "PATH_CONF: [$PATH_CONF]\n";
    
    if (! -d $prontus_varglb::DIR_SERVER) {
        print STDERR "ERROR: DIR_SERVER no válido[$prontus_varglb::DIR_SERVER]\n";
        exit;
    };

    &lib_prontus::load_config($PATH_CONF);

    if ($prontus_varglb::ACTUALIZACIONES ne 'SI') {
        &lib_logproc::add_to_log_finish(&lib_language::_msg_prontus('_error_automatic_updates_disabled_product_configuration'), 1);
    };

    # Para el manejo del log de procesamiento
    $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/prontus_update_log.html";
    $lib_logproc::MODO_WEB = $MODO_WEB;

    # Bloqueo
    $LOCK_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/semaforo_prontus_update";

    # Detecta semaforo.
    my ($lock_obj) = &lib_lock::lock_file($LOCK_FILE);
    if (!ref $lock_obj) { # si ya tiene un bloqueo anterior, aborta.
        &lib_loading::finish_loading(0, &lib_language::_msg_prontus('_running_process_wait_previous_import'));
        &lib_logproc::add_to_log_finish(&lib_language::_msg_prontus('_running_process_wait_previous_import'), 1);
    };
    
    my $ret = &lib_loading::init('result_prontus_update.js');
    unless($ret) {
        &lib_loading::finish_loading(0, &lib_language::_msg_prontus('_unable_write_response_file'));
        &lib_logproc::add_to_log_finish(&lib_language::_msg_prontus('_unable_write_response_file'), 1);
    }    

    # Se realiza el proceso y se escribe al Log
    &lib_logproc::flush_log();
    &lib_logproc::writeRule();
    &lib_logproc::add_to_log_count(&lib_language::_msg_prontus('_starting_update_process'));
    my $error_msg = &actualizar_prontus($PATH_CONF);
    my ($respuesta, $mensaje);
    if ($error_msg eq '') {
        $respuesta = 1;
        $mensaje = &lib_language::_msg_prontus(&lib_language::_msg_prontus('_update_completed_ok'));
    } else {
        $respuesta = 0;
        $mensaje = "<b>".&lib_language::_msg_prontus('_update_completed_errors').":</b><br/>$error_msg";
        &enviar_mail_error($EMAIL_SOPORTE_PRONTUS, $mensaje);
    };
    
    # Borra cache de no publicados
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");

    # Elimina el bloqueo y termina ejecucion.
    &lib_lock::unlock_file($lock_obj, $LOCK_FILE);
    
    &lib_logproc::add_to_log_count($mensaje);
    &lib_logproc::writeRule();
    
    &lib_loading::finish_loading($respuesta, $mensaje);

}; # main

# ------------------------------------------------------------------------------
# SUB-RUTINAS.
# ------------------------------------------------------------------------------
sub enviar_mail_error {
    my ($email, $texto) = @_;
    my ($from) = 'prontus@altavoz.net';
    my ($replyto_name) = 'Prontus CMS';
    my ($replyto_email) =  'prontus@altavoz.net';
    my $server = $prontus_varglb::IP_SERVER;
    my $dir_server_ofusc = $prontus_varglb::DIR_SERVER;
    $dir_server_ofusc =~ s/\//-/g;
    $dir_server_ofusc =~ s/^[- ]+//g;
    $server .= " ($dir_server_ofusc)" if ($server =~ /^[0-9]+\.[0-9]+\./);
    my ($asunto) = "[prontus-update] ".&lib_language::_msg_prontus('_error_updating')." $server - prontus_id: $prontus_varglb::PRONTUS_ID";

    my $buffer_completo_log = &glib_fildir_02::read_file($lib_logproc::LOG_FILE);

    # Codifica en UTF8
    utf8::encode($texto);

    $texto .= "\n\nUser Log:\n\n$buffer_completo_log";

    use FindBin '$Bin';
    my $buffer_error_log = &glib_fildir_02::read_file("$Bin/prontus_error_log/prontus_update_real.cgi.error.log");
    $texto .= "\n\nProntus error Log:\n\n$buffer_error_log";

    my ($htmldoc) = '';
    my ($attach) = '';
    my ($url) = '';
    my ($dir_attach) = '';
    my ($smtp) = $prontus_varglb::SERVER_SMTP;

    &lib_mail::enviar_mail($email, $from, $replyto_name, $replyto_email, $asunto, $texto, $htmldoc, $attach, $url, $dir_attach, $smtp);
};
# ------------------------------------------------------------------------------
sub enviar_mail_notif {
# Notifica al area prontus la ocurrencia del update
    my ($email, $old_version, $new_version, $str_ok) = @_;
    my ($from) = 'prontus@altavoz.net';
    my ($replyto_name) = 'Prontus CMS';
    my ($replyto_email) =  'prontus@altavoz.net';
    my $server = $prontus_varglb::IP_SERVER;
    my $dir_server_ofusc = $prontus_varglb::DIR_SERVER;
    $dir_server_ofusc =~ s/\//-/g;
    $dir_server_ofusc =~ s/^[- ]+//g;
    $server .= " ($dir_server_ofusc)" if ($server =~ /^[0-9]+\.[0-9]+\./);

    my ($asunto) = "[prontus-update] ".&lib_language::_msg_prontus('_update_ok_in')." $server - prontus_id: $prontus_varglb::PRONTUS_ID";
    my ($texto) = '';
    my ($htmldoc) = &lib_language::_msg_prontus('_update_triggered_from_IP').': ' . $ENV{'REMOTE_ADDR'}
                  . "<br>".&lib_language::_msg_prontus('_previous_release').": $old_version<br>".&lib_language::_msg_prontus('_current_release').": $new_version<br><br>"
                  . $str_ok;
    my ($attach) = '';
    my ($url) = '';
    my ($dir_attach) = '';
    my ($smtp) = $prontus_varglb::SERVER_SMTP;

    &lib_mail::enviar_mail($email, $from, $replyto_name, $replyto_email, $asunto, $texto, $htmldoc, $attach, $url, $dir_attach, $smtp);
};
# ------------------------------------------------------------------------------
sub actualizar_prontus {

    my $path_conf = shift;

    my ($msg, $quota_usado, $quota_asignado, $usado_porc, $nousado_porc) = &lib_quota::calcula_unix();
    
    &lib_loading::update_loading(100, 5);    
    my $msg_abort = &lib_language::_msg_prontus('_unable_update_prontus');

    # Creacion del objeto Update (todas los params son obligatorios).
    my $upd_obj = Update->new(
                    'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                    'version_prontus'   => $prontus_varglb::VERSION_PRONTUS,
                    'path_conf'         => $path_conf,
                    'document_root'     => $prontus_varglb::DIR_SERVER)
                    || &lib_logproc::add_to_log_finish("$msg_abort\n\n".&lib_language::_msg_prontus('_error_initializing_update').": [$Update::ERR]", 1);
    
    # Se chequea si es factible realizar la actualización
    &lib_loading::update_loading(100, 10);
    $upd_obj->descarga_upd_descriptor();
    if (!$upd_obj->update_disponible()) {
        return &lib_language::_msg_prontus('_error_no_updates_available_detected');
    };
    
    # Detecta instancias de prontus compatibles con las cgis
    &lib_loading::update_loading(100, 20);
    &lib_logproc::add_to_log_count(&lib_language::_msg_prontus('_detecting_prontus_instances')." ...");

    &lib_logproc::add_to_log_count(&lib_language::_msg_prontus('_calculating_space_available')." ...");
    my $ret = $upd_obj->check_before_download();
    return &lib_language::_msg_prontus('_error_calculate_free_disk_space').": [$Update::ERR]" if (!$ret);
    
    # Descarga release
    &lib_loading::update_loading(100, 30);
    &lib_logproc::add_to_log_count(&lib_language::_msg_prontus('_downloading_release').": " . $upd_obj->{last_version_disponible} . ' desde ' . $upd_obj->{update_server} . '/release ...');
    $ret = $upd_obj->descarga_release();
    return &lib_language::_msg_prontus('_error_downloading_release').": [$Update::ERR]" if (!$ret);
    &lib_logproc::add_to_log_count(&lib_language::_msg_prontus('_release_downloaded_ok')." /_prontus_update/downloads/" . $upd_obj->{last_version_disponible});
    
    # Se chequea factibilidad de instalacion
    &lib_loading::update_loading(100, 70);
    $ret = $upd_obj->check_before_update();
    return &lib_language::_msg_prontus('_error_make_validation').": [$Update::ERR]" if (!$ret);
    
    # Se realizaon los respaldos de todos los elementos
    &lib_loading::update_loading(100, 75);
    $ret = $upd_obj->crea_respaldos();
    return &lib_language::_msg_prontus('_error_creating_backups').": [$Update::ERR]" if (!$ret);
    
    # Instala CGIs de prontus
    &lib_loading::update_loading(100, 80);
    &lib_logproc::add_to_log_count(&lib_language::_msg_prontus('_instaling_new_CGIs'));
    $ret = $upd_obj->install_cgis();
    return &lib_language::_msg_prontus('_error_installing_CGIs').": [$Update::ERR]" if (!$ret);
    &lib_logproc::add_to_log_count(&lib_language::_msg_prontus('_CGI_installed_ok'));
    
    # Actualiza core de las instancias prontus detectadas y tb. del prontus_dir del wizard
    &lib_loading::update_loading(100, 85);
    &lib_logproc::add_to_log_count(&lib_language::_msg_prontus('_updating_folder_core_prontus_instances_detected')." [$upd_obj->{core_dirs}]");
    $ret = $upd_obj->install_core();
    return &lib_language::_msg_prontus('_error_installing_core').": [$Update::ERR]" if (!$ret);
    &lib_logproc::add_to_log_count(&lib_language::_msg_prontus('_folder_core_prontus_instances')." [$upd_obj->{core_dirs}] ".&lib_language::_msg_prontus('_undated_ok'));

    # Actualiza /wizard_prontus/core
    &lib_loading::update_loading(100, 90);
    &lib_logproc::add_to_log_count(&lib_language::_msg_prontus('_undating_folder')." '/wizard_prontus/core'");
    $ret = $upd_obj->install_core_wizard();
    return &lib_language::_msg_prontus('_error_installing_core_wizard').": [$Update::ERR]" if (!$ret);
    &lib_logproc::add_to_log_count(&lib_language::_msg_prontus('_folder')." '/wizard_prontus/core' ".&lib_language::_msg_prontus('_undated_ok'));

    # Borra files descargados
    &lib_loading::update_loading(100, 95);
    $upd_obj->garbage_dirs();

    my $du_result;
    my $dir4du = "$prontus_varglb::DIR_SERVER/_prontus_update";
    $du_result = `du -d 2 -h $dir4du`; # estilo unix/freebsd
    if ($du_result eq '') {
        $du_result = `du -h $dir4du --max-depth=2`; # estilo linux
    };
    $du_result =~ s/$prontus_varglb::DIR_SERVER//isg;

    my $str_ok = &lib_language::_msg_prontus('_update_finished_ok')."<br>"
               . "- ".&lib_language::_msg_prontus('_folders_updated_files_backups')." /_prontus_update/updated/.<br>"
               . "- ".&lib_language::_msg_prontus('_contingency_downloaded_update_preserved_in')." /_prontus_update/downloads/.<br>"
               . "- ".&lib_language::_msg_prontus('_in_both_cases_3_backups_saved').",<br>".&lib_language::_msg_prontus('_olders_deleted_no_accumulation')."<br>"
               . "<br>".&lib_language::_msg_prontus('_current_backups_size').":<br><pre>$du_result</pre>";
    &lib_logproc::add_to_log_count($str_ok);
    
    &enviar_mail_notif($EMAIL_SOPORTE_PRONTUS, $prontus_varglb::VERSION_PRONTUS, $upd_obj->{last_version_disponible}, $str_ok);
    &lib_loading::update_loading(100, 100);
    
    return '';

};


# -------------------------END SCRIPT----------------------
