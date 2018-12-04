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
#
# Borra coment
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/coment/coment_borrar.cgi

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# elimina el registro.

# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
#
#
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# No registra.

# ---------------------------------------------------------------
# Tablas.
# ------------------------


# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 11/2006 - YCH - Primera Version.
# ---------------------------------------------------------------

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    
    $pathLibsProntus =~ s/\/coment$//;
    unshift(@INC,$pathLibsProntus);
};

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use DBI;
use glib_dbi_02;
use glib_cgi_04;
use coment_varglb;
use glib_html_02;
use lib_coment;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%FORM);

main: {
    # Rescatar parametros recibidos.
    &glib_cgi_04::new();

    $FORM{'COMENT_ID'} = &glib_cgi_04::param('COMENT_ID');
    $FORM{'_prontus_id'} = &glib_cgi_04::param('_prontus_id');

    if (! &lib_prontus::valida_prontus($FORM{'_prontus_id'})) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_901_error_data_sent'), 'exit=1,ctype=1');
    };
    if (! -d "$coment_varglb::DIR_SERVER/$FORM{'_prontus_id'}") {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_902_error_data_sent'), 'exit=1,ctype=1');
    };

    # Carga variables de configuracion.
    $FORM{'_path_conf'} = "$coment_varglb::DIR_SERVER/$FORM{'_prontus_id'}/cpan/$FORM{'_prontus_id'}.cfg";
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    # Abrir BD.
    my ($BD, $msg_err_bd);
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    &glib_html_02::print_json_result(0, $msg_err_bd, 'exit=1,ctype=1') if ($msg_err_bd ne '');
    

    if  (!$FORM{'COMENT_ID'}) {
        $BD->disconnect;
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_record_no_exist.'), 'exit=1,ctype=1');
    } else {

        # Obtiene datos faltantes.
        my $sql = "select COMENT_OBJTIPO, COMENT_OBJID from COMENT where COMENT_ID = \"$FORM{'COMENT_ID'}\"";
        my ($objtipo, $objid);
        my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($objtipo, $objid));
        $salida->fetch;

        # Elimina reg.
        $sql = " DELETE FROM COMENT WHERE COMENT_ID = \"$FORM{'COMENT_ID'}\"";
        $BD->do($sql) || &glib_html_02::print_json_result(0, 'DB Error: '.$BD->errstr, 'exit=1,ctype=1');
        
        # genera coments pag actualizada.
        &lib_coment::generar_comentarios($BD, $coment_varglb::DIR_SERVER, $objtipo, $objid, $prontus_varglb::PRONTUS_ID);
        
        # comentario eliminado.
        &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');

    };
}; # main.

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
# No registra.
# ----------------------------END SCRIPT---------------------
