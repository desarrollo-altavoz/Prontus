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
# Regenera las paginas de comentario
#
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/coment/coment_regenera.cgi
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 07/2014 - CVI - Primera Version.
# ---------------------------------------------------------------

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    $pathLibsProntus =~ s/\/coment$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus


};

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);


use DBI;
use glib_dbi_02;
use glib_cgi_04;
use coment_varglb;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;
use lib_coment;
use lib_mail;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my (%FORM, $PLANT_MAIL_PUBLICA);

main: {
    # Rescatar parametros recibidos.
    &glib_cgi_04::new();
    $FORM{'_prontus_id'} = &glib_cgi_04::param('_prontus_id');

    # Carga variables de configuracion.
    my $path_conf = "$coment_varglb::DIR_SERVER/$FORM{'_prontus_id'}/cpan/$FORM{'_prontus_id'}.cfg";
    &lib_prontus::load_config(&lib_prontus::ajusta_pathconf($path_conf));  # Prontus 6.0

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };
    # Abrir BD.
    my ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    &glib_html_02::print_json_result(0, $msg_err_bd, 'exit=1,ctype=1') if ($msg_err_bd ne '');

    print "Content-Type: text/html\n\n";
    print "<h3>Comenzando a regenerar</h3>";
    print "<pre>";
    print "dir_server[$coment_varglb::DIR_SERVER]\n";
    # Obtiene todos los comentarios
    my $sql = "select COMENT_OBJTIPO, COMENT_OBJID from COMENT group by COMENT_OBJID, COMENT_OBJTIPO";
    my ($objtipo, $objid);
    my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($objtipo, $objid));
    while($salida->fetch) {
        print "[$objtipo] -->  [$objid]\n";
        &lib_coment::generar_comentarios($BD, $coment_varglb::DIR_SERVER, $objtipo, $objid, $prontus_varglb::PRONTUS_ID);
    }
    print "</pre>";
    $salida->finish;
    $BD->disconnect;        

    
}; # main.
