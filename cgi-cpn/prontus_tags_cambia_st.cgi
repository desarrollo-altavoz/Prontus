#!/usr/bin/perl


# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# SCRIPT.
# -----------
# prontus_secc_admin.pl.
#
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /prontus/.
#
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Administrador de Secciones de noticias.
#
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------------
# prontus_temas_admin.pl (link Ver en columna Temas).
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde /prontus4_nots/cpan/core/prontus_menu.html
#
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# Plantillas:
#   /prontus4_nots/cpan/core/mant_seccs/prontus_secc_admin.html.
#   /prontus4_nots/cpan/core/mant_seccs/mensajes.html (para mensajes de error).
#
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# Paginas web: No registra. El resultado se imprime directamente hacia el browser.
#
# ---------------------------------------------------------------
# Tablas.
# -------------------
# SECC - # PERSEMP.
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 16/10/2003 - YCH - Primera version.
# 1.1 - 16/10/2007 - YCH - Elimina link mapa del sitio (segun instruccion de ald).
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
use glib_html_02;
use glib_dbi_02;
use glib_fildir_02;

use lib_prontus;
use strict;
use glib_cgi_04;
use lib_tags;

$| = 1; # Sin buffer. Despliega a medida que va leyendo.

# ---------------------------------------------------------------
# MAIN.
# -------------

my ($BD, %FORM,);
my (%XML_VISTAS);

my $RELPATH_TEMPL = '/cpan/core/prontus_tags_admin.html';

main: {

    # Rescatar parametros recibidos.

    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;


    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # user no valido
    if ($prontus_varglb::USERS_ID eq '') {
        #~ &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin o editor
    if ($prontus_varglb::USERS_PERFIL eq 'P') {
      &glib_html_02::print_pag_result('Acceso a Area Restringida','La funcionalidad requerida no está disponible para perfil Redactor',1,'exit=1,ctype=1');
    };


    $FORM{'_id_tag'} = &glib_cgi_04::param('_id_tag');
    if ($FORM{'_id_tag'} !~ /^(\d+)$/) {
        &glib_html_02::print_json_result(0, 'ID del tag no es válido', 'exit=1,ctype=1');
    };

    $FORM{'_new_st'} = &glib_cgi_04::param('_new_st');
    if ($FORM{'_new_st'} !~ /^[1|0]$/) {
        &glib_html_02::print_json_result(0, 'El nuevo estado no es válido', 'exit=1,ctype=1');
    };

    # Conectar a BD
    my $msg;
    ($BD, $msg) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1');
    };

    $msg = &do_update();
    &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1') if ($msg);

    # Se libera el caché de los tags del fid
    &lib_tags::clear_cache($prontus_varglb::PRONTUS_ID);

    $BD->disconnect;

    &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');

}; # main.

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------



sub do_update {

#    if (! &no_referenciada($FORM{'_id_tag'})) {
#        return 'Item está siendo utilizado en algún artículo. No se puede borrar.';
#    };

    my ($sql, $salida);

    # Elimina Tag
    $sql = "update TAGS set TAGS_MOSTRAR = " . $FORM{'_new_st'} . ' where TAGS_ID = ' . $FORM{'_id_tag'};
    unless( $BD->do($sql) ) {
        print STDERR $BD->errstr;
        return 'Error actualizando el Estado del Tag en la base de datos';
    };
    return '';

};
