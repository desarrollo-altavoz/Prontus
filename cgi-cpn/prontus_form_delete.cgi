#!/usr/bin/perl
#
# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Elimina el archivod e datos de respaldo de un formulario Prontus.
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
# 1.0 - 16/05/2007 - Primera version.
#
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
}

# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

use strict;
use prontus_varglb; &prontus_varglb::init();

use glib_fildir_02;
use glib_html_02;
use glib_cgi_04;

use lib_prontus;

my %FORM;        # Contenido del formulario de invocacion.

&getFormData(); # Lee formulario de invocacion y valida las variables.

my $ROOT    = $ENV{'DOCUMENT_ROOT'};
my $PRONTUS = $FORM{'prontus'}; # Nombre del publicador Prontus donde se aloja el formulario.
my $TS      = $FORM{'ts'};      # Nombre del publicador Prontus donde se aloja el formulario.

if ($PRONTUS eq '') { # Muestra pagina en blanco.
    &glib_html_02::print_json_result(0, 'Directorio Prontus no especificado', 'exit=1,ctype=1');
};
my $PATH_CONF = "/$PRONTUS/cpan/$PRONTUS.cfg";

# Ajusta path_conf para completar path y/o cambiar \ por /
$PATH_CONF = &lib_prontus::ajusta_pathconf($PATH_CONF);

# Carga variables de configuracion.
&lib_prontus::load_config($PATH_CONF);  # Prontus 6.0
$PATH_CONF =~ s/^$prontus_varglb::DIR_SERVER//;

# Se chequean los permisos
($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

if ($TS eq '') { # Muestra pagina en blanco.
    &glib_html_02::print_json_result(0, 'Formulario no especificado', 'exit=1,ctype=1');
};

my $dirForm = "$ROOT/$PRONTUS/cpan/procs/form/$TS";
if(-d $dirForm) {
    &glib_fildir_02::borra_dir($dirForm);
} else {
    &glib_html_02::print_json_result(0, 'No se pudo eliminar el directorio con los datos', 'exit=1,ctype=1');
};

&glib_html_02::print_json_result(1, 'El archivo de datos de respaldo ha sido eliminado', 'exit=1,ctype=1');

# ###################################################
# Funciones

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

