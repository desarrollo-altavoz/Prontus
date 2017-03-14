#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

use strict;
# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use glib_hrfec_02;
use glib_dbi_02;
use glib_cgi_04;
use glib_fildir_02;
use Artic;
use lib_tax;
use lib_maxrunning;
use DBI;
use Time::HiRes qw(usleep);
use POSIX qw(strftime ceil);

my (%PARAMS, %TABLA_TEM, %TABLA_STEM, %TABLA_SECC, %FIDS, %CFG_FIL_TAXPORT);
my $BD;
my $RELDIR_PORT_DST = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_PTEMA";
my $RELDIR_PORT_TMP = "$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_PTEMA";
my $CURR_DTIME;
my %WORKERS2TRIGGER;
my $PATHNICE;
my $DIR_SEMAF;

main:{
    if ((! -d "$prontus_varglb::DIR_SERVER") || ($prontus_varglb::DIR_SERVER eq '') )  {
        print STDERR "\nError: Document root no valido.\n\nComo primer parametro debe indicar el path fisico al directorio raiz del servidor web, ejemplo: /sites/misitio/web \n";
        exit;
    };

    $CURR_DTIME = &glib_hrfec_02::get_dtime_pack4();

    $PARAMS{'prontus'} = $ARGV[0];
    $PARAMS{'params'} = $ARGV[1]; # optativo: fid/s/t/st para generar solo para esa taxonomia y fid
    $PARAMS{'ts'} = $ARGV[2]; # optativo: <ts> en formato: 20131008125012

    ($PARAMS{'fid'}, $PARAMS{'s'}, $PARAMS{'t'}, $PARAMS{'st'}) = split (/\//, $PARAMS{'params'});

    &valida_param();

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($PARAMS{'prontus'});
    &lib_prontus::load_config(  &lib_prontus::ajusta_pathconf($relpath_conf) );

    # Se carga la configuracion local si existe
    &lib_tax::carga_configuracion_local();

    $DIR_SEMAF = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/taxport_smf";

    &glib_fildir_02::check_dir($DIR_SEMAF) if (! -d $DIR_SEMAF); # ¿necesario?

    &conecta_db();
    $PATHNICE = &lib_prontus::get_path_nice();

    %TABLA_SECC = &lib_tax::carga_tabla_seccion($BD);
    %TABLA_TEM = &lib_tax::carga_tabla_temas($BD);
    %TABLA_STEM = &lib_tax::carga_tabla_subtemas($BD);

    my %fids2process = &get_fids2process();
    my $filter;

    foreach my $fid (keys %fids2process) {
        print STDERR "fid[$fid]\n";
        &queue_procs(0, 0, 0, $fid, $PARAMS{'ts'});
        &queue_procs($PARAMS{'s'}, 0, 0, $fid, $PARAMS{'ts'}) if ($PARAMS{'s'});
        &queue_procs($PARAMS{'s'}, $PARAMS{'t'}, 0, $fid, $PARAMS{'ts'}) if ($PARAMS{'s'} && $PARAMS{'t'});
        &queue_procs($PARAMS{'s'}, $PARAMS{'t'}, $PARAMS{'st'}, $fid, $PARAMS{'ts'}) if ($PARAMS{'s'} && $PARAMS{'t'} && $PARAMS{'st'});
    }

    foreach my $worker (keys %WORKERS2TRIGGER) {
        # Solo ejecuta el worker si no esta corriendo.
        my $pid = &glib_fildir_02::read_file("$DIR_SEMAF/worker_$worker");
        $pid =~ s/^\s+|\s+$//g;
        # revisamos si el proceso corresponde a un worker
        if ($pid ne '') {
            my $data_pid = &lib_maxrunning::isRunningPid($pid);
            print STDERR $data_pid;
            if ($data_pid eq '') {
                # si no hay procesos conrriendo con este pid se borra el semaforo y lanza el worker
                print "no hay proceso con pid $pid\n";
                unlink("$DIR_SEMAF/worker_$worker");
            } elsif ($data_pid !~ /prontus_cron_taxport_worker.cgi $prontus_varglb::PRONTUS_ID $worker/) {
                # si no es un proceso worker eliminamos el semaforo para lanzar el proceso correcto
                print STDERR "[$pid] no es proceso worker de taxport\n";
                unlink("$DIR_SEMAF/worker_$worker");
            } else {
                print STDERR "worker[$worker] ya esta corriendo.\n";
            }
        }
        my $cmd = "$PATHNICE /usr/bin/perl $Bin/prontus_cron_taxport_worker.cgi $prontus_varglb::PRONTUS_ID $worker >/dev/null 2>&1 &";
        #print "cmd[$cmd]\n";
        system($cmd);
    }

    $BD->disconnect;
};

sub carga_fids {
    foreach my $key (keys %prontus_varglb::FORM_PLTS) { # key = 'fid_general:General(general.php)'
        my $fid_name;
        next if ($key !~ /^(\w+) *:/);
        $fid_name = $1;
        $FIDS{$fid_name}  = 1;
    }
};

sub get_fids2process {
    my %fids;

    &carga_fids();

    if ($PARAMS{'fid'} ne '') {
        my $fname = $PARAMS{'fid'};
        $fids{$fname} = 1;
    } else {
        my $dir = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID$RELDIR_PORT_TMP";
        my @listado = &glib_fildir_02::lee_dir($dir);
        @listado = grep !/^\./, @listado; # Elimina directorios . y ..

        foreach my $item (@listado) {
            if (-d "$dir/$item" && $item =~ /^(\w+)-?/) {
                my $fname = $1;
                next if ($fname eq 'all');
                $fids{$fname} = 1 if (exists $FIDS{$fname});
            }
        }
    };

    # Se agregan como fids los filtros para usar la misma logica.
    my @listado_filtros = &get_taxport_fil();

    foreach my $fil (@listado_filtros) {
        $fids{$fil} = $1;
    };

    # si se invoca sin fid, considera el filtro sin fid
    $fids{''} = 1 if ($PARAMS{'fid'} eq '');

    # para uso normal desde el fid, en donde se invoca siempre con fid. Entonces si viene una tax definida, genera para esa tax con el fid, pero tb. para la tax sin fid especifico
    $fids{''} = 1 if ($PARAMS{'s'});

    return %fids;
};

sub conecta_db {
    # Conectar a BD
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();

    if (!ref($BD)) {
        print STDERR "ERROR: $msg_err_bd\n";
        exit;
    };

    $BD->{mysql_auto_reconnect} = 1;
};

sub valida_param {
    if ((! -d "$prontus_varglb::DIR_SERVER/$PARAMS{'prontus'}") || ($PARAMS{'prontus'} eq '')  || ($PARAMS{'prontus'} =~ /^\//))  {
        print STDERR "\nError: Directorio del publicador no es válido.";
        print STDERR "\nDebe indicar el nombre del Prontus a procesar (ej: prontus_noticias), como parametro de esta CGI\n";
        exit;
    };

    if ($PARAMS{'params'}) {
        if ($PARAMS{'params'} !~ /^[0-9A-Za-z_\-]*\/[0-9]*\/[0-9]*\/[0-9]*$/) {
            print STDERR "\nError al invocar con params especificos, el valor indicado no es valido. Formato debe ser fid/s/t/st. Aborta ejecucion.\n";
            exit;
        }

        $PARAMS{'s'} =~ s/[^0-9]//g;
        $PARAMS{'t'} =~ s/[^0-9]//g;
        $PARAMS{'st'} =~ s/[^0-9]//g;
        $PARAMS{'s'} = 0 if ($PARAMS{'s'} eq '');
        $PARAMS{'t'} = 0 if ($PARAMS{'t'} eq '');
        $PARAMS{'st'} = 0 if ($PARAMS{'st'} eq '');

        if ((!$PARAMS{'s'}) && (!$PARAMS{'fid'}) ) {
            $PARAMS{'params'} = '';
            $PARAMS{'t'} = 0;
            $PARAMS{'st'} = 0;
        }

        if (!$PARAMS{'s'}) {
            $PARAMS{'t'} = 0;
            $PARAMS{'st'} = 0;
        }

        if (!$PARAMS{'t'}) {
            $PARAMS{'st'} = 0;
        }

    }

    if ($PARAMS{'ts'}) {
        $PARAMS{'ts'} = '' if($PARAMS{'ts'} !~ /\d{14}/);
    }

};

sub queue_procs {
    my ($secc_id, $temas_id, $subtemas_id, $fid, $ts) = @_;
    my $id_level = $secc_id . '_' . $temas_id . '_' . $subtemas_id . '_' . $fid;
    my $filtros = &genera_filtros_taxports($secc_id, $temas_id, $subtemas_id, $fid, $CURR_DTIME);
    my $taxport_order = &genera_orden_taxports($fid);
    my $tot_artics = &get_tot_artics($filtros, $BD);
    my $nro_paginas = ceil($tot_artics / $prontus_varglb::TAXPORT_ARTXPAG);

    # ajustamos el id level en caso de que tenga 0s
    $id_level =~ s/^0_/_/ if ($secc_id eq '0');
    $id_level =~ s/(\d*)_0_(\d*)/$1__$2/ if ($temas_id eq '0');
    $id_level =~ s/(\d*)_(\d*)_0/$1_$2_/ if ($subtemas_id eq '0');

    if ($ts) {
        my $nro_pag = &get_pagina_artic($ts, $filtros, $nro_paginas, $taxport_order, $BD);

        if ($nro_pag) {
            print STDERR "Actualiza pagina especifica nro_pag[$nro_pag]\n";

            my $pid = &glib_fildir_02::read_file("$DIR_SEMAF/$id_level\_$nro_pag");
            if ($pid ne '') {
                print STDERR "Existe otro proceso para pagina $nro_pag, level $id_level... matandolo.\n";
                my $ret = `kill -9 $pid`;
                print STDERR "Killed pid[$pid] ret[$ret]\n";
            }

            my $cmd = "$PATHNICE /usr/bin/perl $Bin/prontus_cron_taxport_worker.cgi $prontus_varglb::PRONTUS_ID $fid/$secc_id/$temas_id/$subtemas_id/$nro_pag >/dev/null 2>&1 &";
            system($cmd);
        }

    } else {
        for (my $x = 1; $x <= $nro_paginas; $x++) {
            if ($x == 1) {
                # la primera pagina no se encola, se ejecuta como proceso independiente sin espera.
                # pero si existe otro igual corriendo, lo mata.
                # fid/seccion/tema/subtema
                my $pid = &glib_fildir_02::read_file("$DIR_SEMAF/$id_level\_$x");
                if ($pid ne '') {
                    print STDERR "Existe otro proceso para pagina 1, level $id_level... matandolo.\n";
                    my $ret = `kill -9 $pid`;
                    print STDERR "Killed pid[$pid] ret[$ret]\n";
                }

                my $cmd = "$PATHNICE /usr/bin/perl $Bin/prontus_cron_taxport_worker.cgi $prontus_varglb::PRONTUS_ID $fid/$secc_id/$temas_id/$subtemas_id/1 >/dev/null 2>&1 &";
                system($cmd);
            } else {
                &put_queue($secc_id, $temas_id, $subtemas_id, $fid, $x);
            }
        }
    }
};

sub get_pagina_artic {
    my $ts = $_[0];
    my $filtro = $_[1];
    my $nro_paginas = $_[2];
    my $taxport_order = $_[3];
    my $base = $_[4];
    my ($sql, $salida, $art_id);

    $filtro = "WHERE $filtro" if ($filtro);

    for (my $p = 0; $p < $nro_paginas; $p++) {
        my $limit = $p * $prontus_varglb::TAXPORT_ARTXPAG;
        $sql = "SELECT ART_ID FROM ART $filtro ORDER BY $taxport_order LIMIT $limit, $prontus_varglb::TAXPORT_ARTXPAG";
        $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($art_id));

        while ($salida->fetch) {
            if ($art_id eq $ts) {
                return ($p + 1);
            }
        }

        $salida->finish;
    }

    return '';
};

sub put_queue {
    my ($secc_id, $temas_id, $subtemas_id, $fid, $pagina) = @_;
    my $dir_queue = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/taxqueue";

    &glib_fildir_02::check_dir($dir_queue) if (! -d $dir_queue); # ¿necesario?

    my $worker = &get_queue_worker($dir_queue); # buscar el worker que tiene menos trabajo.
    my $file = "$fid\_$secc_id\_$temas_id\_$subtemas_id\_$pagina.txt";

    # Si existe en otro worker, se elimina para hacerlo abortar.
    for (my $x = 1; $x <= $prontus_varglb::TAXPORT_MAX_WORKERS; $x++) {
        if (-f "$dir_queue/$x\_$file") {
            print STDERR "Se aborta worker[$x] file[$file], se reemplaza por worker[$worker].\n";
            unlink "$dir_queue/$x\_$file";
        } else {
            print STDERR "QUEUE worker[$worker] file[$file]\n";
        }
    }

    $WORKERS2TRIGGER{$worker} = 1;

    &glib_fildir_02::write_file("$dir_queue/$worker\_$file", 1);
};

# devuelve el que tiene menos trabajo.
sub get_queue_worker {
    my $dir_queue = $_[0];
    my %workers;

    for (my $x = 1; $x <= $prontus_varglb::TAXPORT_MAX_WORKERS; $x++) {
        my $wcl = `find $dir_queue -name '$x\_*' | wc -l`;
        chomp ($wcl);
        $workers{$x} = $wcl;
    }

    my $min = (sort { $workers{$a} <=> $workers{$b} } keys %workers)[0];

    return $min;
};

sub genera_filtros_taxports {
    my ($id_secc1, $id_tema1, $id_subtema1, $fid, $curr_dtime) = @_;
    my $fid_fil = $fid;

    if ($fid =~ /^fil_/) {
        $fid = '';
    };

    $id_secc1 =~ s/"/""/g;
    $id_tema1 =~ s/"/""/g;
    $id_subtema1 =~ s/"/""/g;

    $curr_dtime =~ /^(\d{8})(\d\d\d\d)/;

    my $dt_system = $1;
    my $hhmm_system = $2;
    my $filtros;

    if ($id_secc1) {
        $filtros = "(";
        $filtros .= "ART_IDSECC1 = \"$id_secc1\"";
        $filtros .= " or ART_IDSECC2 = \"$id_secc1\"" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
        $filtros .= " or ART_IDSECC3 = \"$id_secc1\"" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
        $filtros .= ")";



        if ($id_tema1) { # Distinto de todos.
            if ($filtros ne '') {
                $filtros .= "and (";
                $filtros .= "ART_IDTEMAS1 = \"$id_tema1\"";
                $filtros .= " or ART_IDTEMAS2 = \"$id_tema1\"" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
                $filtros .= " or ART_IDTEMAS3 = \"$id_tema1\"" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
                $filtros .= ")";
            };
            if ($id_subtema1) { # Distinto de todos.
                if ($filtros ne '') {
                    $filtros .= "and (";
                    $filtros .= "ART_IDSUBTEMAS1 = \"$id_subtema1\"";
                    $filtros .= " or ART_IDSUBTEMAS2 = \"$id_subtema1\"" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
                    $filtros .= " or ART_IDSUBTEMAS3 = \"$id_subtema1\"" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
                    $filtros .= ")";
                };
            };
        };

    } else {
        if($fid eq '') {
            $filtros = "(";
            $filtros .= "ART_IDSECC1 <> \"\"";
            $filtros .= " or ART_IDSECC2 <> \"\"" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
            $filtros .= " or ART_IDSECC3 <> \"\"" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
            $filtros .= ")";
        };
    };

    if ($fid) {
        $filtros .= " and " if ($filtros);
        $filtros .= " (ART_TIPOFICHA = \"$fid\") ";
    };

    if ($fid_fil && defined $CFG_FIL_TAXPORT{$fid_fil}{'FIDS'}) {
        my @fidlist = @{$CFG_FIL_TAXPORT{$fid_fil}{'FIDS'}};
        my $filtro_fids;

        if (scalar @fidlist) {
            foreach my $filfid (@fidlist) {
                $filtro_fids .= "ART_TIPOFICHA = '$filfid' OR ";
            };

            $filtro_fids = substr($filtro_fids, 0, (length($filtro_fids)-3));

            $filtros .= " and " if ($filtros);
            $filtros .= "($filtro_fids)";
        };
    };

    $filtros .= " and " if ($filtros);

    if ($fid_fil && defined $CFG_FIL_TAXPORT{$fid_fil}{'FECHA_DESDE'} & $CFG_FIL_TAXPORT{$fid_fil}{'FECHA_DESDE'} ne '') {
        $filtros .= " (ART_FECHAP >= \"$CFG_FIL_TAXPORT{$fid_fil}{'FECHA_DESDE'}\") ";
    } else {
        $filtros .= " (ART_FECHAPHORAP <= \"$dt_system$hhmm_system\") ";
    };

    $filtros .= " and (ART_ALTA = \"1\") " if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS eq 'SI');

    if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
        $filtros .= " and ( (ART_FECHAEHORAE >= \"$dt_system$hhmm_system\") OR ( (ART_FECHAEHORAE < \"$dt_system$hhmm_system\") AND (ART_SOLOPORTADAS = \"1\") ) )";
    };

    return $filtros;

};

