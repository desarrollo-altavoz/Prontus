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
# prontus_cron_taxport.cgi

# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/.

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Geenerar portadas taxonomicas en modo batch, todas de una vez.
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------
# No registra

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# como cron, con lo sgtes. params:
# $ARGV[0] : Nombre del prontus (ej. prontus_noticias)
# $ARGV[1] : s/t/st a procesar, optativo
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# Plantillas:
# /<_prontus_id>/plantillas/tax/port/(all|<_fid>)[-<_mv>]/taxport[_<_seccion>][_<_tema>][_<_subtema>].<ext>

# + all           : Aca van las plantillas por defecto.
# + <_fid>        : Aca van las plantillas que se utilizaran en caso de que se indique filtro
#                   por un tipo de art. especifico, ademas de la taxonomia.
#                   Si no hay plantillas en la carpeta <fidname>, entonces se utilizan las de 'all'
# + <_seccion>,
#   <_tema>,
#   <_subtema>    : son optativos, sirven para utilizar una plantilla especifica para un nivel
#                   taxonomico especifico. El caso simple es taxport.<ext>
# + -<_mv>        : optativo, para configurar plantillas distintas para cada vista

# Determinacion de la plantilla a usar:
# Se busca primero la plantilla mas especifica y si no se encuentra se va bajando hasta
# llegar a la plantilla basica .../all/taxport.html


# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# /<prontus_dir>/site/tax/port/(all|<fidname>)[-<vista>]/<s>_<t>_<st>_<nropag>.<ext>
# <s>, <t>, <st>: ids de taxonomia, siempre van, si alguno no aplica, se pone un 0 (cero).
# <nropag>      : Nro. de pagina de resultados [1..n]



# ---------------------------------------------------------------
# Tablas.
# ------------------------
# BD: la configurada en Prontus. Tablas: 'ART', 'SECC', 'TEMAS', 'SUBTEMAS'
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 05/2007 - YCH - Primera Version.

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
use glib_hrfec_02;
use glib_dbi_02;
use glib_cgi_04;
use glib_fildir_02;
use Artic;
use lib_tax;
use lib_maxrunning;
use strict;
use DBI;
use lib_stdlog;
use Time::HiRes qw(usleep);
&lib_stdlog::set_stdlog($0, 51200);

close STDOUT;
# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my %ART_XML_FIELDS;
my %ART_XDATA_FIELDS;
    

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
$FORM{'params_especif'} = $ARGV[1]; # optativo: fid/s/t/st para generar solo para esa taxonomia y fid

