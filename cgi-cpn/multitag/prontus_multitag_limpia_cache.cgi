#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

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
# PROPOSITO.
# -----------
# Borra todos los archivos generados en el cache de multitag
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# NO
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# solo web
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# Ninguna
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# NINGUNA
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 26/11/2015 - JOR - Primera version.
# 1.1.0 - 23/02/2017 - EAG - Integracion a Prontus
#
# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/[^\/]+$//;
    unshift(@INC,$pathLibsProntus);
};

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use glib_fildir_02;

main: {
    my $prontus_id = $ARGV[0];

    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($prontus_id);
    my $path_conf = &lib_prontus::ajusta_pathconf($relpath_conf);

    # Carga variables de configuracion.
    &lib_prontus::load_config($path_conf);

    my $cache_dir = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_MULTITAG;

    if (!(&glib_fildir_02::check_dir($cache_dir)) ) {
        print STDERR "No se puede crear el directorio de cache para multitag: [$cache_dir]";
    } else {
        unlink(glob("$cache_dir/*.html"));
    }
};
