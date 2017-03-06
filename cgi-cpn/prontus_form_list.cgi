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
# Lista los archivos del CSV de respaldo de un formulario Prontus.
#
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# El archivo de datos a eliminar se encuentra en:
# /<prontus>/cpan/procs/form/<ts>/backup.csv
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cgi, usando metodo POST. Los parametros son:
# prontus  - Nombre del directorio Prontus.
# ts       - Timestamp del articulo tipo formulario cuyos datos hay que eliminar.
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# /<prontu>/cpan/fid/msg.html - Plantilla de mensajes de resultado de operaciones.
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 15/07/2010 - CVI - Primera version.
# 1.0.1 - 15/07/2015 - EAG - Se agrega verificacion de contenido a archivos json
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

use JSON;

my %FORM; # Contenido del formulario de invocacion.
my $DIRFORM;
my $ROOT;
my $PRONTUS;
my $TS;

main: {

    my $hashref = &lib_form::getFormData(); # Lee formulario de invocacion y valida las variables.
    %FORM = %$hashref;

    $ROOT      = $ENV{'DOCUMENT_ROOT'};
    $PRONTUS   = $FORM{'_prontus_id'}; # Nombre del publicador Prontus donde se aloja el formulario.
    $TS        = $FORM{'_ts'};      # Nombre del publicador Prontus donde se aloja el formulario.

    if ($PRONTUS eq '') { # Muestra pagina en blanco.
        &lib_form::aborta("Directorio Prontus no especificado.");
    };

    my $PATH_CONF = "/$PRONTUS/cpan/$PRONTUS.cfg";

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $PATH_CONF = &lib_prontus::ajusta_pathconf($PATH_CONF);

    # Carga variables de configuracion.
    &lib_prontus::load_config($PATH_CONF);  # Prontus 6.0
    $PATH_CONF =~ s/^$prontus_varglb::DIR_SERVER//;

    # Se chequean los permisos
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    # print STDERR "($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL)\n";

    print "Content-type: text/html\n\n";

    if ($TS eq '') {
        &glib_html_02::print_pag_result("Listado de Datos", 'Formulario no especificado', 1, '');
        exit;
    };
    my $PLANTILLA = &glib_fildir_02::read_file("$ROOT$prontus_varglb::DIR_CORE/prontus_form_list.html");
    if ($PLANTILLA eq '') { # Muestra pagina en blanco.
        &glib_html_02::print_pag_result("Listado de Datos", 'La Plantilla no existe', 1, '');
        exit;
    };

    if ($prontus_varglb::USERS_ID eq '' || $prontus_varglb::USERS_PERFIL ne 'A') {
        $PLANTILLA =~ s/<!--admin-->.*?<!--\/admin-->//s;
    } else {
        $PLANTILLA =~ s/<!--admin-->//s;
        $PLANTILLA =~ s/<!--\/admin-->//s;
    }

    # Se revisa que el archivo de "orden" exista
    $DIRFORM     = "/$PRONTUS/cpan/procs/form/$TS";
    my $ORDERFILE  = "order.json";
    my $BACKUPFILE  = "backup.csv";
    if (-d "$ROOT$DIRFORM" && -f "$ROOT$DIRFORM/$ORDERFILE") {

        # Se lee el archivo de orden
        my $jsonorder = &glib_fildir_02::read_file("$ROOT$DIRFORM/$ORDERFILE");
        my $orderhashref;
        if($JSON::VERSION =~ /^1\./) {
            my $json = new JSON;
            $orderhashref = $json->jsonToObj($jsonorder);
        } else {
            $orderhashref = &JSON::from_json($jsonorder);
        }
        my %orderhash = %$orderhashref;

        # Se agregan las 3 primeras columnas fijas
        my @orderreal;
        push(@orderreal, '_fecha');
        push(@orderreal, '_hora');
        push(@orderreal, '_ip');
        foreach my $index (sort { $a <=> $b} keys %orderhash) {
            push(@orderreal, $orderhash{$index});
        };

        # Se procesan las filas
        $PLANTILLA =~ /%%loop_row%%(.*?)%%\/loop_row%%/s;
        my $origStr = $1;
        $origStr =~ /%%loop_item%%(.*?)%%\/loop_item%%/s;
        my $itemLoop = $1;
        my $totalStr;
        my $tempStr;
        my $tempStr2;
        my $sumrow;
        my $counter = 0;

        # Se leen los archivos de json (los nuevos primero)
        my @files =  &glib_fildir_02::lee_dir("$ROOT$DIRFORM");
        foreach my $file (sort {$b <=> $a} @files) {

            next unless($file =~ /\d{14}\.json/);
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
            my @CSV_ROW;
            # Se recorren según el orden
            foreach my $name (@orderreal) {
                push (@CSV_ROW, $jsonhash{$name});
                delete $jsonhash{$name};
            }

            # Lo que no estaba antes, se agrega ahora y se agrega al orden
            foreach my $name (sort keys %jsonhash) {
                push (@CSV_ROW, $jsonhash{$name});
                push(@orderreal, $name);
                # undef $jsonhash{$name};
            }

            # Una vez que tenemos la fila CSV, se arma la tabla
            my $tempStr = &procesarFila($itemLoop, @CSV_ROW);
            $tempStr2 = $origStr;
            $tempStr2 =~ s/%%loop_item%%.*?%%\/loop_item%%/$tempStr/gs;
            $totalStr = $totalStr . $tempStr2;

            $counter++;
            last if($counter >= $lib_form::MAX_ROWS);
        }
        # Cuando recorremos todos los archivos reemplazamos
        $PLANTILLA =~ s/%%loop_row%%.*?%%\/loop_row%%/$totalStr/s;

        # Se procesa el header ordenado y recortado
        splice(@orderreal, 0, 3, 'Fecha','Hora','IP');
        $PLANTILLA = &procesarHeader($PLANTILLA, @orderreal);
        $PLANTILLA =~ s/%%_rows_order%%/&uacute;ltimas/g;

    } elsif (-d "$ROOT$DIRFORM" && -f "$ROOT$DIRFORM/$BACKUPFILE") {

        open(BACKUP, $ROOT.$DIRFORM.'/'.$BACKUPFILE);

        # Se procesa el header
        my $row = <BACKUP>;
        my @hash = &strToArray($row);
        $PLANTILLA = &procesarHeader($PLANTILLA, @hash);

        # Se procesan las filas
        $PLANTILLA =~ /%%loop_row%%(.*?)%%\/loop_row%%/s;
        my $origStr = $1;
        $origStr =~ /%%loop_item%%(.*?)%%\/loop_item%%/s;
        my $itemLoop = $1;
        my $totalStr;
        my $tempStr;
        my $tempStr2;
        my $sumrow;
        my $counter = 0;
        while(<BACKUP>) {
            my $newrow = $_;
            if($newrow =~ /";\s*$/) {
                $newrow = $sumrow . $newrow;
                my @hash = &strToArray($newrow);
                my $tempStr = &procesarFila($itemLoop, @hash);
                $tempStr2 = $origStr;
                $tempStr2 =~ s/%%loop_item%%.*?%%\/loop_item%%/$tempStr/gs;
                $totalStr = $totalStr . $tempStr2;
                $sumrow = '';
                $counter++;
                last if($counter >= $lib_form::MAX_ROWS);

            } else {
                $sumrow = $sumrow . $newrow;
            }
        };
        $PLANTILLA =~ s/%%loop_row%%.*?%%\/loop_row%%/$totalStr/s;
        $PLANTILLA =~ s/%%_rows_order%%/primeras/g;

    } else {

        # Si ningun archivo existe, se arroja error
        &glib_html_02::print_pag_result("Listado de Datos", 'El archivo de datos está vacío o no existe', 1, '');
        exit;
    }

    # Se parsean los datos comunes
    $PLANTILLA =~ s/%%_max_rows%%/$lib_form::MAX_ROWS/g;
    $PLANTILLA =~ s/%%_prontus_id%%/$PRONTUS/g;
    $PLANTILLA =~ s/%%_ts%%/$TS/g;
    $PLANTILLA =~ s/%%file_backup%%/$DIRFORM\/$BACKUPFILE/g;
    $PLANTILLA =~ s/%%title%%/Administrar Archivo de Datos/g;
    print $PLANTILLA;
};
########################################
## Funciones
########################################
# --------------------------------------------------------------------------------------------------
sub procesarHeader {

    my ($plantilla, @hash) = (@_);

    $plantilla =~ /%%loop_head%%(.*?)%%\/loop_head%%/s;
    my $plt = $1;

    my $totalStr;
    my $tempStr;
    my $count;
    foreach my $item (@hash) {
        $tempStr = $plt;
        $tempStr =~ s/%%head_name%%/$item/ig;
        $totalStr = $totalStr . $tempStr;
        $count++;
        last if($count >= $lib_form::MAX_COLS);
    };
    $tempStr = $plt;
    $tempStr =~ s/%%head_name%%/Archivos Descargables/ig;
    $totalStr = $totalStr . $tempStr;

    $plantilla =~ s/%%loop_head%%.*?%%\/loop_head%%/$totalStr/s;
    my $colspan = $count + 1;
    $plantilla =~ s/%%_colspan%%/$colspan/gs;
    $plantilla =~ s/%%_max_cols%%/$count/gs;

    return $plantilla;
};

