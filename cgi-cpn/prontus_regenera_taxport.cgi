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
# prontus_regenera_taxport.cgi

# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/.

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Script encargado de regenerar todas las portadas taxonómicas.
# Por un tema de performance, no debe usarse como cron. Debe usarse para eventuales
# migraciones u otros eventos por el estilo.
#
# Se crea este script para reemplazar el antiguo prontus_cron_taxport.cgi sin parámetros,
# ya que por motivos de seguridad y performance, ya no cumple dicha funcion.
#
# $ARGV[0] : Nombre del Prontus (ej. prontus_noticias)
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 15/01/2013 - CVI - Primera Version.
#
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    use FindBin '$Bin';
    unshift(@INC,$Bin); # Para dejar disponibles las librerias
};

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use lib_tax;
use glib_hrfec_02;
use glib_dbi_02;
use glib_cgi_04;
use glib_fildir_02;
use strict;
use DBI;


my ($LOOP, %FORM, $NOM_PRONTUS, %TABLA_TEM, %TABLA_STEM, %TABLA_SECC);
my %NOMBASE_PLTS;
# my %HASH_FILES;
# cd /sites/prontus_development/web/cgi-cpn
# perl /sites/prontus_development/web/cgi-cpn/prontus_cron_taxport.cgi prontus_toolbox
my ($FILASXPAG);

if ( (! -d "$prontus_varglb::DIR_SERVER") || ($prontus_varglb::DIR_SERVER eq '') )  {
    print STDERR "\nError: Document root no valido.\n\nComo primer parametro debe indicar el path fisico al directorio raiz del servidor web, ejemplo: /sites/misitio/web \n";
    exit;
};

$FORM{'prontus'} = $ARGV[0];
if ( (! -d "$prontus_varglb::DIR_SERVER/$FORM{'prontus'}") || ($FORM{'prontus'} eq '')  || ($FORM{'prontus'} =~ /^\//) )  {
    print STDERR "\nError: Directorio del publicador no es válido.";
    print STDERR "\nDebe indicar el nombre del Prontus a procesar (ej: prontus_noticias), como parametro de esta CGI\n";
    exit;
};

# Carga variables de configuracion de prontus.
my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus'});
&lib_prontus::load_config("$prontus_varglb::DIR_SERVER$relpath_conf");

my %LEVELS2TRIGGER;
my %FIDS2PROCESS;

main:{

    my $ini_t = time; # debug
        
    # Se cargan todos los niveles, de manera inteligente
    &cargar_taxports();
    
    #~ foreach my $level (sort keys %LEVELS2TRIGGER) {
    #~     print STDERR "$level\n" if($LEVELS2TRIGGER{$level});
    #~ };
    
    # Se gatillan los procesos taxport    
    &gatillar_procesos();
};

# ---------------------------------------------------------------
sub conecta_db {
    
    # Conectar a BD
    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        print STDERR "ERROR: $msg_err_bd\n";
        exit;
    };
    $base->{mysql_auto_reconnect} = 1;
    #~ $base->{InactiveDestroy} = 1;

    return $base;
};

# ---------------------------------------------------------------
sub cargar_taxports {

    my $base = &conecta_db();

    # precarga tabla de temas en hash global para uso posterior reiterado.
    %TABLA_SECC = &lib_tax::carga_tabla_seccion($base);
    %TABLA_TEM = &lib_tax::carga_tabla_temas($base);
    %TABLA_STEM = &lib_tax::carga_tabla_subtemas($base);
    %FIDS2PROCESS = &get_fids2process($base);
    
    $base->disconnect;

    # secc
    my $pid;
    my (@pid) = (); # PIDs de los procesos hijos.
    foreach my $secc_id (keys %TABLA_SECC) {
        my ($secc_nom, $secc_port, $secc_nom4vistas) = split (/\t\t/, $TABLA_SECC{$secc_id});
        &agregar_taxports_thislevel($secc_id, '', '');
        
        # subtemas
        foreach my $temas_id (keys %TABLA_TEM) {
            my ($temas_nom, $temas_port, $temas_idparent, $temas_nom4vistas) = split (/\t\t/, $TABLA_TEM{$temas_id});
            next unless($secc_id eq $temas_idparent);
            &agregar_taxports_thislevel($secc_id, $temas_id, '');

            # subtemas
            foreach my $subtemas_id (keys %TABLA_STEM) {
                my ($subtemas_nom, $subtemas_port, $subtemas_idparent, $subtemas_nom4vistas) = split (/\t\t/, $TABLA_STEM{$subtemas_id});
                next unless($temas_id eq $subtemas_idparent);
                &agregar_taxports_thislevel($secc_id, $temas_id, $subtemas_id);
            };

        }; # foreach temas
                
    }; # foreach seccs
        
    my @levels = keys %LEVELS2TRIGGER;
    my $totartics = (scalar @levels);
    if($totartics == 0) {
        &agregar_taxports_thislevel('', '', ''); # todas
    };
};

