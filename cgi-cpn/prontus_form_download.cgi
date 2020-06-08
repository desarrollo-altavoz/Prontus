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

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use utf8;

use prontus_varglb; &prontus_varglb::init();

use glib_fildir_02;
use glib_html_02;
use glib_cgi_04;

use lib_prontus;
use lib_form;

use Encode;
use JSON;
use Data::Dumper;

# variables globales
my %FORM;
my $CSV;

main: {
    # Lee formulario de invocacion y valida las variables.
    %FORM = %{&lib_form::getFormData()};

    my $ROOT      = $ENV{'DOCUMENT_ROOT'};
    my $PRONTUS   = $FORM{'_prontus_id'};
    my $TS        = $FORM{'_ts'};

    &lib_prontus::setUtf8();

    print "Cache-Control: no-cache, must-revalidate\r\n";
    print "Content-type: application/json\r\n\r\n";

    if (!&lib_prontus::valida_prontus($PRONTUS)) {
        &send_error("Directorio Prontus no es v&aacute;lido");
        exit;
    }

    if(! -d "$ROOT/$PRONTUS") {
        &send_error("Directorio Prontus no es v&aacute;lido");
        exit;
    }

    # Carga variables de configuracion.
    my $PATH_CONF = "/$PRONTUS/cpan/$PRONTUS.cfg";
    $PATH_CONF = &lib_prontus::ajusta_pathconf($PATH_CONF);
    &lib_prontus::load_config($PATH_CONF);  # Prontus 6.0

    # Se comprueba que venga el TS del artículo
    if ($TS !~ /\d{14}/) {
        &send_error("El parámetro _ts no es válido");
        exit;
    };

    # Se chequean los permisos
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    &lib_prontus::write_log('Descargar Datos', 'Prontus Form', "TS[$TS]", $prontus_varglb::USERS_USR);

    # Se revisa que el archivo de "orden" exista
    my $DIRFORM     = "/$PRONTUS/cpan/procs/form/$TS";
    if (! -d "$ROOT$DIRFORM") {
        &send_error("No existe el directorio de datos [$DIRFORM]");
        exit;
    }
    my $ORDERFILE  = "order.json";
    my $BACKUPFILE  = "backup.csv";
    if (!(-f "$ROOT$DIRFORM/$ORDERFILE")) {
        # Si el order no existe, se  revisa que el archivo de respaldo exista
        if (!(-f "$ROOT$DIRFORM/$BACKUPFILE")) {
            &send_error('El archivo de datos está vacío o no existe');
            exit;
        };
    }

    # lanzamos el proceso en segundo plano
    system("/usr/bin/perl $ROOT/$prontus_varglb::DIR_CGI_CPAN/prontus_form_download_real.cgi $PRONTUS $TS >/dev/null 2>&1 &");
    print "{\"status\":1, \"msg\":\"procesando\"}";
}

# --------------------------------------------------------------------------------------------------
sub send_error {
    my $error = shift;
    print "{\"status\":0, \"msg\":\"$error\"}";
}
