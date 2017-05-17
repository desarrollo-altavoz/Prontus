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

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use glib_cgi_04;
use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;

use strict;

my (%FORM);

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');

    # Deduce path conf del referer, en caso de no ser suministrado.
    $FORM{'path_conf'} = &get_path_conf() if ($FORM{'path_conf'} eq '');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'path_conf'});
    $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # $FORM{'tab'} = &glib_cgi_04::param('tab');

    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);

    print "Content-Type: text/html\n\n";
    # Generar pagina final (loopeando una fila modelo)
    my $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/prontus_editor_img.html"; #_20110119
    my $pagina = &glib_fildir_02::read_file($plantilla);

    $pagina = &lib_prontus::set_coreplt_ppal($pagina);

    # Se parsean variables
    $pagina =~ s/%%_path_conf%%/$FORM{'path_conf'}/sg;
    $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/ig;

    my $version = $prontus_varglb::VERSION_PRONTUS;
    $version =~ s/^(\d+)\.(\d+)\.\d+.+$/\1_\2/;

    $pagina =~ s/%%_url_manual_desa%%/$url_manual_desa/ig;
    $pagina =~ s/%%_url_manual_oper%%/$url_manual_oper/ig;

    print $pagina;


};
