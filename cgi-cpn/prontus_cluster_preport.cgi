#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# Copia portada prontus especificada del prontus_noticias a un directorio especial (online)
# desde donde queda disponible para el sitio web visible.

# 1.1 - 24/02/2003 - ALD - Agrega procesamiento de includes en directorio destino.
# 1.2 - 10/2004 - ycc - Adpatacion para nuevo publicador de noticias version 2.
# 1.3 - 07/2007 - ycc - Adpatacion para nuevo publicador lanacion 2007

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use glib_cgi_04;
use glib_hrfec_02;
use lib_prontus;
use prontus_varglb; &prontus_varglb::init();

main:{
    &glib_cgi_04::new();

    $FORM{'edic'} = &glib_cgi_04::param('_edic');
    $FORM{'port'} = &glib_cgi_04::param('_port');
    $FORM{'prontus_id'} = &glib_cgi_04::param('_prontus_id');

    if (!&lib_prontus::valida_prontus($FORM{'prontus_id'})) {
        print STDERR "Prontus no valido";
        exit;
    }

    $path_conf = "/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);

    # Carga variables de configuracion.
    &lib_prontus::load_config($path_conf);  # Prontus 6.0

    # user check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    $FORM{'edic'} =~ s/[^\/\w]+//g;
    $FORM{'port'} =~ s/[^\w\.]+//g;

    if ($FORM{'edic'} eq '' || $FORM{'port'} eq '') {
        &glib_html_02::print_json_result(0, "Error", 'exit=1,ctype=1');
    }

    # Clustering
    my $fullpath_port = "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/site/edic/$FORM{'edic'}/port/$FORM{'port'}";
    use FindBin '$Bin';
    my $rutaScript = $Bin;

    my $cmd = "$rutaScript/prontus_cluster_port.cgi $fullpath_port &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;

    print "Location: ../$FORM{'prontus_id'}/cpan/core/prontus_cluster_preport_confirm.html\n\n";
}
