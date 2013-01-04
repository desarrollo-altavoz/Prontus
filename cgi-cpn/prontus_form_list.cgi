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


# --------------------------------------

my $MAX_COLS = 5; # Numero maximo de columnas que se desplegarán

# --------------------------------------


my %FORM; # Contenido del formulario de invocacion.

&getFormData(); # Lee formulario de invocacion y valida las variables.

my $ROOT      = $ENV{'DOCUMENT_ROOT'};
my $PRONTUS   = $FORM{'_prontus_id'}; # Nombre del publicador Prontus donde se aloja el formulario.
my $TS        = $FORM{'_ts'};      # Nombre del publicador Prontus donde se aloja el formulario.

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

my $DIRFORM     = "/$PRONTUS/cpan/procs/form/$TS";
my $BACKUPFILE  = "backup.csv";
if (!(-d $ROOT . $DIRFORM) || !(-f $ROOT . $DIRFORM . '/' . $BACKUPFILE)) { # Muestra pagina en blanco.
    &glib_html_02::print_pag_result("Listado de Datos", 'El archivo de datos está vacío', 1, '');
    exit;
};

# &glib_html_02::print_pag_result("Eliminar datos", 'El archivo de datos de respaldo ha sido eliminado', 1, '');
$PLANTILLA =~ s/%%_prontus_id%%/$PRONTUS/g;
$PLANTILLA =~ s/%%_ts%%/$TS/g;
$PLANTILLA =~ s/%%file_backup%%/$DIRFORM\/$BACKUPFILE/g;

open(BACKUP, $ROOT.$DIRFORM.'/'.$BACKUPFILE);

# Se procesa el header
$PLANTILLA =~ /%%loop_head%%(.*?)%%\/loop_head%%/s;
my $header = $1;
my $row = <BACKUP>;
$header = &procesarHeader($row, $header);
$PLANTILLA =~ s/%%loop_head%%.*?%%\/loop_head%%/$header/s;

my $colspan = $MAX_COLS + 1;
$PLANTILLA =~ s/%%_colspan%%/$colspan/gs;
$PLANTILLA =~ s/%%_max_cols%%/$MAX_COLS/gs;


# Se procesan las filas
$PLANTILLA =~ /%%loop_row%%(.*?)%%\/loop_row%%/s;
my $origStr = $1;
$origStr =~ /%%loop_item%%(.*?)%%\/loop_item%%/s;
my $itemLoop = $1;
my $totalStr;
my $tempStr;
my $tempStr2;
my $sumrow;
while(<BACKUP>) {
    my $newrow = $_;
    if($newrow =~ /";\s*$/) {
        $newrow = $sumrow . $newrow;
        my $tempStr = &procesarFila($newrow, $itemLoop);
        $tempStr2 = $origStr;
        $tempStr2 =~ s/%%loop_item%%.*?%%\/loop_item%%/$tempStr/gs;
        $totalStr = $totalStr . $tempStr2;
        $sumrow = '';
    } else {
        $sumrow = $sumrow . $newrow;
    }
};
$PLANTILLA =~ s/%%loop_row%%.*?%%\/loop_row%%/$totalStr/s;

print $PLANTILLA;



########################################
## Funciones
########################################

# -------------------------------------------------------------------#
sub procesarHeader {

    my ($row, $plt) = ($_[0], $_[1]);
    my @hash = &strToArray($row);
    my $totalStr;
    my $tempStr;
    my $count;
    foreach my $item (@hash) {
        $tempStr = $plt;
        $tempStr =~ s/%%head_name%%/$item/ig;
        $totalStr = $totalStr . $tempStr;
        $count++;
        last if($count >= $MAX_COLS);
    };
    if($count < $MAX_COLS) {
        $MAX_COLS = $count;
    };
    $tempStr = $plt;
    $tempStr =~ s/%%head_name%%/Archivos Descargables/ig;
    $totalStr = $totalStr . $tempStr;
    return $totalStr;
};

# -------------------------------------------------------------------#
#
sub procesarFila {

    my ($row, $plt) = ($_[0], $_[1]);
    my @hash = &strToArray($row);
    my @files;
    my $totalStr;
    my $tempStr;
    my $count;
    foreach my $item (@hash) {
        $count++;
        if($count <= $MAX_COLS) {
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

# -------------------------------------------------------------------#
sub strToArray {

    my $row = $_[0];
    my @hash;
    while($row =~ /"(.*?)";/g) {
        push @hash, $1;
    };
    return @hash;
}

# -------------------------------------------------------------------#
sub isFile {

    my $item = $_[0];
    if($item =~ /file_\d+\-\-[^\/\\]+?\.\w+/) {
        if(-f $ROOT.$DIRFORM.'/'.$item) {
            return 1;
        };
    };
    return 0;
}

# -------------------------------------------------------------------#
# Rescata y valida las variables del chorro.
sub getFormData {
    my($pair,$buffer);
    if ($ENV{'REQUEST_METHOD'} eq 'GET') {
        $buffer = $ENV{'QUERY_STRING'};
    } else {
        read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
    };
    my(@pairs) = split(/&/, $buffer);
    foreach $pair (@pairs) {
        my($name, $value) = split(/=/,$pair);
        # Un-Webify plus signs and %-encoding
        $value =~ tr/+/ /;
        $value =~ s/%([0-9A-Ha-h]{2})/pack("c",hex($1))/ge;
        # 1.9 $value =~ s/~!/ ~!/g;
        $value =~ s/\.\.\///g; # 1.4 Elimina toda referencia de directorios hacia atras.
        # 1.9 $value =~ s/\|//g;     # 1.4 Elimina toda posibilidad de activar pipes.
        $value =~ s/\x00//g;   # 1.4 Elimina nulls.
        $value =~ s/\x1B//g;   # 1.4 Elimina escapes.
        $value =~ s/[<>%!\|\\\~\$]/ /g; # 1.9 Elimina caracteres peligrosos
        # $value =~ s/[\+\.\^\$\(\)\[\]\{\}\|\\]//g;   # 1.8 Elimina caracteres reservados de Perl.
        $name = lc $name; # 1.3
        $FORM{$name} = $value;
    };
    # Valida variables.
    $FORM{'ts'} =~ s/[^\d]//g; # Elimina todos los no-numeros.
    $FORM{'prontus'} =~ s/[^\w\.\-]//g; # Elimina caracteres no validos como nombres de prontus.
    # print "<p>FILTROACTIVO = $FILTROACTIVO $FORMfechaini $FORMfechafin"; # debug
}; # getFormData
