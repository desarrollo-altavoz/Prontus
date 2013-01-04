#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 23/09/2011 - JOR - Primera versión
# ---------------------------------------------------------------

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------------------------------------------

BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);

    # Incluir path de coment/
    use FindBin '$Bin';
};

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use glib_fildir_02;
use lib_mail;
use lib_prontus;
use strict;
use lib_prontus;
use File::Copy;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%FORM);

main: {
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'}     =~ s/^$prontus_varglb::DIR_SERVER//;
    $FORM{'nombre'}         = &glib_cgi_04::param('nombre');
    $FORM{'email'}          = &glib_cgi_04::param('email');
    $FORM{'tipomsg'}        = &glib_cgi_04::param('tipomsg');
    $FORM{'mensaje'}        = &glib_cgi_04::param('mensaje');
    $FORM{'asunto'}         = &glib_cgi_04::param('asunto');
    $FORM{'empresa'}        = &glib_cgi_04::param('empresa');
    $FORM{'cargo'}          = &glib_cgi_04::param('cargo');
    $FORM{'telefono'}       = &glib_cgi_04::param('telefono');
    $FORM{'disponibilidad'} = &glib_cgi_04::param('disponibilidad');

    my $temp_adjunto_file = &glib_cgi_04::param('adjunto');
    my $real_path_file    = &glib_cgi_04::real_paths('adjunto');

    my ($nom_file_temp, $ext_file_temp) = &get_nomfile($temp_adjunto_file);
    my ($nom_file_destino, $ext_file_destino) = &get_nomfile($real_path_file);
    my $destino = $temp_adjunto_file;
    $destino =~ s/$nom_file_temp/$nom_file_destino/sg;

    if (!move($temp_adjunto_file, $destino)) {
        $destino = $temp_adjunto_file;
    };

    if ($FORM{'nombre'} eq '') {
        &glib_html_02::print_json_result(0, 'El campo "Nombre" es obligatorio.', 'exit=1,ctype=1');
    };

    if (length($FORM{'nombre'}) > 100 ) {
        &glib_html_02::print_json_result(0, 'El campo "Nombre" debe tener como máximo 100 caracteres.', 'exit=1,ctype=1');
    };

    if ($FORM{'email'} eq '') {
        &glib_html_02::print_json_result(0, 'El campo "Email" es obligatorio.', 'exit=1,ctype=1');
    };

    if ($FORM{'email'} !~ /^[_\.0-9a-zA-Z\-]+@([0-9a-zA-Z][0-9a-zA-Z\-]+\.)+[a-zA-Z]{2,6}$/) {
        &glib_html_02::print_json_result(0, 'Email ingresado no es válido.', 'exit=1,ctype=1');
    };

    if ($FORM{'empresa'} ne '' && length($FORM{'empresa'}) > 100) {
        &glib_html_02::print_json_result(0, 'El campo "Empresa u Organización" debe tener como máximo 100 caracteres.', 'exit=1,ctype=1');
    };

    if ($FORM{'cargo'} ne '' && length($FORM{'cargo'}) > 64) {
        &glib_html_02::print_json_result(0, 'El campo "Cargo" debe tener como máximo 64 caracteres.', 'exit=1,ctype=1');
    };

    if ($FORM{'telefono'} ne '' && length($FORM{'telefono'}) > 20) {
        &glib_html_02::print_json_result(0, 'El campo "Teléfono" debe tener como máximo 20 caracteres.', 'exit=1,ctype=1');
    };

    if ($FORM{'tipomsg'} eq '') {
        &glib_html_02::print_json_result(0, 'El campo "Motivo de Contacto" es obligatorio.', 'exit=1,ctype=1');
    };

    if ($FORM{'asunto'} eq '') {
        &glib_html_02::print_json_result(0, 'El campo "Asunto" es obligatorio.', 'exit=1,ctype=1');
    };

    if ($FORM{'asunto'} ne '' && $FORM{'asunto'} > 100) {
        &glib_html_02::print_json_result(0, 'El campo "Asunto" debe tener como máximo 100 caracteres.', 'exit=1,ctype=1');
    };

    if ($FORM{'mensaje'} eq '') {
        &glib_html_02::print_json_result(0, 'El campo "Texto" es obligatorio.', 'exit=1,ctype=1');
    };

    my ($str, $sub, $to, $from, $replyto);

    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    my $glosa_perfil = &lib_prontus::get_glosa_perfil();
    my $useragent = $ENV{'HTTP_USER_AGENT'};

    $to = 'Area Prontus <area_prontus@altavoz.net>';
    $from = 'prontus@altavoz.net';
    $replyto = 'prontus@altavoz.net';

    $sub = "[prontus-contacto] $FORM{'tipomsg'} desde $prontus_varglb::IP_SERVER/$prontus_varglb::PRONTUS_ID";

    $str  = "**************************************************\n";
    $str .= "*************** Datos del Prontus ****************\n";
    $str .= "**************************************************\n\n";
    $str .= "Servidor        : $prontus_varglb::IP_SERVER\n";
    $str .= "Prontus ID      : $prontus_varglb::PRONTUS_ID\n";
    $str .= "Ver. Prontus    : $prontus_varglb::VERSION_PRONTUS\n";
    $str .= "Usuario         : $prontus_varglb::USERS_USR\n";
    $str .= "Perfil          : $glosa_perfil\n";
    $str .= "Useragent       : $useragent\n\n";
    $str .= "**************************************************\n";
    $str .= "**************** Datos del Mensaje ***************\n";
    $str .= "**************************************************\n\n";
    $str .= "Nombre          : $FORM{'nombre'}\n";
    $str .= "Email           : $FORM{'email'}\n";
    $str .= "Empresa         : $FORM{'empresa'}\n" if ($FORM{'empresa'} ne '');
    $str .= "Cargo           : $FORM{'cargo'}\n" if ($FORM{'cargo'} ne '');
    $str .= "Telefono        : $FORM{'telefono'}\n" if ($FORM{'telefono'} ne '');
    $str .= "Motivo          : $FORM{'tipomsg'}\n";
    $str .= "Disponibilidad  : $FORM{'disponibilidad'}\n";
    $str .= "Asunto          : $FORM{'asunto'}\n";
    $str .= "Texto           :\n\n$FORM{'mensaje'}\n";

    #print STDERR $str;
    &lib_mail::mail_text($from, $to, $replyto, $sub, $str, 0, $prontus_varglb::SERVER_SMTP);
    &glib_html_02::print_json_result(1, "Su mensaje ha sido enviado al Equipo Prontus.\n\nGracias.", 'exit=1,ctype=1');

};

sub get_nomfile {
    my $real_path = shift;
    my $nomfile;
    my $ext;

    if ($real_path =~ /(\/|\\)?([^\/\\]+?)(\.\w+)$/) {
        $nomfile = lc $2;
        $ext = lc $3; # ext con punto
    };
    $ext = '.xxx' if ($ext eq '');

    $nomfile =~ tr/\xe1\xe9\xed\xf3\xfa\xc1\xc9\xcd\xd3\xda\xd1\xf1\x20\xfc\xdc/aeiouaeiounn_uu/;
    $nomfile =~ s/\W/_/sg;
    return ($nomfile,$ext);
};
