#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

#
# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# CGI encargada de descargar el CSV de respaldo
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 01/04/2013 - CVI - Primera version.
#
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
}


use strict;
use prontus_varglb; &prontus_varglb::init();

use glib_fildir_02;
use glib_html_02;
use glib_cgi_04;

use lib_prontus;
use lib_form;

main: {
    
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
  
    my $ROOT      = $ENV{'DOCUMENT_ROOT'};
    my $PRONTUS   = &glib_cgi_04::param('_prontus_id');     # Nombre del publicador Prontus donde se aloja el formulario.
    my $TS        = &glib_cgi_04::param('_ts');             # Nombre del publicador Prontus donde se aloja el formulario.
    my $FORMAT    = &glib_cgi_04::param('_format');         # Nombre del publicador Prontus donde se aloja el formulario.
    
    if($PRONTUS eq '' || ! -d "$ROOT/$PRONTUS") {
        &send_error("Directorio Prontus no es v&aacute;lido [$PRONTUS]");
        exit;
    }
    
    # Carga variables de configuracion.
    my $PATH_CONF = "/$PRONTUS/cpan/$PRONTUS.cfg";
    $PATH_CONF = &lib_prontus::ajusta_pathconf($PATH_CONF);
    &lib_prontus::load_config($PATH_CONF);  # Prontus 6.0
    
    # Se comprueba que venga el TS del artículo    
    if($TS !~ /\d{14}/) {
        &send_error("El parámetro _ts no es válido");
        exit;
    };
    
    # Se comprueba que venga el formato a descargar
    if($FORMAT eq '') {
        $FORMAT = 'csv';
    
    } elsif($FORMAT !~ /^csv$/) {
        &send_error("El parámetro _format no es válido");
        exit;
    };
    
    # Se revisa que el archivo de respaldo exista
    my $DIRFORM     = "/$PRONTUS/cpan/procs/form/$TS";
    my $BACKUPFILE  = "backup.csv";
    if (!(-d $ROOT . $DIRFORM) || !(-f $ROOT . $DIRFORM . '/' . $BACKUPFILE)) {
        &send_error('El archivo de datos está vacío o no existe');
        exit;
    };

    my $csv = &glib_fildir_02::read_file("$ROOT$DIRFORM/$BACKUPFILE");
    
    # El archivo viene en UTF-8
    print STDERR "$lib_prontus::FORM_CSV_CHARSET\n";
    if($prontus_varglb::FORM_CSV_CHARSET eq 'iso-8859-1') {
        utf8::decode($csv);
    };
    
    print "Content-Type:application/x-download\n"; 
    print "Content-Disposition:attachment;filename=$BACKUPFILE\n\n";
    print $csv;

}

# --------------------------------------------------------------------------------------------------
sub send_error {
    
    my $error = shift;
    
    print "Content-type: text/html\n\n";
    print $error;
}
