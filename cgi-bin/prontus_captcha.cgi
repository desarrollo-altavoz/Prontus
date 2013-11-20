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
# Este captcha es chequeado luego por prontus_form.cgi (campo _CAPTCHA_FORM)
# Si no hay GD, no se valida el captcha

# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# No registra
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde cualquier formulario para posting de articulos prontus, incluyendo
# el tag de la imagen de la sgte forma:
# <input type="text" name="_CAPTCHA_FORM">
# <img src="/cgi-bin/prontus_captcha.cgi?_type=form" border="0" width="80" height="35" valign="bottom">

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
  require 'dir_cgi.pm';
  my ($ROOTDIR) = $ENV{'DOCUMENT_ROOT'};  # desde el web
  $ROOTDIR .= '/' . $DIR_CGI_CPAN;
  unshift(@INC,$ROOTDIR); # Para dejar disponibles las librerias
};

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use lib_ipcheck;
use glib_html_02;
use lib_captcha;
use lib_maxrunning;
use glib_cgi_04;
require 'dir_cgi.pm';
$lib_captcha::TTF = $ENV{'DOCUMENT_ROOT'} . "/$DIR_CGI_CPAN/fontcaptcha.ttf"; # OBLIGATORIO, para los scripts que estan fuera del cgi-cpn

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
main: {

    &glib_cgi_04::new();
    my $nocache = &glib_cgi_04::param('_nocache');
    if ($nocache) {
        print "Cache-Control: no-cache\n";
        print "Cache-Control: max-age=0\n";
        print "Cache-Control: no-store\n";
    };

    # Soporta un maximo de 500 copias corriendo.
    my $counter = 1;
    my $maxExcedido = 0;
    while($counter <= 3) {
        if (&lib_maxrunning::maxExcedido(500)) {
            $maxExcedido = 1;
        } else {
            $maxExcedido = 0;
            last;
        };
        $counter++;
        sleep(1);
    };
    if($maxExcedido == 1) {
        print "Content-Type: text/html\n\n";
        &glib_html_02::print_pag_result("Error","908-Servidor ocupado.");
        exit;
    };

    # Tipo de captcha
    my $captcha_type = &glib_cgi_04::param('_type');
    if ($captcha_type !~ /^(form|posting|enviar)$/) {
        print "Content-type: image/jpeg\n\n";
        print STDERR "Request invalido, el tipo de captcha no corresponde: captcha_type[$captcha_type]\n";
        exit;
    };

    # Validacion y gestion de ip bloqueada
    my $dir_ip_control = "ip_control_captcha_$captcha_type"; # dentro del prontus_temp
    my $user_ip = $ENV{'REMOTE_ADDR'};
    my $maxrequest_por_ip = 30;
    my $bloqueoip_interval = 60;
    my $bloquear_ip = &lib_ipcheck::check_bloqueo_ip($dir_ip_control, $user_ip, $maxrequest_por_ip, $bloqueoip_interval);
    if ($bloquear_ip) {
        print "Content-type: image/jpeg\n\n";
        print STDERR "Request inhabilitado, la IP ha sido bloqueada: dir_ip_control[$dir_ip_control], user_ip[$user_ip]\n";
        exit;
    };

    # Setea captcha
    my ($img_captcha) = &lib_captcha::set_captcha("captcha_$captcha_type");

    # Imprime captcha
    if ($img_captcha) {
        &lib_captcha::print_img($img_captcha);
    } else {
        print "Content-type: image/jpeg\n\n";
        print STDERR "No se pudo setear captcha type=$captcha_type - ERRCODE[$lib_captcha::ERRCODE][$lib_captcha::ERRGLOSA{$lib_captcha::ERRCODE}]\n";
        exit;
    };
};
# -------------------------------END SCRIPT----------------------

