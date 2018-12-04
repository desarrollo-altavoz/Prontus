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
# Borra Grapevar
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/coment/coment_cambia_st.cgi

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# cambia status.

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
# http://192.168.6.24/cgi-cpn/coment/coment_cambia_st.cgi?COMENT_ID=3&CURRENT_ST=1&_prontus_id=prontus_toolbox
my (%FORM, $PLANT_MAIL_PUBLICA);

main: {
    # Rescatar parametros recibidos.
    &glib_cgi_04::new();

    $FORM{'COMENT_ID'} = &glib_cgi_04::param('COMENT_ID');
    $FORM{'NEW_ST'} = &glib_cgi_04::param('NEW_ST');
    $FORM{'_prontus_id'} = &glib_cgi_04::param('_prontus_id');


    if (! &lib_prontus::valida_prontus($FORM{'_prontus_id'})) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_901_error_data_sent'), 'exit=1,ctype=1');
    };
    if (! -d "$coment_varglb::DIR_SERVER/$FORM{'_prontus_id'}") {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_902_error_data_sent'), 'exit=1,ctype=1');
    };

    # Carga variables de configuracion.
    $FORM{'_path_conf'} = "$coment_varglb::DIR_SERVER/$FORM{'_prontus_id'}/cpan/$FORM{'_prontus_id'}.cfg";
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };


    $PLANT_MAIL_PUBLICA = $coment_varglb::DIR_SERVER . "/$prontus_varglb::PRONTUS_ID/coment/plantillas/coment_email_publica.html";

    # Abrir BD.
    my ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    &glib_html_02::print_json_result(0, $msg_err_bd, 'exit=1,ctype=1') if ($msg_err_bd ne '');

    if  (!$FORM{'COMENT_ID'}) {
        $BD->disconnect;
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_record_no_exist.'), 'exit=1,ctype=1');
    }
    else {

        # Cambia st
        my $new_st = '0';
        $new_st = '1' if ($FORM{'NEW_ST'});
        my $sql = " update COMENT set COMENT_STATUS = \"$new_st\" where COMENT_ID = \"$FORM{'COMENT_ID'}\"";
        # print STDERR "sql[$sql]\n";
        $BD->do($sql) || &glib_html_02::print_json_result(0, 'DB Error: '.$BD->errstr, 'exit=1,ctype=1');

        # Obtiene datos faltantes y genera coments pag.
        $sql = "select COMENT_OBJTIPO, COMENT_OBJID, COMENT_OBJTIT, COMENT_NICK from COMENT where COMENT_ID = \"$FORM{'COMENT_ID'}\"";
        my ($objtipo, $objid, $objtit, $nick);
        my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($objtipo, $objid, $objtit, $nick));
        $salida->fetch;
        $salida->finish;
        &lib_coment::generar_comentarios($BD, $coment_varglb::DIR_SERVER, $objtipo, $objid, $prontus_varglb::PRONTUS_ID);

        &notificar_publicacion($nick, $objid, $objtit, $objtipo) if ($new_st);

        # my $msg = $FORM{'COMENT_ID'} . "|Status cambiado.";
        $BD->disconnect;
        &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');

    };
}; # main.

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub notificar_publicacion {
# Envia un mensaje de correo electronico. al usuario que envió
# comentario, para avisarle que fue publicado
    my ($nick, $objid, $objtit, $objtipo) = @_;

    # Carga y valida cfg
    my ($options_tipo, $msg_err, $hash_tipos_ref) = &lib_coment::get_objtipos($coment_varglb::DIR_SERVER, '', $prontus_varglb::PRONTUS_ID);
    my %hash_tipos = %$hash_tipos_ref;
    if ($msg_err) {
        &glib_html_02::print_json_result(0, $msg_err, 'exit=1,ctype=1');
    };

    if (lc($hash_tipos{$objtipo}{'ENVIAR_MAIL_PUBLICACION'}) eq 'si')  {
        my ($email) = $nick;
        my ($from) = $hash_tipos{$objtipo}{'MAIL_PUBLICACION_FROM'};
        my ($replyto_name) = '';
        my ($replyto_email) = $from;
        my ($asunto) = $hash_tipos{$objtipo}{'MAIL_PUBLICACION_ASUNTO'};
        my ($texto) = '';
        my ($htmldoc) = &glib_fildir_03::read_file($PLANT_MAIL_PUBLICA);

        # reemplazos
        my $file = $hash_tipos{$objtipo}{'URL'};
        $file =~ s/<idobj>/$objid/ig;
        $htmldoc =~ s/%%_FILE%%/$file/ig;
        $htmldoc =~ s/%%_TITULAR%%/$objtit/ig;
        $htmldoc =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/ig;

        my ($attach) = '';
        my ($url) = '';
        my ($dir_attach) = '';
        my $smtp = $hash_tipos{$objtipo}{'MAIL_PUBLICACION_SMTP'};

        &lib_mail::enviar_mail($email, $from, $replyto_name, $replyto_email, $asunto, $texto, $htmldoc, $attach, $url, $dir_attach, $smtp);
    };

};


# ----------------------------END SCRIPT---------------------