($FORM{'fid_especif'}, $FORM{'seccion_especif'}, $FORM{'tema_especif'}, $FORM{'subtema_especif'}) = split (/\//, $FORM{'params_especif'});

&valida_param();

# Carga variables de configuracion de prontus.
my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus'});
&lib_prontus::load_config("$prontus_varglb::DIR_SERVER$relpath_conf");

#~ print STDERR "[$$] param0: $ARGV[0], param1: $ARGV[1]\n";

my ($RELDIR_ARTIC) = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/%%DIRFECHA%%$prontus_varglb::DIR_PAG";
my ($RELDIR_PORT_DST) = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_PTEMA";
my ($RELDIR_PORT_TMP) = "$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_PTEMA";
my (%EXT_PORT_TMP, %BUF_PLT, %BUF_PLT_LOOP, %MSGS, %LOADED_NAMES_PLT);
my ($CURR_DTIME) = &glib_hrfec_02::get_dtime_pack4();


#if (&lib_maxrunning::maxExcedido(1)) {
#  die "[$CURR_DTIME] prontus_cron_taxport en proceso, se aborta ejecucion de [prontus_cron_taxport.cgi $FORM{'prontus'} $FORM{'params_especif'}]\n";
#}

my $COUNTER_TOTAL_PAGS = 0;

# $prontus_varglb::TAXPORT_MAXARTICS = 500; # debug
use Time::HiRes qw ( time ); # debug

main:{
    my $ini_t = time; # debug
    $FILASXPAG = $prontus_varglb::TAXPORT_ARTXPAG;
    # $FILASXPAG = 3; # debug
    &generar_taxports();
    my $delta_t = time - $ini_t;
    # print STDERR "prontus_cron_taxport.cgi - [$$] exec_time[$delta_t], paginas_escritas[$COUNTER_TOTAL_PAGS]\n\n"; # debug

    # Eliminar semaforos para este pid.
    my $dir_semaf = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/taxport_smf";
    my $pid_propio = $$;
    my @files2delete = glob("$dir_semaf/*" . ".$pid_propio");
    foreach my $todelete (@files2delete) {
        unlink $todelete;
    };
    
};

# ---------------------------------------------------------------
sub renovar_semaforos {
# Escribe los semaforos de los id levels q va a utilizar (en realidad solo cambia el fid)
# y borra los escritos por otros procesos para este mismo level, para provocar q aborten
    my ($secc_id, $temas_id, $subtemas_id, $ref_hash) = @_;
    my %fids2process = %$ref_hash;

    my $dir_semaf = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/taxport_smf";
    &glib_fildir_02::check_dir($dir_semaf) if (! -d $dir_semaf);
    my $pid_propio = $$;

            
    # si se invoca sin fid, considera el filtro sin fid
    $fids2process{''} = 1 if ($FORM{'fid_especif'} eq '');

    # para uso normal desde el fid, en donde se invoca siempre con fid. Entonces si viene una tax definida, genera para esa tax con el fid, pero tb. para la tax sin fid especifico
    $fids2process{''} = 1 if ($FORM{'seccion_especif'});
    
    foreach my $fid (keys %fids2process) {
        # Nivel superior.
        my $id_level =  '____' . $fid;
        my @files2delete = glob("$dir_semaf/$id_level" . '.*');
        foreach my $file2delete (@files2delete) {
            if ($file2delete !~ /\.$pid_propio$/) {
                unlink $file2delete;
                print STDERR "\n[$$] hice abortar al: $file2delete !\n";
            };
        };
        &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');

        # Solo seccion, todos los temas y todos los subtemas de los temas.
        # Genera s/*/*
        if ($secc_id && !$temas_id && !$subtemas_id) {
            # Seccion.
            my $id_level = $secc_id . '___' . $fid;
            my @files2delete = glob("$dir_semaf/$id_level" . '.*');
            foreach my $file2delete (@files2delete) {
                if ($file2delete !~ /\.$pid_propio$/) {
                    unlink $file2delete;
                    print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                };
            };
            &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');

            # Todos los temas y subtemas para la seccion.
            # Temas.
            #~ my ($temas_nom, $temas_port, $temas_idparent, $temas_nom4vistas);
            #~ foreach my $temaid (keys %TABLA_TEM) {
                #~ print STDERR "temas_idparent[$temas_idparent] == secc_id[$secc_id]\n";
                #~ ($temas_nom, $temas_port, $temas_idparent, $temas_nom4vistas) = split (/\t\t/, $TABLA_TEM{$temaid});
                #~ if ($temas_idparent == $secc_id) {
                    #~ print STDERR "temas_idparent[$temas_idparent] == secc_id[$secc_id], nom[$temas_nom], temaid[$temaid]\n";
                    #~ my $id_level = $secc_id . '_' . $temaid . '__' . $fid;
                    #~ print STDERR "level[$id_level]\n";
                    #~ my @files2delete = glob("$dir_semaf/$id_level" . '.*');
                    #~ foreach my $file2delete (@files2delete) {
                        #~ if ($file2delete !~ /\.$pid_propio$/) {
                            #~ unlink $file2delete;
                            #~ print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                        #~ };
                    #~ };
                    #~ &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
                    #~ # Subtemas.
                    #~ my ($subtemas_nom, $subtemas_port, $subtemas_idparent, $subtemas_nom4vistas);
                    #~ foreach my $subtemaid (keys %TABLA_STEM) {
                        #~ ($subtemas_nom, $subtemas_port, $subtemas_idparent, $subtemas_nom4vistas) = split (/\t\t/, $TABLA_STEM{$subtemaid});
                        #~ if ($subtemas_idparent == $temaid) {
                            #~ my $id_level = $secc_id . '_' . $temaid . '_' . $subtemaid . '_' . $fid;
                            #~ print STDERR "level[$id_level]\n";
                            #~ my @files2delete = glob("$dir_semaf/$id_level" . '.*');
                            #~ foreach my $file2delete (@files2delete) {
                                #~ if ($file2delete !~ /\.$pid_propio$/) {
                                    #~ unlink $file2delete;
                                    #~ print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                                #~ };
                            #~ };
                            #~ &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
                        #~ };
                    #~ };
                #~ };
            #~ };
        }; # end solo seccion.

        # Solo seccion y tema y todos los subtemas del tema.
        # Genera s/t/*
        if ($secc_id && $temas_id && !$subtemas_id) {
            # Seccion.
            my $id_level = $secc_id . '___' . $fid;
            my @files2delete = glob("$dir_semaf/$id_level" . '.*');
            foreach my $file2delete (@files2delete) {
                if ($file2delete !~ /\.$pid_propio$/) {
                    unlink $file2delete;
                    print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                };
            };
            &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
            
            # Tema.
            my $id_level = $secc_id . '_' . $temas_id . '__' . $fid;
            my @files2delete = glob("$dir_semaf/$id_level" . '.*');
            foreach my $file2delete (@files2delete) {
                if ($file2delete !~ /\.$pid_propio$/) {
                    unlink $file2delete;
                    print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                };
            };
            &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
            
            # Todos los subtemas para el tema.
            #~ my ($subtemas_nom, $subtemas_port, $subtemas_idparent, $subtemas_nom4vistas);
            #~ foreach my $subtemaid (keys %TABLA_STEM) {
                #~ ($subtemas_nom, $subtemas_port, $subtemas_idparent, $subtemas_nom4vistas) = split (/\t\t/, $TABLA_STEM{$subtemaid});
                #~ if ($subtemas_idparent == $temas_id) {
                    #~ my $id_level = $secc_id . '_' . $temas_id . '_' . $subtemaid . '_' . $fid;
                    #~ my @files2delete = glob("$dir_semaf/$id_level" . '.*');
                    #~ foreach my $file2delete (@files2delete) {
                        #~ if ($file2delete !~ /\.$pid_propio$/) {
                            #~ unlink $file2delete;
                            #~ print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                        #~ };
                    #~ };
                    #~ &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
                #~ };
            #~ };
        }; # end solo seccion y tema.

        # Seccion, tema y subtema
        # Genera s/t/st
        if ($secc_id && $temas_id && $subtemas_id) {
            # Seccion.
            my $id_level = $secc_id . '___' . $fid;
            my @files2delete = glob("$dir_semaf/$id_level" . '.*');
            foreach my $file2delete (@files2delete) {
                if ($file2delete !~ /\.$pid_propio$/) {
                    unlink $file2delete;
                    print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                };
            };
            &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
            
            # Tema.
            my $id_level = $secc_id . '_' . $temas_id . '__' . $fid;
            my @files2delete = glob("$dir_semaf/$id_level" . '.*');
            foreach my $file2delete (@files2delete) {
                if ($file2delete !~ /\.$pid_propio$/) {
                    unlink $file2delete;
                    print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                };
            };
            &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
            
            # Subtema.
            my $id_level = $secc_id . '_' . $temas_id . '_' . $subtemas_id . '_' . $fid;
            my @files2delete = glob("$dir_semaf/$id_level" . '.*');
            foreach my $file2delete (@files2delete) {
                if ($file2delete !~ /\.$pid_propio$/) {
                    unlink $file2delete;
                    print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                };
            };
            &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
        }; # end seccion, tema y subtema.

        # No hay seccion.
        # Genera todo */*/*
        if (!$secc_id) {
           foreach my $seccid (keys %TABLA_SECC) {
                my $id_level = $seccid . '___' . $fid;
                #~ print STDERR "level[$id_level]\n";
                my @files2delete = glob("$dir_semaf/$id_level" . '.*');
                foreach my $file2delete (@files2delete) {
                    if ($file2delete !~ /\.$pid_propio$/) {
                        unlink $file2delete;
                        print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                    };
                };
                &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
                # Todos los temas y subtemas para la seccion.
                # Temas.
                my ($temas_nom, $temas_port, $temas_idparent, $temas_nom4vistas);
                foreach my $temaid (keys %TABLA_TEM) {
                    #~ print STDERR "temas_idparent[$temas_idparent] == secc_id[$secc_id]\n";
                    ($temas_nom, $temas_port, $temas_idparent, $temas_nom4vistas) = split (/\t\t/, $TABLA_TEM{$temaid});
                    if ($temas_idparent == $seccid) {
                        #~ print STDERR "temas_idparent[$temas_idparent] == secc_id[$secc_id], nom[$temas_nom], temaid[$temaid]\n";
                        my $id_level = $seccid . '_' . $temaid . '__' . $fid;
                        #~ print STDERR "level[$id_level]\n";
                        my @files2delete = glob("$dir_semaf/$id_level" . '.*');
                        foreach my $file2delete (@files2delete) {
                            if ($file2delete !~ /\.$pid_propio$/) {
                                unlink $file2delete;
                                print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                            };
                        };
                        &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
                        # Subtemas.
                        my ($subtemas_nom, $subtemas_port, $subtemas_idparent, $subtemas_nom4vistas);
                        foreach my $subtemaid (keys %TABLA_STEM) {
                            ($subtemas_nom, $subtemas_port, $subtemas_idparent, $subtemas_nom4vistas) = split (/\t\t/, $TABLA_STEM{$subtemaid});
                            if ($subtemas_idparent == $temaid) {
                                my $id_level = $seccid . '_' . $temaid . '_' . $subtemaid . '_' . $fid;
                                #~ print STDERR "level[$id_level]\n";
                                my @files2delete = glob("$dir_semaf/$id_level" . '.*');
                                foreach my $file2delete (@files2delete) {
                                    if ($file2delete !~ /\.$pid_propio$/) {
                                        unlink $file2delete;
                                        print STDERR "\n[$$] hice abortar al: $file2delete !\n";
                                    };
                                };
                                &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
                            };
                        };
                    };
                };
            };
            
        }; # end no hay seccion.
        
        my $id_level = '___' . $fid;
        my @files2delete = glob("$dir_semaf/$id_level" . '.*');
        foreach my $file2delete (@files2delete) {
            if ($file2delete !~ /\.$pid_propio$/) {
                unlink $file2delete;
                print STDERR "\n[$$] hice abortar al: $file2delete !\n";
            };
        };
        &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
    };
        
};

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
sub generar_taxports {

    my $base = &conecta_db();

    # precarga tabla de temas en hash global para uso posterior reiterado.
    %TABLA_SECC = &lib_tax::carga_tabla_seccion($base);
    %TABLA_TEM = &lib_tax::carga_tabla_temas($base);
    %TABLA_STEM = &lib_tax::carga_tabla_subtemas($base);

    $base->disconnect;

    &carga_nombase_plts();

    my %fids2process = &get_fids2process();

    # print STDERR "\nMI PID: $$\n";
    
    # Escribe los semaforos de los id levels q va a utilizar (en realidad solo cambia el fid)
    # y borra los escritos por otros procesos para este mismo level, para provocar q aborten
    &renovar_semaforos($FORM{'seccion_especif'}, $FORM{'tema_especif'}, $FORM{'subtema_especif'}, \%fids2process);
    
    &generar_taxports_thislevel('', '', '', '', \%fids2process, $base); # todas
        
    if (($FORM{'seccion_especif'}) || ($FORM{'params_especif'} eq '')) {

        # secc
        my ($secc_id, $secc_nom, $secc_port, $secc_nom4vistas);
        my $pid;
        my (@pid) = (); # PIDs de los procesos hijos.
        foreach $secc_id (keys %TABLA_SECC) {

            ($secc_nom, $secc_port, $secc_nom4vistas) = split (/\t\t/, $TABLA_SECC{$secc_id});
            if ($FORM{'seccion_especif'}) {
                next if ($FORM{'seccion_especif'} != $secc_id);
            };

            if ($FORM{'seccion_especif'}) {
                &generar_taxports_thislevel($secc_id, '', '', $secc_port, \%fids2process, $base);
            }
            
            my ($temas_id, $temas_nom, $temas_port, $temas_idparent, $temas_nom4vistas);
            foreach $temas_id (keys %TABLA_TEM) {
                ($temas_nom, $temas_port, $temas_idparent, $temas_nom4vistas) = split (/\t\t/, $TABLA_TEM{$temas_id});
                next if ($temas_idparent != $secc_id);
                if ($FORM{'tema_especif'}) {
                    next if ($FORM{'tema_especif'} != $temas_id);
                };

                if ($FORM{'tema_especif'}) {
                    &generar_taxports_thislevel($secc_id, $temas_id, '', $temas_port, \%fids2process, $base);
                }
                
                # subtemas
                my ($subtemas_id, $subtemas_nom, $subtemas_port, $subtemas_idparent, $subtemas_nom4vistas);
                foreach $subtemas_id (keys %TABLA_STEM) {
                    ($subtemas_nom, $subtemas_port, $subtemas_idparent, $subtemas_nom4vistas) = split (/\t\t/, $TABLA_STEM{$subtemas_id});
                    next if ($subtemas_idparent != $temas_id);
                    if ($FORM{'subtema_especif'}) {
                        next if ($FORM{'subtema_especif'} != $subtemas_id);
                    };          
                    if ($FORM{'subtema_especif'}) {
                        &generar_taxports_thislevel($secc_id, $temas_id, $subtemas_id, $subtemas_port, \%fids2process, $base);
                    }
                };

            }; # foreach temas
        }; # foreach seccs

    };

    #~ $base->disconnect;


};


# ---------------------------------------------------------------
sub get_tpl_tema {
# Obtiene nombre del q sera el tpl de la portada tipo tema, es el primer archivo q se encuentre.
    my ($ruta_dir) = $_[0];
    my (@lisdir, $k);

    @lisdir = &glib_fildir_02::lee_dir($ruta_dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

    foreach $k (@lisdir) {
        if (-f "$ruta_dir/$k") {
            return $k;
        };
    };
    return '';
};

# ---------------------------------------------------------------
sub generar_taxports_thislevel {
# Genera todas las portadas tax (de la 1..n) correspondientes
# a este nivel taxonomico, para todas las vistas declaradas y fids.


    my ($secc_id, $temas_id, $subtemas_id, $tax_fixedurl, $ref_hash, $base) = @_;

    my %fids2process = %$ref_hash;
    # si se invoca sin fid, considera el filtro sin fid
    $fids2process{''} = 1 if ($FORM{'fid_especif'} eq '');

    # para uso normal desde el fid, en donde se invoca siempre con fid. Entonces si viene una tax definida, genera para esa tax con el fid, pero tb. para la tax sin fid especifico
    $fids2process{''} = 1 if ($FORM{'seccion_especif'});

    my $dir_semaf = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/taxport_smf";
    &glib_fildir_02::check_dir($dir_semaf) if (! -d $dir_semaf);
    my $pid_propio = $$;

    foreach my $fid (keys %fids2process) {
        my $id_level = $secc_id . '_' . $temas_id . '_' . $subtemas_id . '_' . $fid;
        if (! -f "$dir_semaf/$id_level.$pid_propio") {
            print STDERR "prontus_cron_taxport.cgi - [$$] PROCESAR LEVEL[$id_level] hasta aca no mas llegamos!\n";
            next;
        };
        my $base = &conecta_db();
        
        my $filtros = &genera_filtros_taxports($secc_id, $temas_id, $subtemas_id, $fid, $CURR_DTIME);
        my $tot_artics = &get_tot_artics($filtros, $base);
        print STDERR "[$$] PROCESANDO LEVEL [$secc_id, $temas_id, $subtemas_id, $fid] - tot[$tot_artics]\n"; # - filtro[$filtros]\n";
        my ($secc_nom, $filler) = split (/\t\t/, $TABLA_SECC{$secc_id});

        my $sql = "select ART_ID, ART_FECHAP, ART_HORAP, ART_TITU, "
        . "ART_DIRFECHA, ART_EXTENSION, ART_TIPOFICHA, ART_IDTEMAS1, ART_BAJA from ART "
        . "%%FILTRO%% order by $prontus_varglb::TAXPORT_ORDEN LIMIT 0, $prontus_varglb::TAXPORT_MAXARTICS";

        if ($filtros ne '') {
            $sql =~ s/%%FILTRO%%/ where $filtros /;
        }
        else {
            $sql =~ s/%%FILTRO%%/$filtros/;
        };

        my $salida = &glib_dbi_02::ejecutar_sql($base, $sql);
        my $nro_filas = 0;
        my $nro_pag = 0;
        my %filas;

        my $arrayref = $salida->fetchall_arrayref;
        $salida->finish;
        $base->disconnect;
        
        foreach my $row (@{$arrayref}) {
            my $art_id = $row->[0];
            my $art_fecha = $row->[1];
            my $art_horap = $row->[2];
            my $art_titu = $row->[3];
            my $art_dirfecha = $row->[4];
            my $art_extension = $row->[5];
            my $art_tipoficha = $row->[6];
            my $art_idtemas1 = $row->[7];
            my $art_baja = $row->[8];
            
            $nro_filas++;
            if (-f "$dir_semaf/$id_level.$pid_propio") {
                my $nro_pag_to_write = $nro_pag + 1;
                # print STDERR "\r                   pag[$nro_pag_to_write] row[$nro_filas]";
                # sleep (1) if ($nro_filas > 98);
            } else {
                # print STDERR "\n[$$] FETCHING: hasta aca no mas llegamos!\n";
                return;
            };


            # parsea esta fila en todas las multivistas
            my ($tem, $filler1, $filler2) = split (/\t\t/, $TABLA_TEM{$art_idtemas1});
            my $mv;
            my %vistas; # incluye las mv y la normal
            %vistas = %prontus_varglb::MULTIVISTAS;
            $vistas{''} = 1; # vista default
            foreach $mv (keys %vistas) {
                foreach my $nombase_plt (keys %NOMBASE_PLTS) {
                    
                    # Obtiene plantilla, de acuerdo al nivel taxonomico especificado, fid y mv
                    my $loop_plt = &get_loop_plt($secc_id, $temas_id, $subtemas_id, $fid, $mv, $nombase_plt);
                    next if (!$loop_plt);
                    my $fila_content;
                    my ($auxref, $auxref2);
                    
                    # En estos casos sólo es válida la primera página
                    my $key_hash = "$secc_id|$temas_id|$subtemas_id|$fid|$mv|$nombase_plt";
                    if($BUF_PLT{$key_hash} =~ /%%_no_paginar%%/ && $nro_pag > 1) {
                        next;
                    };

                    ($fila_content, $auxref, $auxref2) = &lib_tax::generar_fila($RELDIR_ARTIC, $art_id, $art_extension, $loop_plt, $nro_filas, $tot_artics, $ART_XML_FIELDS{$art_id}, $ART_XDATA_FIELDS{$art_id});

                    $ART_XML_FIELDS{$art_id} = $auxref if (! exists $ART_XML_FIELDS{$art_id}); # para no leer 2 veces un xml
                    $ART_XDATA_FIELDS{$art_id} = $auxref2 if (! exists $ART_XDATA_FIELDS{$art_id}); # para no leer las xdata 2 veces
                    

                    $filas{"$mv|$nombase_plt"} .= $fila_content;

                    if ($nro_pag > 0) {
                        # Se baja a medio segundo
                        usleep(500000);
                    };
                };
            };
            
            # escribir la pag actual y cambiar a la pagina siguiente
            if ($nro_filas >= $FILASXPAG) {
                
                $nro_pag++; # avanza pag
                &write_pag($tax_fixedurl, $fid, $secc_nom, $tot_artics, $nro_pag, $secc_id, $temas_id, $subtemas_id, \%filas);
                $nro_filas = 0; # resetea conta de filas para empezar del ppio en la pagina que viene.
                %filas = ();
            };
        };


        $nro_pag++; # avanza pag
        &write_pag($tax_fixedurl, $fid, $secc_nom, $tot_artics, $nro_pag, $secc_id, $temas_id, $subtemas_id, \%filas);

        if (-f "$dir_semaf/$id_level.$pid_propio") {
            unlink "$dir_semaf/$id_level.$pid_propio";
            print STDERR "[$$] PROCESAR LEVEL[$id_level] proceso completado OK!\n";
        };
    };
    
};
# ---------------------------------------------------------------
sub get_loop_plt {
# Obtiene buffer del loop del tpl de la portada tipo tema, de acuerdo a s, t y st + fid y mv.

    my ($secc_id, $temas_id, $subtemas_id, $fid, $mv, $nombase_plt) = @_;

    # Si fue cargado el tpl, lo retorna
    my $key_hash = "$secc_id|$temas_id|$subtemas_id|$fid|$mv|$nombase_plt";
    return $BUF_PLT_LOOP{$key_hash} if ($BUF_PLT_LOOP{$key_hash});


    # Si no, lo obtiene.
    my $plt = &obtiene_plt($secc_id, $temas_id, $subtemas_id, $fid, $mv, $nombase_plt);

    return '' if (!$plt);
    # print STDERR "determinando plt para s[$secc_id]t[$temas_id]st[$subtemas_id]fid[$fid]mv[$mv] -> plt[$plt]\n";

    if ($LOADED_NAMES_PLT{$plt}) { # si ya fue leida esta plt para algun otro key_hash, lo saco de ahi
        my $key_hash_anterior = $LOADED_NAMES_PLT{$plt};
        $BUF_PLT_LOOP{$key_hash} = $BUF_PLT_LOOP{$key_hash_anterior};
        $BUF_PLT{$key_hash} = $BUF_PLT{$key_hash_anterior};
        return $BUF_PLT_LOOP{$key_hash};
    };

    my $buffer = &glib_fildir_02::read_file($plt);
    my $dirmacros = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_PTEMA_MACROS";
    #~ print "dirmacros: $dirmacros\n";
    $buffer = &lib_prontus::add_macros($buffer, $dirmacros) if(-d $dirmacros);
    my $loop;
    if ($buffer =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
        $loop = $1;
    };
    # Carga en ram plantillas
    $BUF_PLT_LOOP{$key_hash} = $loop;
    $BUF_PLT{$key_hash} = $buffer;
    $LOADED_NAMES_PLT{$plt} = $key_hash;
    return $loop;

};

# ---------------------------------------------------------------
sub get_buffer_plt {
# Obtiene buffer del tpl de la portada tipo tema, de acuerdo a s, t y st.

    my ($secc_id, $temas_id, $subtemas_id, $fid, $mv, $nombase_plt) = @_;

    # Si fue cargado el tpl, lo retorna
    my $key_hash = "$secc_id|$temas_id|$subtemas_id|$fid|$mv|$nombase_plt";
    return $BUF_PLT{$key_hash} if ($BUF_PLT{$key_hash});

    # Si no, lo obtiene.
    my $plt = &obtiene_plt($secc_id, $temas_id, $subtemas_id, $fid, $mv, $nombase_plt);
    return '' if (!$plt);

    # si ya fue leida esta plt para algun otro key_hash, lo saco de ahi para no leer de nuevo de FS
    if ($LOADED_NAMES_PLT{$plt}) {
        my $key_hash_anterior = $LOADED_NAMES_PLT{$plt};
        $BUF_PLT_LOOP{$key_hash} = $BUF_PLT_LOOP{$key_hash_anterior};
        $BUF_PLT{$key_hash} = $BUF_PLT{$key_hash_anterior};
        return $BUF_PLT{$key_hash};
    };

    my $buffer = &glib_fildir_02::read_file($plt);
    my $dirmacros = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_PTEMA_MACROS";
    #~ print "dirmacros: $dirmacros\n";
    $buffer = &lib_prontus::add_macros($buffer, $dirmacros) if(-d $dirmacros);
    my $loop;
    if ($buffer =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
        $loop = $1;
    };
    # Carga en ram plantillas
    $BUF_PLT_LOOP{$key_hash} = $loop;
    $BUF_PLT{$key_hash} = $buffer;
    $LOADED_NAMES_PLT{$plt} = $key_hash;

    return $buffer;

};


# ---------------------------------------------------------------
sub obtiene_plt {
# Obtiene nombre del q sera el tpl de la portada tipo tema, de acuerdo a s, t y st.
#  O sea, si taxonomia de entrada es:
#  seccion=sN
#  tema=tN
#  subtema=stN
#  Se busca si existe una plantilla que se llame taxport_sN_tN_stN.html
#  Si no existe, se busca taxport_sN_tN.html
#  Si no existe, se busca taxport_sN.html
#  Si no existe, se usa taxport.html
# La plantilla es del tipo:
# /<_prontus_id>/plantillas/tax/port/(all|<_fid>)[-<_mv>]/taxport[_<_seccion>][_<_tema>][_<_subtema>].<ext>

    my ($secc_id, $temas_id, $subtemas_id, $fid, $mv, $nombase_plt) = @_;


    my ($dir_plt) = "$prontus_varglb::DIR_SERVER$RELDIR_PORT_TMP";
    # Obtiene extension (con punto) de la plantilla a usar.
    my ($nombase, $ext_port_tmp) = &lib_prontus::split_nom_y_extension($nombase_plt);
    $ext_port_tmp = '.' . $ext_port_tmp;

    # deja guardada la extension de la plantilla, para usarla al grabar la pagina.
    my $key_hash = "$secc_id|$temas_id|$subtemas_id|$fid|$mv|$nombase_plt";
    $EXT_PORT_TMP{$key_hash} = $ext_port_tmp;

    my ($plt);
    # Intenta obtener plantilla para filtro por fid
    if ($fid) {
        my $dir_plt_fid = $dir_plt . "/$fid";
        if ($mv) {
            my $dir_plt_fid_vista = $dir_plt_fid . '-' . $mv;
            $plt = &obtienePltPorTax($secc_id, $temas_id, $subtemas_id, $dir_plt_fid_vista, $ext_port_tmp, $nombase);

            return $plt if (-f $plt);
            # return ''; # si no hay plantilla para la vista, retorna vacio
        } else {
            $plt = &obtienePltPorTax($secc_id, $temas_id, $subtemas_id, $dir_plt_fid, $ext_port_tmp, $nombase);
            return $plt if ( -f $plt);
        };
    };

    # Ahora la intenta obtener sin filtro de fid
    my $dir_plt_all = $dir_plt . '/all';

    if ($mv) {
        # Intenta con la vista
        my $dir_plt_all_vista = $dir_plt_all . '-' . $mv;
        $plt = &obtienePltPorTax($secc_id, $temas_id, $subtemas_id, $dir_plt_all_vista, $ext_port_tmp, $nombase);
        return $plt if (-f $plt);
        return ''; # si no hay plantilla para la vista, retorna vacio
    } else {
        # intenta obtener plantilla estandar
        $plt = &obtienePltPorTax($secc_id, $temas_id, $subtemas_id, $dir_plt_all, $ext_port_tmp, $nombase);
        return $plt if (-f $plt);
    };

    # No se enontro ninguna plantilla
    return '';

};


# ---------------------------------------------------------------
sub carga_nombase_plts {
# Obtiene nombres de las multiples plantillas, las lee siempre del /all

    my ($ruta_dir) = "$prontus_varglb::DIR_SERVER$RELDIR_PORT_TMP/all";
    my @lisdir = &glib_fildir_02::lee_dir($ruta_dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..


    foreach my $k (@lisdir) {
        if ((-f "$ruta_dir/$k") && ($k =~ /^([a-z]+\.\w+)$/)) {
            $NOMBASE_PLTS{$1} = 1;
        };
    };

};

# ---------------------------------------------------------------
sub obtienePltPorTax {
# Obtiene nombre de plantilla taxonomica, de acuerdo a s, t y st.
#  O sea, si taxonomia de entrada es:
#  seccion=sN
#  tema=tN
#  subtema=stN
#  Se busca si existe una plantilla que se llame taxport_sN_tN_stN.<ext>
#  Si no existe, se busca taxport_sN_tN.<ext>
#  Si no existe, se busca taxport_sN.<ext>
#  Si no existe, se usa taxport.<ext>
    my ($s, $t, $st, $ruta_dir, $ext_port_tmp, $nombase) = @_;
    my $tpl;

    # Busca de la plantilla mas especifica a la mas general
    $tpl = "$ruta_dir/$nombase\_$s" . "_$t" . "_$st$ext_port_tmp";
    return $tpl if (-f $tpl);

    $tpl = "$ruta_dir/$nombase\_$s" . "_$t$ext_port_tmp";
    return $tpl if (-f $tpl);

    $tpl = "$ruta_dir/$nombase\_$s$ext_port_tmp";
    return $tpl if (-f $tpl);

    $tpl = "$ruta_dir/$nombase$ext_port_tmp";
    return $tpl if (-f $tpl);

    # return $ruta_dir;
    return '';

};
# ---------------------------------------------------------------
sub write_pag {

    my ($tax_fixedurl, $fid, $secc_nom, $tot_artics, $nro_pag, $secc_id, $temas_id, $subtemas_id, $filas_hashref) = @_;
    my %filas = %$filas_hashref;

#    $secc_id = '' if ($secc_id == 0);
#    $temas_id = '' if ($temas_id == 0);
#    $subtemas_id = '' if ($subtemas_id == 0);


    # escribe pagina en todas las vistas incluida la normal
    my %vistas; # incluye las mv y la normal
    %vistas = %prontus_varglb::MULTIVISTAS;
    $vistas{''} = 1;
    my $mv;
    foreach $mv (keys %vistas) {
        foreach my $nombase_plt (keys %NOMBASE_PLTS) {
            next if ((!$filas{"$mv|$nombase_plt"}) && ($nro_pag > 1)); # para evitar pagina sobrante sin items
            # Obtiene plantilla, de acuerdo al nivel taxonomico especificado, fid y mv
            my $pagina = &get_buffer_plt($secc_id, $temas_id, $subtemas_id, $fid, $mv, $nombase_plt);
            next if (!$pagina);
            
            # En estos casos sólo es válida la primera página
            my $key_hash = "$secc_id|$temas_id|$subtemas_id|$fid|$mv|$nombase_plt";
            if($BUF_PLT{$key_hash} =~ /%%_no_paginar%%/ && $nro_pag > 1) {
                next;
            };
            
            ($pagina, $MSGS{"$mv|$nombase_plt"}) = &carga_mensajes($pagina); # 1.8
            $pagina =~ s/%%_totartics%%/$tot_artics/ig;
            my $key_hash = "$secc_id|$temas_id|$subtemas_id|$fid|$mv|$nombase_plt";
            # warn "$key_hash lista[$lista]";
            my $reldir_port_dst = &obtieneRelDirDestino($fid, $mv);
            my ($nombase, $extension) = &lib_prontus::split_nom_y_extension($nombase_plt);
            $extension = '.' . $extension;
            $pagina =~ s/%%LOOP%%(.*?)%%\/LOOP%%/$filas{"$mv|$nombase_plt"}/isg;
            $pagina = &incluir_navbar($pagina, $secc_id, $temas_id, $subtemas_id, $mv, $reldir_port_dst, $extension, $nombase);
            $pagina = &incluir_nrosdepag($tot_artics, $pagina, $nro_pag, $secc_id, $temas_id, $subtemas_id, $mv, $reldir_port_dst, $extension, $nombase);
            $pagina =~ s/%%NOMSECC%%/$secc_nom/isg;
            # reemplazar nombre del prontus
            $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
            $pagina =~ s/%%_SERVER_NAME%%/$prontus_varglb::PUBLIC_SERVER_NAME/isg;


            $tax_fixedurl = &lib_prontus::get_tax_link($tax_fixedurl, $mv);
            $pagina =~ s/%%_FIXED_URL%%/$tax_fixedurl/isg;

            # Se parsean todas las marcas de seccion, tema y subtema.
            $pagina =~ s/%%_SECCION[1-3]%%/$secc_id/isg;
            $pagina =~ s/%%_TEMA[1-3]%%/$temas_id/isg;
            $pagina =~ s/%%_SUBTEMA[1-3]%%/$subtemas_id/isg;

            $pagina =~ s/%%_NOM_SECCION[1-3]%%/$secc_nom/isg;

            my ($temas_nom, $filler1, $filler2) = split (/\t\t/, $TABLA_TEM{$temas_id});
            $pagina =~ s/%%_NOM_TEMA[1-3]%%/$temas_nom/isg;

            my ($subtemas_nom, $filler3, $filler4) = split (/\t\t/, $TABLA_STEM{$subtemas_id});
            $pagina =~ s/%%_NOM_SUBTEMA[1-3]%%/$subtemas_nom/isg;

            my $path_include = &lib_prontus::get_path_croncgi();
            $pagina = &lib_prontus::parser_custom_function($pagina, $path_include);

            $pagina = &lib_prontus::parse_includes($prontus_varglb::DIR_SERVER, $pagina);

            $pagina =~ s/%%.*?%%//isg;

            # Escribe pagina
            my $fullpath_dir = "$prontus_varglb::DIR_SERVER$reldir_port_dst";

            &glib_fildir_02::check_dir($fullpath_dir) if (! -d $fullpath_dir);
            my $k = "$fullpath_dir/$nombase" . '_'
                                        . $secc_id
                                        . '_' . $temas_id
                                        . '_' . $subtemas_id
                                        . '_' . $nro_pag
                                    . $extension;
#            # debug
#            if (! exists $HASH_FILES{$k}) {
#                $HASH_FILES{$k} = 1;
#            } else {
#                print STDERR "escrito de nuevo!![$k]\n";
#            };


                
    #~ my $delta_t = time - $ini_t;
    #~ print STDERR "\tescribiendo[$delta_t][$k]\n"; # debug
    $COUNTER_TOTAL_PAGS++;
    
            &glib_fildir_02::write_file($k, $pagina);
            &lib_prontus::purge_cache($k);
            # print STDERR "writing [$k]\n";

        };

    };

};
# ---------------------------------------------------------------
sub obtieneRelDirDestino {
# Obtiene directorio de destino (relativo al doc root) donde sera almacenada
# la portada taxonomica generada
    my ($fid, $mv) = @_;
    my $reldir_port_dst = $RELDIR_PORT_DST;
    if ($fid) {
        $reldir_port_dst .= "/$fid";
    } else {
        $reldir_port_dst .= '/all';
    };
    if ($mv) { # nombre de la vista.
        $reldir_port_dst .= '-' . $mv;
    };
    return $reldir_port_dst;
};
# ---------------------------------------------------------------
sub incluir_navbar {
    my ($pagina, $secc_id, $temas_id, $subtemas_id, $mv, $reldir_port_dst, $extension, $nombase) = @_;
    # La navbar
    my $secc_tema_stema_nom;
    # secc
    # my ($secc_nom, $secc_port) = &get_nombreyport('SECC', $secc_id, 'seccion', $mv); # rotulos tax
    my ($secc_nom, $secc_port, $secc_nom4vistas) = split (/\t\t/, $TABLA_SECC{$secc_id});
    $secc_nom = &lib_prontus::get_nomtax_envista($mv, $secc_nom4vistas) if ($mv);
    $secc_nom = &lib_prontus::escape_html($secc_nom);

    # Se lee el separador
    my $separador = '/';
    if($pagina =~ /%%_secc_tema_stema_nom\((.*?)\)%%/i) {
      $separador = $1;
    }

    my $lnk_secc;
    if ($secc_port) {
        $lnk_secc = &lib_prontus::get_tax_link($secc_port);
    }
    else {
        # $lnk_secc = "/$prontus_varglb::DIR_CGI_PUBLIC/prontus_taxport_lista.cgi?seccion=$secc_id&amp;_REL_PATH_PRONTUS=$FORM{'prontus'}&amp;_MV=$mv";
        $lnk_secc = "$reldir_port_dst/$nombase" . '_'
        . $secc_id
        . '_'
        . '_'
        . '_' . '1'
        . $extension;
    };
    $secc_tema_stema_nom = "<a href='$lnk_secc'>$secc_nom</a>";
    # warn "slink[$secc_tema_stema_nom]";

    # tem
    # my ($tem_nom, $tem_port) = &get_nombreyport('TEMAS', $temas_id, 'tema-' . $secc_id, $mv); # rotulos tax
    my ($tem_nom, $tem_port, $filler1, $tem_nom4vistas) = split (/\t\t/, $TABLA_TEM{$temas_id});
    $tem_nom = &lib_prontus::get_nomtax_envista($mv, $tem_nom4vistas) if ($mv);
    $tem_nom = &lib_prontus::escape_html($tem_nom);

    if ($tem_nom) {
        my $lnk_tem;
        if ($tem_port) {
            $lnk_tem = &lib_prontus::get_tax_link($tem_port);
        }
        else {
            # $lnk_tem = "/$prontus_varglb::DIR_CGI_PUBLIC/prontus_taxport_lista.cgi?seccion=$secc_id&amp;tema=$temas_id&amp;_REL_PATH_PRONTUS=$FORM{'prontus'}&amp;_MV=$mv"; # rotulos tax
            $lnk_tem = "$reldir_port_dst/$nombase" . '_'
            . $secc_id
            . '_' . $temas_id
            . '_'
            . '_' . '1'
            . $extension;

        };
        $secc_tema_stema_nom .= " $separador <a href='$lnk_tem'>$tem_nom</a>";
        # warn "tlink[$secc_tema_stema_nom]";
    };

    # stem
    # my ($stem_nom, $stem_port) = &get_nombreyport('SUBTEMAS', $subtemas_id, 'subtema-' . $temas_id, $mv); # rotulos tax
    my ($stem_nom, $stem_port, $filler2, $stem_nom4vistas) = split (/\t\t/, $TABLA_STEM{$subtemas_id});
    $stem_nom = &lib_prontus::get_nomtax_envista($mv, $stem_nom4vistas) if ($mv);
    $stem_nom = &lib_prontus::escape_html($stem_nom);

    if ($stem_nom) {
        my $lnk_stem;
        if ($stem_port) {
            $lnk_stem = &lib_prontus::get_tax_link($stem_port);
        }
        else {
            # $lnk_stem = "/$prontus_varglb::DIR_CGI_PUBLIC/prontus_taxport_lista.cgi?seccion=$secc_id&amp;tema=$temas_id&amp;subtema=$subtemas_id&amp;_REL_PATH_PRONTUS=$FORM{'prontus'}&amp;_MV=$mv"; # rotulos tax
            $lnk_stem = "$reldir_port_dst/$nombase" . '_'
            . $secc_id
            . '_' . $temas_id
            . '_' . $subtemas_id
            . '_' . '1'
            . $extension;
        };
        $secc_tema_stema_nom .=  " $separador <a href='$lnk_stem'>$stem_nom</a>";
        # warn "stlink[$secc_tema_stema_nom]";
    };

    $pagina =~ s/%%_SECC_TEMA_STEMA_NOM.*?%%/$secc_tema_stema_nom/isg;
    return $pagina;

};
# ---------------------------------------------------------------
sub incluir_nrosdepag {
    my ($tot_artics, $pagina, $nro_pag, $secc_id, $temas_id, $subtemas_id, $mv, $reldir_port_dst, $extension, $nombase) = @_;
    my $msgs_aux = $MSGS{"$mv|$nombase$extension"};
    my %msgs = %$msgs_aux;

    my ($tpl_nropag) = '<a href="%%lnk%%">%%cnro_pag%%</a>';
    my ($tpl_nropag2) = '<span class="actual">%%cnro_pag%%</span>';

    my $cnro_pag = 0;
    my $html_nros_pag = '';
    my $i;

    for ($i=0;$i<$tot_artics;$i++) {
        if (((($i % $FILASXPAG) == 0) && ($i >= $FILASXPAG)) || ($i == 0)) {
            $cnro_pag++;
            my $tpl_nropag_aux;
            if ($cnro_pag == $nro_pag) {
                $tpl_nropag_aux = $tpl_nropag2;
            }else{
                $tpl_nropag_aux = $tpl_nropag;
            };

            # my $lnk = "/$prontus_varglb::DIR_CGI_PUBLIC/prontus_taxport_lista.cgi?seccion=$secc_id&amp;tema=$temas_id&amp;subtema=$subtemas_id&amp;nropag=$cnro_pag&amp;_REL_PATH_PRONTUS=$FORM{'prontus'}&amp;_MV=$mv"; # rotulos tax

            my $lnk = "$reldir_port_dst/$nombase" . '_'
            . $secc_id
            . '_' . $temas_id
            . '_' . $subtemas_id
            . '_' . $cnro_pag
            . $extension;

            $tpl_nropag_aux =~ s/%%lnk%%/$lnk/;
            $tpl_nropag_aux =~ s/%%cnro_pag%%/$cnro_pag/;
            $html_nros_pag .= "$tpl_nropag_aux\n";
        };
    };

    if ($html_nros_pag ne '') {
        $pagina =~ s/%%_HTML_NROS_PAG%%/ $html_nros_pag /ig;
    }
    else {
        $pagina =~ s/%%_HTML_NROS_PAG%%//ig;
        $pagina =~ s/%%_msg%%.*?%%\/_msg%%/$msgs{'no_results'}/is; # 1.8
    };

    return $pagina;

};


# ---------------------------------------------------------------
sub get_tot_artics {
    my ($filtros) = shift;
    my $base = shift;
    my ($sql, $salida, $tot);
    my ($count_art);
    $sql = "select count(ART_ID) from ART %%FILTRO%%";

    if ($filtros ne '') {
        $sql =~ s/%%FILTRO%%/ where $filtros /;
        $sql =~ s/group by ART_ID//i;
    }
    else {
        $sql =~ s/%%FILTRO%%//;
    };
    # print STDERR "$sql contar[$sql]";
    # &glib_fildir_02::write_file('tipotema.sql', $sql); # debug
    $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($count_art));
    $salida->fetch;
    $salida->finish;
    $count_art = '0' if $count_art eq '';
    $count_art = $prontus_varglb::TAXPORT_MAXARTICS if ($count_art > $prontus_varglb::TAXPORT_MAXARTICS);
    return $count_art;

};


# ---------------------------------------------------------------
sub valida_param {

    if ( (! -d "$prontus_varglb::DIR_SERVER/$FORM{'prontus'}") || ($FORM{'prontus'} eq '')  || ($FORM{'prontus'} =~ /^\//) )  {
        print STDERR "\nError: Directorio del publicador no es válido.";
        print STDERR "\nDebe indicar el nombre del Prontus a procesar (ej: prontus_noticias), como parametro de esta CGI\n";
        exit;
    };

    if ($FORM{'params_especif'}) {
        if ($FORM{'params_especif'} !~ /^[0-9A-Za-z_\-]*\/[0-9]*\/[0-9]*\/[0-9]*$/) {
            print STDERR "\nError al invocar con params especificos, el valor indicado no es valido. Formato debe ser fid/s/t/st. Aborta ejecucion.\n";
            exit;
        };
        $FORM{'seccion_especif'} =~ s/[^0-9]//g;
        $FORM{'tema_especif'} =~ s/[^0-9]//g;
        $FORM{'subtema_especif'} =~ s/[^0-9]//g;
        $FORM{'seccion_especif'} = 0 if ($FORM{'seccion_especif'} eq '');
        $FORM{'tema_especif'} = 0 if ($FORM{'tema_especif'} eq '');
        $FORM{'subtema_especif'} = 0 if ($FORM{'subtema_especif'} eq '');

        if ( (!$FORM{'seccion_especif'}) && (!$FORM{'fid_especif'}) ) {
            $FORM{'params_especif'} = '';
            $FORM{'tema_especif'} = 0;
            $FORM{'subtema_especif'} = 0;
        };

        if (!$FORM{'seccion_especif'}) {
            $FORM{'tema_especif'} = 0;
            $FORM{'subtema_especif'} = 0;
        };
        if (!$FORM{'tema_especif'}) {
            $FORM{'subtema_especif'} = 0;
        };

    };


};
# -------------------------------------------------------------------------#
sub carga_mensajes {
# Busca, inicializa y elimina mensajes dentro de la plantilla.
# Carga hash de mensajes
#     <!-- MSG xxx = xxx -->

    my($plantilla) = $_[0];
    my %msgs;
    # Mensajes por defecto.
    $msgs{'no_results'} = 'No se encontraron resultados.';

    while ($plantilla =~ /<!--\s*MSG\s*(\w+)\s*=\s*(.+?)\s*-->/sg) {
        $msgs{$1} = $2;
    };
    # Elimina mensajes de la plantilla.
    $plantilla =~ s/<!--\s*MSG\s*(\w+)\s*=\s*(.+?)\s*-->//sg;

    return ($plantilla, \%msgs);
};

# ---------------------------------------------------------------
sub get_fids2process {
# Obtiene fids para los cuales se generaran portadas taxonomicas.
# Estos son solo los que cuenten con plantilla taxonomica en el dir correspondiente:
# /<_prontus_id>/plantillas/tax/port/<_fid>[-<_mv>]/taxport[_<_seccion>][_<_tema>][_<_subtema>].<ext>

    my %fids;

    if ($FORM{'fid_especif'} ne '') {
        my $fname = $FORM{'fid_especif'};
        $fids{$fname} = 1;
    } else {
        my %multivistas = %prontus_varglb::MULTIVISTAS;
        $multivistas{''} = 1; # item artificial para procesar tb. la vista default

        foreach my $key (keys %prontus_varglb::FORM_PLTS) { # key = 'fid_general:General(general.php)'
            my $fid_name;
            next if ($key !~ /^(\w+) *:/);
            $fid_name = $1;

            foreach my $mv (keys %multivistas) {
                $mv = '-' . $mv if ($mv ne '');
                my $dir = "$prontus_varglb::DIR_SERVER$RELDIR_PORT_TMP/$fid_name$mv";
                next if (! -d $dir);
                my $plt = &get_tpl_tema($dir);
                next if ( (!-f "$dir/$plt") || (!$plt));
                $fids{$fid_name} = 1;
            };
        };
    };
    
    return %fids;

};
#-----------------------------------------------------------------------
sub stat_arch {
# Determina si el archivo es mas antiguo que N segundos, de acuerdo a fecha/hora de modificacion.
    my ($pathArch) = shift;

    # Obtener estadisticas del arch.
    my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,
        $mtime, $ctime,  $blksize,  $blocks)= stat $pathArch;
    return ($mtime, $size);
};

# ---------------------------------------------------------------
sub genera_filtros_taxports {
# Genera segmento variable del sql para encontrar los articulos.
# Aplica a portadas tax normales y a portadillas de calendarios taxonomicos

    my ($id_secc1, $id_tema1, $id_subtema1, $fid, $curr_dtime) = @_;

    $id_secc1 =~ s/"/""/g;
    $id_tema1 =~ s/"/""/g;
    $id_subtema1 =~ s/"/""/g;

    $curr_dtime =~ /^(\d{8})(\d\d\d\d)/;
    my $dt_system = $1;
    my $hhmm_system = $2;

    my ($filtros);

    if ($id_secc1) {
        # $filtros = "(ART_IDSECC1 = \"$id_secc1\" or ART_IDSECC2 = \"$id_secc1\" or ART_IDSECC3 = \"$id_secc1\")";
        $filtros = "(";
        $filtros .= "ART_IDSECC1 = \"$id_secc1\"";
        $filtros .= " or ART_IDSECC2 = \"$id_secc1\"" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
        $filtros .= " or ART_IDSECC3 = \"$id_secc1\"" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
        $filtros .= ")";



        if ($id_tema1) { # Distinto de todos.
            if ($filtros ne '') {
                # $filtros .= " and (ART_IDTEMAS1 = \"$id_tema1\" or ART_IDTEMAS2 = \"$id_tema1\" or ART_IDTEMAS3 = \"$id_tema1\")";
                $filtros .= "and (";
                $filtros .= "ART_IDTEMAS1 = \"$id_tema1\"";
                $filtros .= " or ART_IDTEMAS2 = \"$id_tema1\"" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
                $filtros .= " or ART_IDTEMAS3 = \"$id_tema1\"" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
                $filtros .= ")";
            };
            if ($id_subtema1) { # Distinto de todos.
                if ($filtros ne '') {
                    # $filtros .= " and (ART_IDSUBTEMAS1 = \"$id_subtema1\" or ART_IDSUBTEMAS2 = \"$id_subtema1\" or ART_IDSUBTEMAS3 = \"$id_subtema1\")";
                    $filtros .= "and (";
                    $filtros .= "ART_IDSUBTEMAS1 = \"$id_subtema1\"";
                    $filtros .= " or ART_IDSUBTEMAS2 = \"$id_subtema1\"" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
                    $filtros .= " or ART_IDSUBTEMAS3 = \"$id_subtema1\"" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
                    $filtros .= ")";
                };
            };
        };
    };

    if ($fid) {
        $filtros .= " and " if ($filtros);
        $filtros .= " (ART_TIPOFICHA = \"$fid\") ";
    };

    $filtros .= " and " if ($filtros);

    $filtros .= " (ART_FECHAPHORAP <= \"$dt_system$hhmm_system\") ";
    $filtros .= " and (ART_ALTA = \"1\") " if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS eq 'SI');

    if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
        $filtros .= " and ( (ART_FECHAEHORAE >= \"$dt_system$hhmm_system\") OR ( (ART_FECHAEHORAE < \"$dt_system$hhmm_system\") AND (ART_SOLOPORTADAS = \"1\") ) )";
    };

    return $filtros;

};


# -------------------------END SCRIPT----------------------
