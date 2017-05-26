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
# ---------------------------------------------------------------
# 1.0.0 - 24/05/2017 - JOR - Primera versión
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
    $FORM{'path_conf'}  = &glib_cgi_04::param('_path_conf');
    $FORM{'relfoto'}    = &glib_cgi_04::param('relfoto');
    $FORM{'wfoto'}      = &glib_cgi_04::param('w');
    $FORM{'hfoto'}      = &glib_cgi_04::param('h');
    $FORM{'active'}     = &glib_cgi_04::param('active');
    $FORM{'ts'}         = &glib_cgi_04::param('ts');

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
    my $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/editor_imag/prontus_editor_imag.html"; #_20110119
    my $pagina = &glib_fildir_02::read_file($plantilla);

    $pagina = &lib_prontus::set_coreplt_ppal($pagina);

    # Se parsean variables
    $pagina =~ s/%%_path_conf%%/$FORM{'path_conf'}/sg;
    $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/ig;
    $pagina =~ s/%%_relfoto%%/$FORM{'relfoto'}/ig;
    $pagina =~ s/%%_wfoto%%/$FORM{'wfoto'}/ig;
    $pagina =~ s/%%_hfoto%%/$FORM{'hfoto'}/ig;
    $pagina =~ s/%%active%%/$FORM{'active'}/ig;
    $pagina =~ s/%%ts%%/$FORM{'ts'}/ig;

    print $pagina;
};