sub genera_orden_taxports {
    my $fid = $_[0];

    if ($fid =~ /^fil_/) {
        if (defined $CFG_FIL_TAXPORT{$fid}{'TAXPORT_ORDEN'} && $CFG_FIL_TAXPORT{$fid}{'TAXPORT_ORDEN'} ne '' ) {
            return $CFG_FIL_TAXPORT{$fid}{'TAXPORT_ORDEN'};
        } else {
            return $prontus_varglb::TAXPORT_ORDEN;
        }
    } else {
        return $prontus_varglb::TAXPORT_ORDEN;
    }

};

sub get_tot_artics {
    my $filtros = shift;
    my $base = shift;
    my ($sql, $salida, $tot);
    my $count_art;

    $sql = "select count(ART_ID) from ART %%FILTRO%%";

    if ($filtros ne '') {
        $sql =~ s/%%FILTRO%%/ where $filtros /;
        $sql =~ s/group by ART_ID//i;
    } else {
        $sql =~ s/%%FILTRO%%//;
    };

    $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($count_art));
    $salida->fetch;
    $salida->finish;

    $count_art = '0' if $count_art eq '';
    $count_art = $prontus_varglb::TAXPORT_MAXARTICS if ($count_art > $prontus_varglb::TAXPORT_MAXARTICS);

    return $count_art;
};

