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
# Genera una imagen (imprime Content-type: image/jpeg) para chequear visualmente.
# Este captcha es chequeado luego por prontus_recordarpass.cgi
# Si no hay GD, no se valida el captcha

# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# No registra
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde la pag. de recordar contrasena:
# /<prontus_dir>/cpan/core/prontus_olvidopass.html
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# No registra.
# ---------------------------------------------------------------

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);
use prontus_varglb; &prontus_varglb::init();

#~ use strict;
#~ use lib_captcha;
use lib_captcha2;
use glib_cgi_04;
use lib_maxrunning;
use lib_ipcheck;
use JSON;

$lib_captcha::MAX_FILES = 20; # OPTATIVO
$lib_captcha::FORECOLOR = '0,61,122'; # OPTATIVO, Color azul prontus.
$lib_captcha::BACKCOLOR = '227,241,251'; # OPTATIVO, Color celeste prontus.

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
main: {

    #~ require 'dir_cgi.pm';
    &lib_captcha2::init($ENV{'DOCUMENT_ROOT'}, $prontus_varglb::DIR_CGI_CPAN);
    #~ $lib_captcha2::DIR_CGI_CPAN = $DIR_CGI_CPAN;

    &glib_cgi_04::new();

    print "Cache-Control: no-cache\n";
    print "Cache-Control: max-age=0\n";
    print "Cache-Control: no-store\n";

    print "Content-Type: text/plain\n\n";

    # Soporta un maximo de n copias corriendo.
    if (&lib_maxrunning::maxExcedido(4)) {
        &lib_captcha2::print_response('', '', '', $lib_captcha2::ERR_MSGS{'MSG_CAPTCHA_BUSY'});
    };

    # Tipo de captcha
    my $captcha_type = 'cpan';

    # Validacion y gestion de ip bloqueada
    my $dir_ip_control = "ip_control_captcha_prontus"; # dentro del prontus_temp
    my $user_ip = $ENV{'REMOTE_ADDR'};
    my $maxrequest_por_ip = 100;
    my $bloqueoip_interval = 60;
    my $bloquear_ip = &lib_ipcheck::check_bloqueo_ip($dir_ip_control, $user_ip, $maxrequest_por_ip, $bloqueoip_interval);
    if ($bloquear_ip) {
        &lib_captcha2::print_response('', '', '', $lib_captcha2::ERR_MSGS{'MSG_CAPTCHA_BLOCKED'});
    };

    my $path_to_img = "$lib_captcha2::PATH_CAPTCHA_IMG/$captcha_type/";
    my $full_path_to_img = "$lib_captcha2::DOCUMENT_ROOT$path_to_img";

    # Garbage collector, borra archivos siempre y cuando el numero de archivos a sido superado.
    &lib_captcha2::garbage_collector($full_path_to_img);

    # Crear directorio de imagenes si no existe.
    &glib_fildir_02::check_dir($full_path_to_img);

    my $captcha_code_clear = &glib_str_02::random_string(4);
    my $captcha_code_hash = &lib_captcha2::make_hash($captcha_code_clear);

    my $captcha_img_name = &lib_captcha2::get_img_name($captcha_code_hash);

    print STDERR "creando imagen en[$full_path_to_img/$captcha_img_name]\n";
    my $make_captcha_img_resp = &lib_captcha2::make_captcha_img($captcha_code_clear, "$full_path_to_img/$captcha_img_name");
    &lib_captcha2::print_response('', '', '', $make_captcha_img_resp) unless($make_captcha_img_resp eq '');

    &lib_captcha2::print_response($captcha_img_name, $path_to_img, $captcha_code_hash, '');
};
# -------------------------------END SCRIPT----------------------

