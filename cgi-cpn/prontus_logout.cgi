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
# Chequear / conectar un usuario al sistema.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# 2) Desde la pag. de ingreso al Sistema, via boton 'Ingresar'.
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# No registra.
# ---------------------------------------------------------------

# 1.1 - 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.2 - 16/05/2001 - Revision general de detalles de forma.
# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0

# Prontus 8.0 - 23/05/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT--------------------
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

use prontus_varglb; &prontus_varglb::init();

use glib_cgi_04;
use lib_prontus;
use lib_cookies;
use lib_multiediting;

use strict;

# ---------------------------------------------------------------
# MAIN.
# -------------
my (%FORM, $TIPO_PRONTUS, $AREA_MENU, $AREA_CONT, $PRONTUS_KEY);

main: {

    my ($lnk);

    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    $FORM{'_modo'} = &glib_cgi_04::param('_modo');
    
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    &lib_prontus::load_config($FORM{'_path_conf'});   # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    &lib_prontus::cerrar_sesion();

    if($FORM{'_modo'} eq 'ajax') {
        # Se aplica Json
        my $lnk = $prontus_varglb::DIR_CORE . '/prontus_index.html';
        print "Content-Type: text/html\n\n";
        my $respuesta = '{"resp":"1", "url":"'.$lnk.'", "msg":""}';
        print $respuesta;
    } else {
        # 8.0
        $lnk = $prontus_varglb::DIR_CORE . '/prontus_index.html';
        print "Content-Type: text/html\n\n";
        print "<HTML><HEAD><META HTTP-EQUIV=\"refresh\" CONTENT=\"0;URL=$lnk\"></HEAD><BODY></BODY></HTML>";   # 1.1
    };
};


# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
# No hay.
# -------------------------------END SCRIPT----------------------

