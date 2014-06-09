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

main:{
    &glib_cgi_04::new();

    $FORM{'edic'} = &glib_cgi_04::param('_edic');
    $FORM{'port'} = &glib_cgi_04::param('_port');
    $FORM{'prontus_id'} = &glib_cgi_04::param('_prontus_id');

    # Clustering
    my $fullpath_port = "$ENV{DOCUMENT_ROOT}/$FORM{'prontus_id'}/site/edic/$FORM{'edic'}/port/$FORM{'port'}";
    use FindBin '$Bin';
    my $rutaScript = $Bin;
    
    my $cmd = "/prontus_cluster_port.cgi $fullpath_port &";
    print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
    system $cmd;
    
    print "Location: ../$FORM{'prontus_id'}/cpan/core/prontus_cluster_preport_confirm.html\n\n";
};
