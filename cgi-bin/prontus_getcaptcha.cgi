#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibs = $Bin;
    unshift(@INC, $pathLibs);
    require 'dir_cgi.pm';

    $pathLibs =~ s/(\/)[^\/]+$/\1$DIR_CGI_CPAN/;
    unshift(@INC,$pathLibs);
};

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use lib_captcha2;
use lib_ipcheck;
use glib_html_02;
use lib_maxrunning;
use glib_cgi_04;
use glib_fildir_02;


main: {

    # require 'dir_cgi.pm';
    &lib_captcha2::init($ENV{'DOCUMENT_ROOT'}, $DIR_CGI_CPAN);
    #~ $lib_captcha2::DIR_CGI_CPAN = $DIR_CGI_CPAN;

    print "Content-Type: text/plain\n\n";
    &glib_cgi_04::new();

    # Soporta un maximo de n copias corriendo.
    if (&lib_maxrunning::maxExcedido(200)) {
        &lib_captcha2::print_response('', '', '', $lib_captcha2::ERR_MSGS{'MSG_CAPTCHA_BUSY'});
    };

    # Tipo de captcha
    my $captcha_type = &glib_cgi_04::param('_type');
    if(! &lib_captcha2::validar_tipo($captcha_type)) {
        print STDERR "Captcha no valido captcha_type[$captcha_type]\n";
        &lib_captcha2::print_response('', '', '', $lib_captcha2::ERR_MSGS{'MSG_CAPTCHA_TYPE'});
    };

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


    my $make_captcha_img_resp = &lib_captcha2::make_captcha_img($captcha_code_clear, "$full_path_to_img/$captcha_img_name");
    &lib_captcha2::print_response('', '', '', $make_captcha_img_resp) unless($make_captcha_img_resp eq '');
    &lib_captcha2::print_response($captcha_img_name, $path_to_img, $captcha_code_hash, '');

};


