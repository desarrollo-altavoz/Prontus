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
# parsea:
# Hola [admin] ([Administrador]), estás trabajando en [prontus_toolbox].
# Espacio disponible: xxx...
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------

#
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------

# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------

# ---------------------------------------------------------------

# HISTORIAL DE VERSIONES.
# ---------------------------

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};


use prontus_varglb;
&prontus_varglb::init();

use glib_html_02;
use glib_fildir_02;
use lib_prontus;

use glib_cgi_04;

use lib_quota;
use Update;


my (%FORM);
# ---------------------------------------------------------------
# MAIN.
# -------------


main: {

    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    my $buffer = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/prontus_head_info.html");

    $buffer =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/g;
    $buffer =~ s/%%_path_conf%%/$FORM{'_path_conf'}/g;

    $buffer =~ s/%%_prontus_version%%/versi&oacute;n $prontus_varglb::VERSION_PRONTUS/g;
    $buffer =~ s/%%_prontus_user_name%%/$prontus_varglb::USERS_USR/g;

    my $glosa_perfil = &lib_prontus::get_glosa_perfil(); # basandose en $prontus_varglb::USERS_PERFIL
    $buffer =~ s/%%_prontus_user_perfil%%/$glosa_perfil/g;

    my ($msg, $usado_mb, $quota_asig_mb, $usado_porc, $nousado_porc);

    ($msg, $usado, $quota_asig, $usado_porc, $nousado_porc) = &lib_quota::calcula_unix();
    # ($msg, $usado_mb, $quota_asig_mb, $usado_porc, $nousado_porc) = ('', 111, 222, '40%', '60%');# debug
    my $class_level = 1;
    $usado_porc =~ /^(\d+)/i;
    my $used = $1;
    if($used > 50 && $used <= 80) {
      $class_level = 2;
    } elsif($used > 80) {
      $class_level = 3;
    };
    if ($msg ne '') {
        $buffer =~ s/%%_quota_msg%%/$msg/g;
        $buffer =~ s/<!--quota_data-->(.*)<!--\/quota_data-->//sg;
    } else {
        $buffer =~ s/<!--quota_msg-->(.*)<!--\/quota_msg-->//sg;
        my $usado_format      = &lib_quota::format_bytes($usado);
        my $quota_asig_format = &lib_quota::format_bytes($quota_asig);
        $buffer =~ s/%%_usado_format%%/$usado_format/g;
        $buffer =~ s/%%_quota_asig_format%%/$quota_asig_format/g;

        $buffer =~ s/%%_usado_porc%%/$usado_porc/g;
        $buffer =~ s/%%_nousado_porc%%/$nousado_porc/g;
        $buffer =~ s/%%_class_level%%/$class_level/g;
    };

    # Revisa el file de actualizaciones disponibles.
    my $status_upd;

    if ($prontus_varglb::USERS_PERFIL eq 'A') {
        # Creacion del objeto Update (todas los params son obligatorios).
        my $upd_obj = Update->new(
                        'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                        'version_prontus'   => $prontus_varglb::VERSION_PRONTUS,
                        'actualizaciones'   => $prontus_varglb::ACTUALIZACIONES,
                        'path_conf'         => $FORM{'_path_conf'},
                        'document_root'     => $prontus_varglb::DIR_SERVER,
                        'just_status'           => '1')
                        || &glib_html_02::print_pag_result('Error',"Error inicializando objeto Update: $Update::ERR", 1, 'exit=1,ctype=1');

        $status_upd = $upd_obj->get_status_update();
    } else {
        $status_upd = 'no_user';
    }

    $buffer =~ s/%%_status_upd%%/$status_upd/g;

    print "Content-Type: text/html\n\n";
    print $buffer;

};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------


# -------------------------------END SCRIPT----------------------
