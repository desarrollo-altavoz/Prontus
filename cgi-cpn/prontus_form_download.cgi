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
# 1.0.1 - 04/06/2015 - EAG - Se restringen archivos a solo ".json"
# 1.0.2 - 15/07/2015 - EAG - Se agrega verificacion de contenido a archivos json
#
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

use strict;
use prontus_varglb; &prontus_varglb::init();

use glib_fildir_02;
use glib_html_02;
use glib_cgi_04;

use lib_prontus;
use lib_form;

use Encode;
use JSON;

my %FORM;
my $CSV;

main: {

    # Lee formulario de invocacion y valida las variables.
    my $hashref = &lib_form::getFormData();
    %FORM = %$hashref;

    my $ROOT      = $ENV{'DOCUMENT_ROOT'};
    my $PRONTUS   = $FORM{'_prontus_id'};
    my $TS        = $FORM{'_ts'};
    my $FORMAT    = $FORM{'_format'};

    if($PRONTUS eq '' || ! -d "$ROOT/$PRONTUS") {
        &send_error(&lib_language::_msg_prontus('_invalid_prontus_directory')." [$PRONTUS]");
        exit;
    }

    # Carga variables de configuracion.
    my $PATH_CONF = "/$PRONTUS/cpan/$PRONTUS.cfg";
    $PATH_CONF = &lib_prontus::ajusta_pathconf($PATH_CONF);
    &lib_prontus::load_config($PATH_CONF);  # Prontus 6.0

    # Se comprueba que venga el TS del artículo
    if($TS !~ /\d{14}/) {
        &send_error(&lib_language::_msg_prontus('_the_parameter')" _ts ".&lib_language::_msg_prontus('_invalid'));
        exit;
    };

    # Se comprueba que venga el formato a descargar
    if($FORMAT eq '') {
        $FORMAT = 'csv';

    } elsif($FORMAT !~ /^csv$/) {
        &send_error(&lib_language::_msg_prontus('_the_parameter')." ".&lib_language::_msg_prontus('_invalid'));
        exit;
    };

    # Se revisa que el archivo de "orden" exista
    my $DIRFORM     = "/$PRONTUS/cpan/procs/form/$TS";
    my $ORDERFILE  = "order.json";
    my $BACKUPFILE  = "backup.csv";
    if (!(-d "$ROOT$DIRFORM") || !(-f "$ROOT$DIRFORM/$ORDERFILE")) {

        # Si el order no existe, se  revisa que el archivo de respaldo exista
        if (!(-d $ROOT . $DIRFORM) || !(-f $ROOT . $DIRFORM . '/' . $BACKUPFILE)) {
            &send_error(&lib_language::_msg_prontus('_data_file_empty_or_no_exist'));
            exit;
        };
        $CSV = &glib_fildir_02::read_file("$ROOT$DIRFORM/$BACKUPFILE");

    } else {

        my $jsonorder = &glib_fildir_02::read_file("$ROOT$DIRFORM/$ORDERFILE");
        my $orderhashref;
        if($JSON::VERSION =~ /^1\./) {
            my $json = new JSON;
            $orderhashref = $json->jsonToObj($jsonorder);
        } else {
            $orderhashref = &JSON::from_json($jsonorder);
        }
        my %orderhash = %$orderhashref;
        # print "Content-Type:text/html\n\n";

        my @orderreal;
        push(@orderreal, '_fecha');
        push(@orderreal, '_hora');
        push(@orderreal, '_ip');
        foreach my $index (sort { $a <=> $b} keys %orderhash) {
            push(@orderreal, $orderhash{$index});
        };

        my @files =  &glib_fildir_02::lee_dir("$ROOT$DIRFORM");
        # print "Total: $#files<br><hr>";
        foreach my $file (sort @files) {

            next unless($file =~ /\d{14}\.json$/);
            my $json = &glib_fildir_02::read_file("$ROOT$DIRFORM/$file");
            next if ($json !~ /^\{.*\}$/);
            my $jsonhashref;
            if($JSON::VERSION =~ /^1\./) {
                my $jsonobj = new JSON;
                $jsonhashref = $jsonobj->jsonToObj($json);
            } else {
                $jsonhashref = &JSON::from_json($json);
            }
            my %jsonhash = %$jsonhashref;

            # Se recorren según el orden
            foreach my $name (@orderreal) {
                $CSV = $CSV . &lib_form::add_to_csv($jsonhash{$name});
                delete $jsonhash{$name};
            }

            # Lo que no estaba antes, se agrega ahora y se agrega al orden
            foreach my $name (sort keys %jsonhash) {
                $CSV = $CSV . &lib_form::add_to_csv($jsonhash{$name});
                push(@orderreal, $name);
                # undef $jsonhash{$name};
            }
            $CSV =~ s/$lib_form::SEPARADOR$/\n/;
        }

        splice(@orderreal,0,3,'Fecha','Hora','IP');
        my $headers = &lib_form::array_to_csv(@orderreal);
        $CSV = $headers . "\n". $CSV;
    }

    # Se hace esto para que no se caiga la funcion con strings muy largos
    if($prontus_varglb::FORM_CSV_CHARSET eq 'iso-8859-1') {
        my $oct = decode("utf8", $CSV);
        $CSV = encode("iso-8859-1", $oct);
    };

    print STDOUT "Content-Type:application/x-download\n";
    print STDOUT "Content-Disposition:attachment;filename=$BACKUPFILE\n\n";

    binmode STDOUT, ":raw";
    print STDOUT $CSV;

}

# --------------------------------------------------------------------------------------------------
sub send_error {

    my $error = shift;

    print "Content-type: text/html\n\n";
    print $error;
}
