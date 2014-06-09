#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO .
# -----------
# Para ser linkeado desde el CPAN. Muestra el XML desde el Prontus
# para facilitar el soporte y revision de sistemas
#
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 10/04/2014 - CVI - Primera version
#
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
# use glib_fildir_02;
# use glib_str_02;
use lib_prontus;
# use glib_html_02;

use glib_cgi_04;

# use DBI;
# use glib_dbi_02;
# use lib_secc;
# use lib_tags;
# use lib_waitlock; # Bloqueos tipo espera.
# use lib_quota;
# use Session;

my $ART_AUTOINC;
my $BD;
my (%ID_SECCIONES, %ID_TEMAS, %ID_SUBTEMAS);

# ---------------------------------------------------------------
# MAIN.
# -------------


# Rescatar parametros recibidos.
&glib_cgi_04::new();
$FORM{'_prontus_id'} = &glib_cgi_04::param('_prontus_id');
$FORM{'_ts'} = &glib_cgi_04::param('_ts');

# Ajusta path_conf para completar path y/o cambiar \ por /
$FORM{'_path_conf'} = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'_prontus_id'});

# Carga variables de configuracion.
&lib_prontus::load_config(&lib_prontus::ajusta_pathconf($FORM{'_path_conf'}));  # Prontus 6.0

# Control de usuarios obligatorio chequeando la cookie contra el dbm.
($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);
if ($prontus_varglb::USERS_ID eq '') {
    &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
};

print "Cache-Control: no-cache\n";
print "Cache-Control: max-age=0\n";
print "Cache-Control: no-store\n";

# Validaciones
if ($FORM{'_ts'} !~ /^\d{14}$/) {
    &glib_html_02::print_pag_result('Error','Articulo indicado no es v&aacute;lido', 1, 'exit=1,ctype=1');
};

my $fechac = substr($FORM{'_ts'}, 0, 8);
my $path_final_xml =   $prontus_varglb::DIR_SERVER .
                    $prontus_varglb::DIR_CONTENIDO .
                    $prontus_varglb::DIR_ARTIC .
                    '/' . $fechac .
                    '/xml/' .
                    $FORM{'_ts'} . 
                    '.xml';

if (! -f $path_final_xml) {
    &glib_html_02::print_pag_result('Error','Articulo indicado no existe ['.$path_final_xml.']', 1, 'exit=1,ctype=1');
};

print "Content-Type: text/xml\n\n";
my $xml = &glib_fildir_02::read_file($path_final_xml);
print $xml;


# -------------------------------END SCRIPT----------------------
