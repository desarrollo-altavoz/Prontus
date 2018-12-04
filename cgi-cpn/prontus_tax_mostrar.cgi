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
# SCRIPT.
# -----------
# prontus_secc_guardar.cgi.
#
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /prontus/.
#
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Mantencion Secciones. Crea, actualiza y/o elimina.
#
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------------
# Location: prontus_secc_admin.cgi (Administrador de Secciones).
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde pagina 'Administrador de Secciones' (/prontus4_nots/cpan/core/mant_seccs/prontus_secc_admin.html) boton 'Guardar'.
#
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# Plantillas: /prontus4_nots/cpan/core/mant_seccs/mensajes.html (para mensajes de error).
#
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# Paginas web: No registra.
#
# ---------------------------------------------------------------
# Tablas.
# -------------------
# SECC - TEMAS - SUBTEMAS.
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 16/10/2003 - YCH - Primera version.
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
use glib_dbi_02;
use glib_html_02;
use glib_cgi_04;
use glib_str_02;
use lib_secc;

use lib_prontus;
use strict;



# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM, $BD);


my %DATA_VISTAS;

main: {

    # Rescatar parametros recibidos.

    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    $FORM{'_entidad'} = &glib_cgi_04::param('_entidad');
    $FORM{'_entidad'} = 'seccion' if ($FORM{'_entidad'} eq '');
    if ($FORM{'_entidad'} !~ /^(seccion|tema|subtema)$/) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_invalid_entity_type'), 'exit=1,ctype=1');
    };

    if ($FORM{'_entidad'} eq 'tema') {
        $FORM{'_secc_id'} = &glib_cgi_04::param('_secc_id');
        if ($FORM{'_secc_id'} !~ /^[0-9]+$/) {
            &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_invalid_section'), 'exit=1,ctype=1');
        };
    };

    if ($FORM{'_entidad'} eq 'subtema') {
        $FORM{'_tema_id'} = &glib_cgi_04::param('_tema_id');
        if ($FORM{'_tema_id'} !~ /^[0-9]+$/) {
            &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_invalid_topic'), 'exit=1,ctype=1');
        };
    };


    $FORM{'_id'}= &glib_cgi_04::param('_id');
    if (($FORM{'_id'} !~ /^[0-9]+$/) || (!$FORM{'_id'})) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_invalid_id'), 'exit=1,ctype=1');
    };

    $FORM{'_mostrar'}= &glib_cgi_04::param('_mostrar');
    if ($FORM{'_mostrar'} !~ /^[01]$/) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_invalid_show_field'), 'exit=1,ctype=1');
    };
    $FORM{'_mostrar'} = '' if (!$FORM{'_mostrar'});

    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # user no valido
    if ($prontus_varglb::USERS_ID eq '') {
        #~ &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };
    
    # Conectar a BD
    my $msg;
    ($BD, $msg) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1');
    };

    $msg = &do_update();
    &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1') if ($msg);

    # &actualiza_xml_vistas($new_id); TO-DO !!!!!!!!!!!!!!!!!!!
    &lib_prontus::make_mapa('', $BD);

    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        &lib_prontus::make_mapa($mv, $BD);
    };

    # Genera tax en arch. JS, para ser incluido en FIDs
    my $arr_tst = &lib_secc::genera_array_temas_subtemas($BD, '', 'solo habilitadas');
    my $dir_tax4fids = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CPAN . '/procs/tax4fids';
    &glib_fildir_02::check_dir($dir_tax4fids);
    &glib_fildir_02::write_file($dir_tax4fids . '/tax4fids.js', $arr_tst);

    $BD->disconnect;

    &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');

}; # main.

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub do_update {

    # Saving de mostrar
    my $sql;
    $sql = "update SECC set SECC_MOSTRAR = '$FORM{'_mostrar'}' where SECC_ID = $FORM{'_id'} " if ($FORM{'_entidad'} eq 'seccion');
    $sql = "update TEMAS set TEMAS_MOSTRAR = '$FORM{'_mostrar'}' where TEMAS_ID = $FORM{'_id'} " if ($FORM{'_entidad'} eq 'tema');
    $sql = "update SUBTEMAS set SUBTEMAS_MOSTRAR = '$FORM{'_mostrar'}' where SUBTEMAS_ID = $FORM{'_id'} " if ($FORM{'_entidad'} eq 'subtema');
    $BD->do($sql) || return &lib_prontus::handle_internal_error($BD->errstr, 'Error actualizando visibilidad del �tem en la base de datos', 'exit=0');
    return '';

};



# ----------------------------END SCRIPT---------------------