# --------------------------------------------------------------------------------------------------
sub procesarFila {

    my ($plt, @hash) = (@_);

    my @files;
    my $totalStr;
    my $tempStr;
    my $count;
    foreach my $item (@hash) {
        $count++;
        if($count <= $lib_form::MAX_COLS) {
            $tempStr = $plt;
            $tempStr =~ s/%%item_value%%/$item/ig;
            $totalStr = $totalStr . $tempStr;
        };
        my $bfile = &isFile($item);
        if($bfile) {
            push @files, $item;
        };
    };
    my $strFiles;
    foreach my $f (@files) {
        my $name = $f;
        $name =~ s/file_\d+\-\-//;
        $strFiles = $strFiles . '&raquo; <a href="'.$DIRFORM.'/'.$f.'">'.$name.'</a><br/>';
    };
    $tempStr = $plt;
    $tempStr =~ s/%%item_value%%/$strFiles/ig;
    $totalStr = $totalStr . $tempStr;
    return $totalStr;
}

# --------------------------------------------------------------------------------------------------
sub strToArray {

    my $row = $_[0];
    my @hash;
    while($row =~ /"(.*?)";/g) {
        push @hash, $1;
    };
    return @hash;
}

# --------------------------------------------------------------------------------------------------
sub isFile {

    my $item = $_[0];
    if($item =~ /file_\d+\-\-[^\/\\]+?\.\w+/) {
        if(-f $ROOT.$DIRFORM.'/'.$item) {
            return 1;
        };
    };
    return 0;
}
