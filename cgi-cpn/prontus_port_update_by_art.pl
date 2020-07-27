#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

use strict;
use utf8;

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();

use lib_prontus;
use lib_artic;

main: {
    &lib_prontus::setUtf8();
    if (scalar @ARGV < 1) {
        print "Parámetros insuficientes. Modo de uso:\n";
        print "perl prontus_port_update_by_art.pl <path_completo_a_html_articulo>, por ejemplo:\n";
        print "perl prontus_port_update_by_art.pl /var/www/misitio.cl/web/miprontus/site/artic/20121029/pags/20121029134513.html\n";
        exit;
    }

    # Ruta hacia el Archivo del Artículo (por ejemplo, /var/www/misitio.cl/web/miprontus/site/artic/20121029/pags/20121029134513.html)
    my $fullpath_art = $ARGV[0];

    my $fechac;
    my $marca_video;
    my $video = '';
    my $ts ='';
    # se usa | como delimitador para facilitar la regexp
    if ($fullpath_art =~ m|/([^\/]+?)/site/artic/\d{8}/pags/(\d{14})\.\w+|) {
        $prontus_varglb::PRONTUS_ID = $1;
        $ts = $2;
    } else {
        print STDERR "Error al leer el TS del artículo [$fullpath_art]\n";
        exit;
    }

    if ($prontus_varglb::PRONTUS_ID eq '' || !&lib_prontus::valida_prontus($prontus_varglb::PRONTUS_ID)) {
        print STDERR "El identificador de prontus es inválido\n";
    }

    # Configuracion de Variables
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($prontus_varglb::PRONTUS_ID);
    my $pathconf = &lib_prontus::ajusta_pathconf($relpath_conf);
    &lib_prontus::load_config($pathconf);

    &lib_prontus::actualizar_portadas_byartic($ts, 'ALTA_CONTROL');
}
