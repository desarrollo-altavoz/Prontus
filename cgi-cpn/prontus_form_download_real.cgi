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
# 1.0.3 - 19/01/2016 - JOR - Se soluciona bug en csv, no aparecia ruta a archivos adjuntos.
#
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

use strict;

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();

use glib_fildir_02;
use glib_html_02;
use glib_cgi_04;

use lib_prontus;
use lib_form;

use Encode qw(decode encode);
use JSON;
use Data::Dumper;

# variables globales
my %FORM;
my $CSV;

main: {
    my $PRONTUS   = $ARGV[0];
    my $TS        = $ARGV[1];

    if($PRONTUS eq '' || ! -d "$prontus_varglb::DIR_SERVER/$PRONTUS") {
        print STDERR "Directorio Prontus no es v�lido [$PRONTUS]\n";
        exit;
    }

    # Carga variables de configuracion.
    my $PATH_CONF = "/$PRONTUS/cpan/$PRONTUS.cfg";
    $PATH_CONF = &lib_prontus::ajusta_pathconf($PATH_CONF);
    &lib_prontus::load_config($PATH_CONF);  # Prontus 6.0

    # Se comprueba que venga el TS del art�culo
    if($TS !~ /\d{14}/) {
        print STDERR "El par�metro ts no es v�lido [$TS]\n";
        exit;
    };

    # Se revisa que el archivo de "orden" exista
    my $DIRFORM     = "/$PRONTUS/cpan/procs/form/$TS";

    if (! -d "$prontus_varglb::DIR_SERVER$DIRFORM") {
        print STDERR "No existe el directorio de datos [$prontus_varglb::DIR_SERVER$DIRFORM]\n";
        exit;
    }

    my $status_file = "$prontus_varglb::DIR_SERVER$DIRFORM/status.json";

    &glib_fildir_02::write_file($status_file, '{"status":1, "msg":"procesando"}');

    my $ORDERFILE  = "order.json";
    my $BACKUPFILE  = "backup.csv";
    if (!(-f "$prontus_varglb::DIR_SERVER$DIRFORM/$ORDERFILE")) {
        if (!(-f "$prontus_varglb::DIR_SERVER$DIRFORM/$BACKUPFILE")) {
        # Si el order no existe, se  revisa que el archivo de respaldo exista
            print STDERR "El archivo de datos est� vac�o o no existe\n";
            &glib_fildir_02::write_file($status_file, '{"status":2, "msg": "error al generar archivo de descarga"}');
            exit;
        };
        $CSV = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$DIRFORM/$BACKUPFILE");
    } else {
        my $jsonorder = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$DIRFORM/$ORDERFILE");
        my $orderhashref;
        if($JSON::VERSION =~ /^1\./) {
            my $json = new JSON;
            $orderhashref = $json->jsonToObj($jsonorder);
        } else {
            $orderhashref = &JSON::from_json($jsonorder);
        }
        my %orderhash = %$orderhashref;

        my @orderreal;
        push(@orderreal, '_fecha');
        push(@orderreal, '_hora');
        push(@orderreal, '_ip');
        foreach my $index (sort { $a <=> $b} keys %orderhash) {
            push(@orderreal, $orderhash{$index});
        }

        my %newheader;
        my $newheaderorder = 0;

        my @files =  &glib_fildir_02::lee_dir("$prontus_varglb::DIR_SERVER$DIRFORM");
        my %orderreal_values;
        foreach my $file (sort @files) {

            next unless($file =~ /\d{14}\.json$/);
            my $json = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$DIRFORM/$file");
            next if ($json !~ /^\{.*\}$/);

            # quita caracteres encodeados como codigo unicode ya que no son visibles y causan problemas de compatibilidad
            $json =~ s/\\u[0-9a-fA-F]{4}//g;

            my $jsonhashref;
            if($JSON::VERSION =~ /^1\./) {
                my $jsonobj = new JSON;
                eval { $jsonhashref = $jsonobj->jsonToObj($json); }
            } else {
                eval { $jsonhashref = &JSON::from_json($json); }
            }

            if ($@) {
                print STDERR "Error al decodificar json $@, file[$file] json:[$json]\n";
                next;
            }
            my %jsonhash = %$jsonhashref;
            my $filesref = $jsonhash{'_files'};

            delete $jsonhash{'_files'};

            # Se recorren seg�n el orden
            foreach my $name (@orderreal) {
                $CSV = $CSV . &lib_form::add_to_csv($jsonhash{$name});
                delete $jsonhash{$name};
            }

            # Lo que no estaba antes, se agrega ahora y se agrega al orden
            %orderreal_values = map {$_ => 1 } @orderreal;
            foreach my $name (sort keys %jsonhash) {
                $CSV = $CSV . &lib_form::add_to_csv($jsonhash{$name});
                push(@orderreal, $name) if (!$orderreal_values{$name});
            }

            # Se agregan los archivos si es que hay.
            if ($filesref) {
                my %files = %{$filesref};

                foreach my $fieldname (keys %files) {
                    my $ruta = "http://$prontus_varglb::CPAN_SERVER_NAME$files{$fieldname}";
                    $CSV = $CSV . &lib_form::add_to_csv($ruta);
                    if (!exists $newheader{$fieldname}) {
                        $newheaderorder++;
                        $newheader{$fieldname} = $newheaderorder;
                    }
                }
            }
            $CSV =~ s/$lib_form::SEPARADOR$/\n/;
        }

        foreach my $name (sort { $newheader{$a} <=> $newheader{$b} } keys %newheader) {
            push(@orderreal, $name) if (!$orderreal_values{$name});
        }

        splice(@orderreal,0,3,'Fecha','Hora','IP');
        my $headers = &lib_form::array_to_csv(@orderreal);
        $CSV = $headers . "\n". $CSV;
    }

    # reconvertimos a utf8 para eliminar caracteres invalidos
    my $characters = decode('UTF-8', $CSV, Encode::FB_DEFAULT);
    $CSV     = encode('UTF-8', $characters, Encode::FB_DEFAULT);

    # el texto no es utf8, al aplicar las operaciones previas se pierde la decodificacion
    utf8::decode($CSV);
    #~ $CSV =~ s/\x{2028}//g;
    # elimina caracteres especiales unicode
    $CSV =~ s/[\x{fff0}-\x{ffff}]//g;
    utf8::encode($CSV);

    # Encodeamos a latin1 si est� configurado asi.
    if($prontus_varglb::FORM_CSV_CHARSET eq 'iso-8859-1') {
        # el texto no es utf8, al aplicar las operaciones previas se pierde la decodificacion
        utf8::decode($CSV);
        # eliminamos caracters no iso-8859-1, > U+00FF
        $CSV =~ s/[\x{00ff}-\x{ffff}]//g;
        utf8::encode($CSV);

        my $oct = decode("UTF-8", $CSV);
        $CSV = encode("iso-8859-1", $oct, Encode::FB_DEFAULT);
    }

    my $filename = "prontus_form$TS.csv";
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$DIRFORM/$filename", $CSV);
    &glib_fildir_02::write_file($status_file, '{"status":0, "msg": "", "path": "'."$DIRFORM/$filename".'"}');
}
