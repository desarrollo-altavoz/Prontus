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
# SCRIPT.
# -----------
# prontus_regenera_relac.cgi

# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/.

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Script encargado de regenerar los archivos relacioandos.
# Se usa como alternativa a la regeneración masiva de artículos (que al final realiza
# esta accion) ya que es mas rapido que hacer todo el proceso.
#
# $ARGV[0] : Nombre del Prontus (ej. prontus_noticias)
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 02/12/2013 - CVI - Primera Version.
#
# -------------------------------BEGIN SCRIPT--------------------
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
use lib_prontus;
use lib_tax;
use glib_hrfec_02;
use glib_dbi_02;
use glib_cgi_04;
use glib_fildir_02;
use strict;
use DBI;

use lib_maxrunning;

# Soporta sólo 1 copia andando
if (&lib_maxrunning::maxExcedido(1)) {
    print "Error: Servidor ocupado. Intente otra vez mas tarde.\n";
    exit;
};

my $DB;
my %FORM;
my $counter = 0;

main: {

    if ( (! -d "$prontus_varglb::DIR_SERVER") || ($prontus_varglb::DIR_SERVER eq '') )  {
        print STDERR "Error: Document root no valido.\n";
        exit;
    };

    $FORM{'prontus'} = $ARGV[0];
    if ( (! -d "$prontus_varglb::DIR_SERVER/$FORM{'prontus'}") || ($FORM{'prontus'} eq '')  || ($FORM{'prontus'} =~ /^\//) )  {
        print STDERR "\nError: Directorio del publicador no es válido.";
        print STDERR "\nDebe indicar el nombre del Prontus a procesar (ej: prontus_noticias), como parametro de esta CGI\n";
        exit;
    };

    # Carga variables de configuracion de prontus.
    my $path_conf = "/$FORM{'prontus'}/cpan/$FORM{'prontus'}.cfg";
    &lib_prontus::load_config(&lib_prontus::ajusta_pathconf($path_conf));

    # Se conecta a la Base de Datos, si es que no esta conectado
    my $base = &conecta_db();

    my %tabla_secc = &lib_tax::carga_tabla_seccion($base);
    my %tabla_tem = &lib_tax::carga_tabla_temas($base);
    my %tabla_stem = &lib_tax::carga_tabla_subtemas($base);

    my %TAXONOMIAS_TO_REGEN;

    # Para las secciones
    foreach my $seccion (keys %tabla_secc) {
        $TAXONOMIAS_TO_REGEN{$seccion . '_0_0'} = '1';
    }

    # Para los temas
    my %hashtemas;
    foreach my $tema (keys %tabla_tem) {
        if($tabla_tem{$tema} =~ /^(.*?)\t\t(.*?)\t\t(.*?)\t\t/) {
            my $seccion = $3;
            $hashtemas{$tema} = $seccion;
            $TAXONOMIAS_TO_REGEN{$seccion . '_'.$tema.'_0'} = '1';
        }
    }

    # Para los subtemas
    foreach my $subtema (keys %tabla_stem) {
        if($tabla_stem{$subtema} =~ /^(.*?)\t\t(.*?)\t\t(.*?)\t\t/) {
            my $tema = $3;
            my $seccion = $hashtemas{$tema};
            $TAXONOMIAS_TO_REGEN{$seccion . '_'.$tema.'_'.$subtema} = '1';
        }
    }

    &regen_taxonomia(\%TAXONOMIAS_TO_REGEN);
    print "Los articulos relacionados fueron regenerados\n";
    print "Total de niveles procesados: $counter\n";

};
# --------------------------------------------------------------------
sub regen_taxonomia {
# Regenera art. relacionados
    my ($taxonomia) = shift;

    my ($secc, $tem, $stem);
    my ($tripleta);

    &lib_tax::set_vars($prontus_varglb::DIR_CONTENIDO,
                        $prontus_varglb::DIR_ARTIC,
                        $prontus_varglb::DIR_PAG,
                        $prontus_varglb::DIR_TEMP,
                        $prontus_varglb::DIR_TAXONOMIA,
                        $prontus_varglb::NUM_RELAC_DEFAULT,
                        $prontus_varglb::CONTROLAR_ALTA_ARTICULOS);

    foreach $tripleta (keys %$taxonomia) {

        my $base = &conecta_db();

        ($secc, $tem, $stem) = split(/_/, $tripleta);
        $secc = '' if($secc eq '0');
        $tem = '' if($tem eq '0');
        $stem = '' if($stem eq '0');
        print "Regenerando tripleta: $tripleta\n";
        &lib_tax::generar_relacionados($secc, $tem, $stem, $base, '');

        # Ahora parsea art relacionados para MVs
        my $mv;
        foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
            &lib_tax::generar_relacionados($secc, $tem, $stem, $base, $mv);
        };
        $counter++;
    };
};

# ---------------------------------------------------------------
sub conecta_db {

    # Conectar a BD
    if (ref($DB)) {
        return $DB;
    };

    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        print STDERR "ERROR: $msg_err_bd\n";
        exit;
    };
    $base->{mysql_auto_reconnect} = 1;
    #~ $base->{InactiveDestroy} = 1;

    return $base;
};