# ---------------------------------------------------------------
sub agregar_taxports_thislevel {
# Genera todas las portadas tax (de la 1..n) correspondientes
# a este nivel taxonomico, para todas las vistas declaradas y fids.

    my ($secc_id, $temas_id, $subtemas_id) = @_;
        
    if($subtemas_id) {
        $LEVELS2TRIGGER{"$secc_id/$temas_id/$subtemas_id"} = 1;
        $LEVELS2TRIGGER{"$secc_id/$temas_id/"} = 0;
        $LEVELS2TRIGGER{"$secc_id//"} = 0;
            
    } elsif($temas_id) {
        if(! exists $LEVELS2TRIGGER{"$secc_id/$temas_id/"}) {
            $LEVELS2TRIGGER{"$secc_id/$temas_id/"} = 1;
            $LEVELS2TRIGGER{"$secc_id//"} = 0;
        }
    } else {
        if(! exists $LEVELS2TRIGGER{"$secc_id//"}) {
            $LEVELS2TRIGGER{"$secc_id//"} = 1;
        }
    };
};

# ---------------------------------------------------------------
sub gatillar_procesos {
        
    use FindBin '$Bin';
    my $rutaScript = $Bin;
    my $pathnice = &lib_prontus::get_path_nice();
    $pathnice = "$pathnice -n19 " if($pathnice);

    foreach my $fid_name (keys %FIDS2PROCESS) { # key = 'fid_general:General(general.php)'

        foreach my $levels (sort keys %LEVELS2TRIGGER) {

            next unless($LEVELS2TRIGGER{$levels});
            my $param_especif_taxport = "$fid_name/$levels";                        
            my $cmd = "$pathnice $rutaScript/prontus_cron_taxport.cgi $prontus_varglb::PRONTUS_ID $param_especif_taxport >/dev/null 2>&1 &";
            print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
            system $cmd;
        }
    }
}
# ---------------------------------------------------------------
sub get_fids2process {
# Obtiene fids para los cuales se generaran portadas taxonomicas.
# Estos son solo los que cuenten con plantilla taxonomica en el dir correspondiente:
# /<_prontus_id>/plantillas/tax/port/<_fid>[-<_mv>]/taxport[_<_seccion>][_<_tema>][_<_subtema>].<ext>
        
    my $base = $_[0];
        
    my %fids;
    my %fidswithtax;
    my $fid;
    
    foreach my $key (keys %prontus_varglb::FORM_PLTS) { # key = 'fid_general:General(general.php)'
        my $fid_name;
        next if ($key !~ /^(\w+) *:/);
        $fid_name = $1;
        $fids{$fid_name} = 1;
    };
    
    my $sql = "select ART_TIPOFICHA from ART where ART_IDSECC1<>0 or ART_IDSECC2<>0 or ART_IDSECC3<>0 group by ART_TIPOFICHA";
    my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($fid));
    while ($salida->fetch) {
        if($fids{$fid}) {
            $fidswithtax{$fid} = 1;
        };
    };

    return %fidswithtax;
};
# -------------------------END SCRIPT----------------------
