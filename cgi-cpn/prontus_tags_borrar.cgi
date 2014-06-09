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
use lib_tags;

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

    # Conectar a BD
    my $msg;
    ($BD, $msg) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1');
    };

    $msg = &do_delete();
    &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1') if ($msg);
    $BD->disconnect;

    # Se libera el caché de los tags del fid
    &lib_tags::clear_cache($prontus_varglb::PRONTUS_ID);

    # Si todo sale bien, se elimina el text con los datos
    my $dir_txt = $prontus_varglb::DIR_SERVER . '/'.$prontus_varglb::PRONTUS_ID.'/site/cache/tagging/pags/';
    if(-f $dir_txt . $FORM{'_id_tag'} . '.txt') {
      unlink($dir_txt . $FORM{'_id_tag'} . '.txt');
    };

    &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');

}; # main.

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------



sub do_delete {

    if (! &no_referenciada($FORM{'_id_tag'})) {
        return 'Item está siendo utilizado en algún artículo. No se puede borrar.';
    };

    my ($sql, $salida);

    # Elimina Tag
    $sql = "delete from TAGS where TAGS_ID = " . $FORM{'_id_tag'};
    unless( $BD->do($sql) ) {
        print STDERR $BD->errstr;
        return 'Error eliminando tags de la base de datos';
    };
    return '';

};


# ---------------------------------------------------------------
sub no_referenciada {

  # Verifica que el registro actual no este referenciado en alguna de las tablas principales correspondientes.
  my ($id) = $_[0];
  my ($sql, $salida, $id_ref);

  $sql = "select TAGSART_IDTAGS from TAGSART where TAGSART_IDTAGS = $id";
  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \$id_ref);
  $salida->fetch;
  if ($salida->rows <= 0) {
    return 1; # No referenciada.
  };
  return 0; # Referenciada.
}; # no_referenciada.

# ----------------------------END SCRIPT---------------------