# -------------------------------------------------------------------------
# Se buscan los directorios que comiencen con fil_ en las plantillas de taxport.
sub get_taxport_fil {
    my ($ruta_dir) = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID$RELDIR_PORT_TMP";
    my @listado = glob("$ruta_dir/fil_*");
    my @filtros;

    foreach my $dir (@listado) {
        if ($dir =~ /fil_(.*?)$/) {
            push @filtros, "fil_" . $1;
            #&cargar_fil_cfg("$dir/filtros.cfg", "fil_" . $1);
        };

    };

    return @filtros;
};

sub cargar_fil_cfg {
    my $file = $_[0];
    my $fil = $_[1];
    my $cfg = &glib_fildir_02::read_file($file);

    return if (exists $CFG_FIL_TAXPORT{$fil}); # para no cargarlo dos veces.

    if ($cfg =~ m/\s*TAXPORT_FIDS\s*=\s*("|')(.*?)("|')/) {
        my $value = $2;

        # Se limpian los espacios.
        $value =~ s/\s+/ /sg;
        $value =~ s/^\s//sg;
        $value =~ s/\s$//sg;

        $value =~ s/[^a-zA-Z0-9_,]//sg; # dejar solo caracteres permitidos

        my @valores = split(',', $value);

        $CFG_FIL_TAXPORT{$fil}{'FIDS'} = \@valores;

        #print STDERR "CFG TAXPORT_FIDS! fil[$fil] value[$value]\n";
    };

    if ($cfg =~ m/\s*TAXPORT_PLANTILLAS\s*=\s*("|')(.*?)("|')/) {
        my $value = $2;

        # Se limpian los espacios.
        $value =~ s/\s+/ /sg;
        $value =~ s/^\s//sg;
        $value =~ s/\s$//sg;

        $value =~ s/[^a-zA-Z0-9_\-,\.]//sg; # dejar solo caracteres permitidos

        my @valores = split(',', $value);

        foreach my $tpl (@valores) {
            $CFG_FIL_TAXPORT{$fil}{'PLANTILLAS'}{$tpl} = 1;
        };

        #print STDERR "CFG TAXPORT_PLANTILLAS! fil[$fil] value[$value]\n";
    };

    if ($cfg =~ m/\s*TAXPORT_FECHAP?_DESDE\s*=\s*("|')(.*?)("|')/s) { # fecha de publicacion, ART_FECHAP
        my $value = $2;

        # Se limpian los espacios.
        $value =~ s/\s+/ /sg;
        $value =~ s/^\s//sg;
        $value =~ s/\s$//sg;

        if ($value eq 'now') {
            $value = strftime "%Y%m%d", localtime;
        } else {
            $value =~ s/[^0-9]//sg; # dejar solo caracteres permitidos, numeros.
        }

        $value = '' if ($value !~ /^(\d{8})$/); # formato debe ser YYYYMMDD

        $CFG_FIL_TAXPORT{$fil}{'FECHA_DESDE'} = $value;

        #print STDERR "CFG CFG_FIL_TAXPORT! fil[$fil] value[$value]\n";
    };

    if ($cfg =~ m/\s*TAXPORT_ORDEN\s*=\s*("|')(.*?)("|')/s) { # fecha de publicacion, ART_FECHAP
        my $value = $2;
        my $taxport_orden = 'ART_FECHAP desc, ART_HORAP desc'; # valor por defecto.

        # Se limpian los espacios.
        $value =~ s/\s+/ /sg;
        $value =~ s/^\s//sg;
        $value =~ s/\s$//sg;

        if ($value =~ /^(PUBLICACION|TITULAR|CREACION)\((ASC|DESC)\)$/) {
            if ($1 eq 'PUBLICACION') {
                $taxport_orden = "ART_FECHAP $2, ART_HORAP $2";
            } elsif ($1 eq 'TITULAR') {
                $taxport_orden = "ART_TITU $2";
            } elsif ($1 eq 'CREACION') {
                $taxport_orden = "ART_AUTOINC $2";
            }
        }

        $CFG_FIL_TAXPORT{$fil}{'TAXPORT_ORDEN'} = $taxport_orden;

        #print STDERR "CFG CFG_FIL_TAXPORT! fil[$fil] value[$value] taxport_orden[$taxport_orden]\n";
    };

};
