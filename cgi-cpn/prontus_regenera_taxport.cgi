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
# 2.0.0 - 15/01/2013 - JOR - Cambia logica del script para hacerlo un poco mas eficiente.
#
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC, $pathLibsProntus);
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


my ($LOOP, %FORM, $NOM_PRONTUS, %TABLA_TEM, %TABLA_STEM, %TABLA_SECC);
my %NOMBASE_PLTS;
my ($FILASXPAG);
my %LEVELS2TRIGGER;
my %FIDS2PROCESS;

$FORM{'prontus'} = $ARGV[0];
$FORM{'fid2process'} = $ARGV[1];

main: {
    if ((!-d "$prontus_varglb::DIR_SERVER") || ($prontus_varglb::DIR_SERVER eq ''))  {
        print "Error: Document root no valido.\n";

        exit;
    }

    if ((!-d "$prontus_varglb::DIR_SERVER/$FORM{'prontus'}") || ($FORM{'prontus'} eq '')  || ($FORM{'prontus'} =~ /^\//))  {
        print "\nError: Directorio del publicador no es valido.";
        print "\nDebe indicar el nombre del Prontus a procesar (ej: prontus_noticias), como parametro de esta CGI\n";

        exit;
    }

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus'});
    &lib_prontus::load_config( &lib_prontus::ajusta_pathconf($relpath_conf) );

    # Se cargan todos los niveles, de manera inteligente
    &cargar_taxports();

    # Se gatillan los procesos de regeneracion.
    &gatillar_procesos();
};

# ---------------------------------------------------------------
sub conecta_db {
    # Conectar a BD
    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();

    if (!ref($base)) {
        print "ERROR: $msg_err_bd\n";

        exit;
    }

    $base->{mysql_auto_reconnect} = 1;

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
            }
        } # foreach temas
    } # foreach seccs

    my @levels = keys %LEVELS2TRIGGER;
    my $totartics = (scalar @levels);

    if ($totartics == 0) {
        &agregar_taxports_thislevel('', '', ''); # todas
    }
};

# ---------------------------------------------------------------
sub agregar_taxports_thislevel {
    # Genera todas las portadas tax (de la 1..n) correspondientes
    # a este nivel taxonomico, para todas las vistas declaradas y fids.
    my ($secc_id, $temas_id, $subtemas_id) = @_;

    if ($subtemas_id) {
        $LEVELS2TRIGGER{"$secc_id/$temas_id/$subtemas_id"} = 1;
        $LEVELS2TRIGGER{"$secc_id/$temas_id/"} = 0;
        $LEVELS2TRIGGER{"$secc_id//"} = 0;

    } elsif($temas_id) {
        if (!exists $LEVELS2TRIGGER{"$secc_id/$temas_id/"}) {
            $LEVELS2TRIGGER{"$secc_id/$temas_id/"} = 1;
            $LEVELS2TRIGGER{"$secc_id//"} = 0;
        }
    } else {
        if (!exists $LEVELS2TRIGGER{"$secc_id//"}) {
            $LEVELS2TRIGGER{"$secc_id//"} = 1;
        }
    }
};

# ---------------------------------------------------------------
sub gatillar_procesos {
    my $rutaScript = $Bin;
    my $pathnice = &lib_prontus::get_path_nice();
    $pathnice = "$pathnice -n19 " if($pathnice);

    foreach my $fid_name (keys %FIDS2PROCESS) { # key = 'fid_general:General(general.php)'
        foreach my $levels (sort keys %LEVELS2TRIGGER) {
            next unless($LEVELS2TRIGGER{$levels});

            while (&check_taxport_running() >= 3) {
                print "Muchos procesos simultaneos... esperando 5 segundos.\n";
                sleep(5);
            }
            while (&check_worker_running() >= ($prontus_varglb::TAXPORT_MAX_WORKERS + 1)) {
                print "Muchos procesos worker simultaneos... esperando 5 segundos.\n";
                sleep(5);
            }

            my $param_especif_taxport = "$fid_name/$levels";
            my $cmd = "$pathnice $rutaScript/prontus_cron_taxport.cgi $prontus_varglb::PRONTUS_ID $param_especif_taxport >/dev/null 2>&1 &";

            print "[" . &glib_hrfec_02::get_dtime_pack4() . "] $cmd\n";

            system $cmd;
        }
    }
}
# ---------------------------------------------------------------
sub check_taxport_running {
    my($res) = qx/ps axww | grep 'prontus_cron_taxport.cgi' | grep -v ' grep ' | grep -v 'sh -c' | wc -l/;

    $res =~ s/\D//gs;
    $res += 0; # para forzar el casteo a numero
    return $res;
};
# ---------------------------------------------------------------
sub check_worker_running {
    my($res) = qx/ps axww | grep 'prontus_cron_taxport_worker.cgi' | grep -v ' grep ' | grep -v 'sh -c' | wc -l/;

    $res =~ s/\D//gs;
    $res += 0; # para forzar el casteo a numero
    return $res;
};
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
    }

    my $sql = "select ART_TIPOFICHA from ART where ART_IDSECC1<>0 or ART_IDSECC2<>0 or ART_IDSECC3<>0 group by ART_TIPOFICHA";
    my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($fid));

    while ($salida->fetch) {
        if ($fids{$fid}) {
            $fidswithtax{$fid} = 1;
        }
    }

    # Si viene por parametro el fid, se utiliza solo ese.
    if ($FORM{'fid2process'}) {
        if (!defined $fids{$FORM{'fid2process'}}) {
            print "ERROR: El FID [$FORM{'fid2process'}] no existe en la configuracion de Prontus.\n";
            exit;
        }

        if (defined $fidswithtax{$FORM{'fid2process'}}) {
            return ($FORM{'fid2process'} => 1);
        } else {
            print "ERROR: No hay articulos con taxonomia con FID [$FORM{'fid2process'}].\n";
            exit;
        }
    }

    return %fidswithtax;
};
# -------------------------END SCRIPT----------------------
