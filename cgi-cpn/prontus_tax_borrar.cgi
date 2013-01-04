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
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

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

    $FORM{'_entidad'} = &glib_cgi_04::param('_entidad');
    $FORM{'_entidad'} = 'seccion' if ($FORM{'_entidad'} eq '');
    if ($FORM{'_entidad'} !~ /^(seccion|tema|subtema)$/) {
        &glib_html_02::print_json_result(0, 'Tipo de entidad no es válida', 'exit=1,ctype=1');
    };

    if ($FORM{'_entidad'} eq 'tema') {
        $FORM{'_secc_id'} = &glib_cgi_04::param('_secc_id');
        if ($FORM{'_secc_id'} !~ /^[0-9]+$/) {
            &glib_html_02::print_json_result(0, 'Sección no es válida', 'exit=1,ctype=1');
        };
    };

    if ($FORM{'_entidad'} eq 'subtema') {
        $FORM{'_tema_id'} = &glib_cgi_04::param('_tema_id');
        if ($FORM{'_tema_id'} !~ /^[0-9]+$/) {
            &glib_html_02::print_json_result(0, 'Tema no es válido', 'exit=1,ctype=1');
        };
    };


    $FORM{'_id'}= &glib_cgi_04::param('_id');
    if (($FORM{'_id'} !~ /^[0-9]+$/) || (!$FORM{'_id'})) {
        &glib_html_02::print_json_result(0, 'Id no válido', 'exit=1,ctype=1');
    };


    # Conectar a BD
    my $msg;
    ($BD, $msg) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1');
    };

    $msg = &do_delete();
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



sub do_delete {

    if (! &no_referenciada($FORM{'_id'})) {
        return 'Item está siendo utilizado en algún artículo. No se puede borrar.';
    };

    my ($sql, $salida);

    # Eliminar seccion y todos sus temas/subtemas
    if ($FORM{'_entidad'} eq 'seccion') {
        # Selecciona todos los temas de la seccion a eliminar.
        $sql = "select TEMAS_ID from TEMAS where TEMAS_IDSECC = $FORM{'_id'}";
        my $id_temas;
        $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \$id_temas);

        while ($salida->fetch) {
            # Elimina subtema.
            $sql = " delete from SUBTEMAS where SUBTEMAS_IDTEMAS = $id_temas";
            $BD->do($sql) || return &lib_prontus::handle_internal_error($BD->errstr, 'Error eliminando categorías de la base de datos', 'exit=0');
        };

        $salida->finish;

        # Elimina Temas.
        $sql = " delete from TEMAS where TEMAS_IDSECC = $FORM{'_id'}";
        $BD->do($sql) || return &lib_prontus::handle_internal_error($BD->errstr, 'Error eliminando categorías de la base de datos', 'exit=0');

        # Elimina Secc.
        $sql = " delete from SECC where SECC_ID = $FORM{'_id'}";
        $BD->do($sql) || return &lib_prontus::handle_internal_error($BD->errstr, 'Error eliminando categorías de la base de datos', 'exit=0');
    };

    # Eliminar tema y todos sus subtemas
    if ($FORM{'_entidad'} eq 'tema') {

        # Elimina subtemas.
        $sql = " delete from SUBTEMAS where SUBTEMAS_IDTEMAS = $FORM{'_id'}";
        $BD->do($sql) || return &lib_prontus::handle_internal_error($BD->errstr, 'Error eliminando categorías de la base de datos', 'exit=0');

        # Elimina tema
        $sql = " delete from TEMAS where TEMAS_ID = $FORM{'_id'}";
        $BD->do($sql) || return &lib_prontus::handle_internal_error($BD->errstr, 'Error eliminando categorías de la base de datos', 'exit=0');
    };

    # Eliminar subtema
    if ($FORM{'_entidad'} eq 'subtema') {

        # Elimina subtema
        $sql = " delete from SUBTEMAS where SUBTEMAS_ID = $FORM{'_id'}";
        $BD->do($sql) || return &lib_prontus::handle_internal_error($BD->errstr, 'Error eliminando categorías de la base de datos', 'exit=0');
    };

    return '';

};


# ---------------------------------------------------------------
sub no_referenciada {

  # Verifica que el registro actual no este referenciado en alguna de las tablas principales correspondientes.
  my ($id) = $_[0];
  my ($sql, $salida, $id_ref);

  $sql = "select ART_ID from ART where ART_IDSECC1 = $id or ART_IDSECC2 = $id or ART_IDSECC3 = $id" if ($FORM{'_entidad'} eq 'seccion');
  $sql = "select ART_ID from ART where ART_IDTEMAS1 = $id OR ART_IDTEMAS2 = $id OR ART_IDTEMAS3 = $id" if ($FORM{'_entidad'} eq 'tema');
  $sql = "select ART_ID from ART where ART_IDSUBTEMAS1 = $id or ART_IDSUBTEMAS2 = $id or ART_IDSUBTEMAS3 = $id" if ($FORM{'_entidad'} eq 'subtema');
  # print STDERR "sql SECC NOREF[$sql]\n\n";
  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \$id_ref);
  $salida->fetch;
  if ($salida->rows <= 0) {
    return 1; # No referenciada.
  };

  return 0; # Referenciada.
}; # no_referenciada.

# ----------------------------END SCRIPT---------------------
