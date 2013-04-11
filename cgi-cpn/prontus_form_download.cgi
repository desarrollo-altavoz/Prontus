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

use JSON;

my $SEPARADOR = ';';
my $CSV;

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
    
    # Se revisa que el archivo de "orden" exista
    my $DIRFORM     = "/$PRONTUS/cpan/procs/form/$TS";
    my $ORDERFILE  = "order.json";
    my $BACKUPFILE  = "backup.csv";
    if (!(-d "$ROOT$DIRFORM") || !(-f "$ROOT$DIRFORM/$ORDERFILE")) {

        # Si el order no existe, se  revisa que el archivo de respaldo exista
        if (!(-d $ROOT . $DIRFORM) || !(-f $ROOT . $DIRFORM . '/' . $BACKUPFILE)) {
            &send_error('El archivo de datos está vacío o no existe');
            exit;
        };
        $CSV = &glib_fildir_02::read_file("$ROOT$DIRFORM/$BACKUPFILE");

    } else {
        
        my $jsonorder = &glib_fildir_02::read_file("$ROOT$DIRFORM/$ORDERFILE");
        my $orderhashref = &JSON::from_json($jsonorder);
        my %orderhash = %$orderhashref;
        # print "Content-Type:text/html\n\n"; 
        
        my @orderreal;
        push(@orderreal, '_fecha');
        push(@orderreal, '_hora');
        push(@orderreal, '_ip');
        foreach my $index (sort keys %orderhash) {
            push(@orderreal, $orderhash{$index});
        };
        
        my @files =  &glib_fildir_02::lee_dir("$ROOT$DIRFORM");
        # print "Total: $#files<br><hr>";
        foreach my $file (sort @files) {
            
            next unless($file =~ /\d{14}\.json/);
            my $json = &glib_fildir_02::read_file("$ROOT$DIRFORM/$file");
            my $jsonhashref = &JSON::from_json($json);
            my %jsonhash = %$jsonhashref;
            
            # Se recorren según el orden
            foreach my $name (@orderreal) {
                $CSV = $CSV . &add_to_csv($jsonhash{$name});
                delete $jsonhash{$name};
            }
            
            # Lo que no estaba antes, se agrega ahora y se agrega al orden
            foreach my $name (sort keys %jsonhash) {
                $CSV = $CSV . &add_to_csv($jsonhash{$name});
                push(@orderreal, $name);
                # undef $jsonhash{$name};
            }
            $CSV =~ s/$SEPARADOR$/\n/;
        }

        my $total = $#orderreal;
        my $headers;
        $headers = $headers . &add_to_csv('Fecha');
        $headers = $headers . &add_to_csv('Hora');
        $headers = $headers . &add_to_csv('IP');
        for(my $i = 3; $i <= $total; $i++) {
            $headers = $headers . &add_to_csv($orderreal[$i]);
        };
        $headers =~ s/$SEPARADOR$/\n/;
        $CSV = $headers . $CSV;
    }  
    
   
    # El archivo viene en UTF-8
    #~ print STDERR "$lib_prontus::FORM_CSV_CHARSET\n";
    if($prontus_varglb::FORM_CSV_CHARSET eq 'iso-8859-1') {
        utf8::decode($CSV);
    };
    
    print "Content-Type:application/x-download\n"; 
    print "Content-Disposition:attachment;filename=$BACKUPFILE\n\n";
    print $CSV;

}
# --------------------------------------------------------------------------------------------------
sub add_to_csv {
    
    my $data = shift;
    $data = &glib_str_02::trim($data); # Elimina espacios para que no molesten.
    $data =~ s/\"/\'\'/gs; # Convierte comillas para que no arruinen el archivo csv.
    $data =~ s/\r//gs;     # 1.5 Elimina retornos de carro para que no arruinen el archivo csv.
    return "\"$data\"$SEPARADOR";    
};
# --------------------------------------------------------------------------------------------------
sub send_error {
    
    my $error = shift;
    
    print "Content-type: text/html\n\n";
    print $error;
}
