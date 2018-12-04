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

# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/.

# ---------------------------------------------------------------
# PROPOSITO.
# -----------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------

# ---------------------------------------------------------------
# INVOCACIONES REALIZADAS.
# ------------------------

# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------

# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------

# ---------------------------------------------------------------
# Tablas.
# ------------------------
# No utiliza.

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------

# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();

use glib_html_02;
use glib_fildir_02;
use lib_prontus;

use glib_cgi_04;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my (%FORM);


main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();

    $FORM{'NEW_PORT'} = &glib_cgi_04::param('NEW_PORT'); # nombre c/ext. y sin path de la nueva portada.

    $FORM{'Lst_PORTACT'} = &glib_cgi_04::param('Lst_PORT4');

    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # Acceso permitido solo para admin
    if (($prontus_varglb::ADMIN_PORT ne 'SI') or ($prontus_varglb::USERS_PERFIL ne 'A')) {
        &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_access_restricted_area'),&lib_language::_msg_prontus('_functionality_available_administrator_presetting'));
        exit;
    };

    my $origen;

    my $dir_port = $prontus_varglb::DIR_SERVER .
                 $prontus_varglb::DIR_TEMP .
                 $prontus_varglb::DIR_EDIC .
                 $prontus_varglb::DIR_NROEDIC .
                 $prontus_varglb::DIR_SECC;

    $origen = "$dir_port/" . $FORM{'Lst_PORTACT'};

    if (!(-f $origen)) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_invalid_selected_template'), 'exit=1,ctype=1');
        exit;
    };


    my ($msg);

    unlink $origen;
    if (-s $origen) {
        $msg = &lib_language::_msg_prontus('_unable_delete_selected_template');
        &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1');

    } else {
        &update_cfg();
        # Duplica vistas
        my $mv;
        foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
            my $origen_mv = "$dir_port-$mv/" . $FORM{'Lst_PORTACT'};
            unlink $origen_mv;
        };
        # CVI - 10/01/2012 - Se Logea esta accion
        &lib_prontus::write_log('Borrar', 'Portada', $origen);

        $msg = &lib_language::_msg_prontus('_selected_template_deleted_correctly');
        &glib_html_02::print_json_result(1, $msg, 'exit=1,ctype=1');
    };

};


# ---------------------------------------------------------------

sub update_cfg {
    # nom_port --> nombre con extension y sin path.

    my $nomcfg;
    if ($FORM{'_path_conf'} =~ /(.*)\.cfg$/) {
        $nomcfg = $1;
    };

    my ($buffer) = &glib_fildir_02::read_file("$nomcfg-port.cfg");

    # Respalda antes de aplicar cambios.
    my ($bak) = "$nomcfg-port.cfg";
    my $dir_bak = $bak;
    $dir_bak =~ s/\/$prontus_varglb::PRONTUS_ID\-port\.cfg$//;
    $dir_bak .= '/_unused';
    &glib_fildir_02::check_dir($dir_bak);

    $bak =~ s/\/cpan\/$prontus_varglb::PRONTUS_ID\-port\.cfg$/\/cpan\/_unused\/$prontus_varglb::PRONTUS_ID\-port\.bak/i;

    &glib_fildir_02::write_file($bak, $buffer);

    my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;

    $buffer =~ s/$crlf/\x0a/sg;

    $buffer =~ s/ *PORT_PLTS *= *['"]$FORM{'Lst_PORTACT'}(\(.*?\)){0,3}['"]//isg;



    # Elimina linea del cfg.
    # $buffer =~ s/ *PORT_PLTS *= *['"]$FORM{'Lst_PORTACT'}(\(.*\)){0,3}['"]//isg;
    # $buffer =~ s/ *PORT_PLTS *= *['"]$FORM{'Lst_PORTACT'}(\(.*\)){0,3}['"].*\n//isg;
    $buffer =~ s/ *BASE_PORTS *= *['"]$FORM{'Lst_PORTACT'}('|")//isg;


    # Guarda el archivo cfg.
    &glib_fildir_02::write_file("$nomcfg-port.cfg", $buffer);
    # print STDERR "CFG[$buffer]\n";
};
# ----------------------------END-SCRIPT-----------------------------------
