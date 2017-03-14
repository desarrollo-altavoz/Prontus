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
# PROPOSITO.
# -----------
# Funciones para controlar maximo de instancias de un script en ejecucion

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 1.0.0 - 06/2008 - YCC - Primera version.
# 1.0.1 - 08/2009 - YCC - Mejora conteo de instancias, agregando el grep -v sh -c, para evitar
# interferencias en el conteo al ejecutar un script via crontab
# 1.0.2 - 10/2010 - YCC - Elimina soporte windows.

# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

package lib_maxrunning;

use strict;
# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

# ---------------------------------------------------------------
sub myselfRunning {
# Retorna las copias de del script que se encuentran corriendo.
    my($res) = qx/ps axww | grep $0 | grep -v ' grep ' | grep -v 'sh -c' | wc -l/;
    $res =~ s/\D//gs;
    return $res;
}; # myselfRunning

# ---------------------------------------------------------------
sub maxExcedido {
# Aborta si hay mas de $max copias corriendo.
    my($max) = $_[0];

    if (&myselfRunning() > $max) {
        return 1; # max excedido, abortar
    };

    return 0;
}; # maxRunning
# ---------------------------------------------------------------
# deterimna si un pid esta corriendo o no
# retorna la informacion del PID
sub isRunningPid {
    my $result = `ps -p $_[0] -o args=`;
    return $result;
}

# -------------------------------END LIBRERIA--------------------
return 1;
