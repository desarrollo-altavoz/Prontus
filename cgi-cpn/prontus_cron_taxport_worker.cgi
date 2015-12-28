#!/usr/bin/perl

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
use glib_hrfec_02;
use glib_dbi_02;
use glib_cgi_04;
use glib_fildir_02;
use Artic;
use lib_tax;
use lib_maxrunning;
use strict;
use DBI;
use Time::HiRes qw(usleep);
use POSIX qw(strftime ceil);

my $BD;
my (%PARAMS, %TABLA_TEM, %TABLA_STEM, %TABLA_SECC, %FIDS, %CFG_FIL_TAXPORT);\
my %NOMBASE_PLTS;
my $CURR_DTIME;
my $WORKER;
my $DIR_SEMAF;
my $RELDIR_PORT_DST;
my $RELDIR_PORT_TMP;
my (%EXT_PORT_TMP, %BUF_PLT, %BUF_PLT_LOOP, %MSGS, %LOADED_NAMES_PLT);
my $RELDIR_ARTIC;
my %ART_XML_FIELDS;
my %ART_XDATA_FIELDS;

main: {
    if ((!-d "$prontus_varglb::DIR_SERVER") || ($prontus_varglb::DIR_SERVER eq ''))  {
        print STDERR "\nError: Document root no valido.\n\nComo primer parametro debe indicar el path fisico al directorio raiz del servidor web, ejemplo: /sites/misitio/web \n";
        exit;
    };

    $CURR_DTIME = &glib_hrfec_02::get_dtime_pack4();

    $PARAMS{'prontus'} = $ARGV[0];
    $PARAMS{'params'} = $ARGV[1]; # puede ser el numero del worker o fid/s/t/st

    ($PARAMS{'fid'}, $PARAMS{'s'}, $PARAMS{'t'}, $PARAMS{'st'}, $PARAMS{'pag'}) = split (/\//, $PARAMS{'params'});
    &valida_param();

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($PARAMS{'prontus'});
    &lib_prontus::load_config(  &lib_prontus::ajusta_pathconf($relpath_conf) );

    $RELDIR_PORT_DST = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_PTEMA";
    $RELDIR_PORT_TMP = "$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_PTEMA";
    $DIR_SEMAF = "$prontus_varglb::DIR_SERVER/$prontus_varglb::DIR_DBM/taxport_smf";
    $RELDIR_ARTIC = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/%%DIRFECHA%%$prontus_varglb::DIR_PAG";

    &glib_fildir_02::check_dir($DIR_SEMAF) if (! -d $DIR_SEMAF); # ¿necesario?

    &conecta_db();
    &carga_nombase_plts();

    %TABLA_SECC = &lib_tax::carga_tabla_seccion($BD);
    %TABLA_TEM = &lib_tax::carga_tabla_temas($BD);
    %TABLA_STEM = &lib_tax::carga_tabla_subtemas($BD);

    if ($PARAMS{'params'} =~ /^(\d+)$/) {
        $WORKER = $1;

        if (!$WORKER) {
            print STDERR "ERROR: Worker no especificado.\n";
            exit;
        } else {
            &procesa_queue_worker($WORKER);
        }
    } else {
        &generar_taxports_thislevel($PARAMS{'s'}, $PARAMS{'t'}, $PARAMS{'st'}, $PARAMS{'fid'}, $PARAMS{'pag'}, 1); # solo pagina 1.
    }

    $BD->disconnect;
};

sub procesa_queue_worker {
    my $worker = $_[0];
    my $semaforo = "$DIR_SEMAF/worker_$worker";
    my $dir_queue = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/taxqueue";

    exit if (-f $semaforo);

    &glib_fildir_02::write_file($semaforo, $$);

    my @jobs = glob("$dir_queue/$worker\_*.txt");
    my $job;

    while (defined($job = shift @jobs)) {
        if (!-f $job) {
            print STDERR "[$$][$worker] TOMADO POR OTRO WORKER: $job\n";
            @jobs = glob("$dir_queue/$worker\_*.txt");
            next;
        }

        # Formato: $worker_$fid\_$secc_id\_$temas_id\_$subtemas_id\_$pagina.txt
        if ($job =~ /$dir_queue\/$worker\_([0-9A-Za-z_\-]*)_(\d*)_(\d*)_(\d*)_(\d*)\.txt$/) {
            my ($fid, $secc_id, $tema_id, $subtema_id, $pagina) = ($1, $2, $3, $4, $5);
            $secc_id = '' if ($secc_id eq '0');
            $tema_id = '' if ($tema_id eq '0');
            $subtema_id = '' if ($subtema_id eq '0');

            &generar_taxports_thislevel($secc_id, $tema_id, $subtema_id, $fid, $pagina, 0);
        }

        unlink $job;

        if (!scalar @jobs) {
            # Buscar mas...
            @jobs = glob("$dir_queue/$worker\_*.txt");
        }
    }

    print STDERR "[$$][$worker] Fin.\n";

    unlink $semaforo;
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

# ---------------------------------------------------------------
sub generar_taxports_thislevel {
    my ($secc_id, $temas_id, $subtemas_id, $fid, $nro_pagina, $semaf) = @_;
    my $id_level = $secc_id . '_' . $temas_id . '_' . $subtemas_id . '_' . $fid . '_' . $nro_pagina;
    my $filtros = &genera_filtros_taxports($secc_id, $temas_id, $subtemas_id, $fid, $CURR_DTIME);
    my $taxport_order = &genera_orden_taxports($fid);
    my $tot_artics = &get_tot_artics($filtros, $BD);
    my $tax_fixedurl;

    &glib_fildir_02::write_file("$DIR_SEMAF/$id_level", $$) if ($semaf);

    print STDERR "[$$][$WORKER] procesando [$id_level]\n";

    my $p = $nro_pagina - 1;
    my $limit = $p * $prontus_varglb::TAXPORT_ARTXPAG;

    my ($secc_nom, $secc_port, $secc_nom4vistas) = split (/\t\t/, $TABLA_SECC{$secc_id});
    my ($temas_nom, $temas_port, $temas_idparent, $temas_nom4vistas) = split (/\t\t/, $TABLA_TEM{$temas_id});
    my ($subtemas_nom, $subtemas_port, $subtemas_idparent, $subtemas_nom4vistas) = split (/\t\t/, $TABLA_STEM{$subtemas_id});

    $tax_fixedurl = $secc_port if ($secc_port);
    $tax_fixedurl = $temas_port if ($temas_port);
    $tax_fixedurl = $subtemas_port if ($subtemas_port);

    my $sql = "select ART_ID, ART_FECHAP, ART_HORAP, ART_TITU, "
    . "ART_DIRFECHA, ART_EXTENSION, ART_TIPOFICHA, ART_IDTEMAS1, ART_BAJA from ART "
    . "%%FILTRO%% order by $taxport_order LIMIT $limit, $prontus_varglb::TAXPORT_ARTXPAG";

    if ($filtros ne '') {
        $sql =~ s/%%FILTRO%%/ where $filtros /;
    } else {
        $sql =~ s/%%FILTRO%%/$filtros/;
    };

    my $nro_filas = 0;
    my %filas;
    my ($art_id, $art_fecha, $art_horap, $art_titu, $art_dirfecha, $art_extension, $art_tipoficha, $art_idtemas1, $art_baja);
    my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($art_id, $art_fecha, $art_horap, $art_titu, $art_dirfecha, $art_extension, $art_tipoficha, $art_idtemas1, $art_baja));

    while ($salida->fetch) {
        $nro_filas++;

        # parsea esta fila en todas las multivistas
        my $mv;
        my %vistas = %prontus_varglb::MULTIVISTAS;
        $vistas{''} = 1; # vista default

        foreach $mv (keys %vistas) {
            foreach my $nombase_plt (keys %NOMBASE_PLTS) {
                # Obtiene plantilla, de acuerdo al nivel taxonomico especificado, fid y mv
                my $loop_plt = &get_loop_plt($secc_id, $temas_id, $subtemas_id, $fid, $mv, $nombase_plt);

                next if (!$loop_plt);

                my $key_hash = "$secc_id|$temas_id|$subtemas_id|$fid|$mv|$nombase_plt";

                if ($BUF_PLT{$key_hash} =~ /%%_no_paginar%%/ && $nro_pagina > 0) {
                    next;
                }

                my ($fila_content, $auxref, $auxref2) = &lib_tax::generar_fila($RELDIR_ARTIC, $art_id, $art_extension, $loop_plt, $nro_filas, $tot_artics, $ART_XML_FIELDS{$art_id}, $ART_XDATA_FIELDS{$art_id}, $nro_pagina);

                $ART_XML_FIELDS{$art_id} = $auxref if (!exists $ART_XML_FIELDS{$art_id}); # para no leer 2 veces un xml
                $ART_XDATA_FIELDS{$art_id} = $auxref2 if (!exists $ART_XDATA_FIELDS{$art_id}); # para no leer las xdata 2 veces

                $filas{"$mv|$nombase_plt"} .= $fila_content;
            }
        }
    }

    $salida->finish;

    &write_pag($tax_fixedurl, $fid, $secc_nom, $tot_artics, $nro_pagina, $secc_id, $temas_id, $subtemas_id, \%filas);

    unlink "$DIR_SEMAF/$id_level" if ($semaf);
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
            }

            if ($id_subtema1) { # Distinto de todos.
                if ($filtros ne '') {
                    $filtros .= "and (";
                    $filtros .= "ART_IDSUBTEMAS1 = \"$id_subtema1\"";
                    $filtros .= " or ART_IDSUBTEMAS2 = \"$id_subtema1\"" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
                    $filtros .= " or ART_IDSUBTEMAS3 = \"$id_subtema1\"" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
                    $filtros .= ")";
                }
            }
        }

    } else {
        if ($fid eq '') {
            $filtros = "(";
            $filtros .= "ART_IDSECC1 <> \"\"";
            $filtros .= " or ART_IDSECC2 <> \"\"" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
            $filtros .= " or ART_IDSECC3 <> \"\"" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
            $filtros .= ")";
        }
    }

    if ($fid) {
        $filtros .= " and " if ($filtros);
        $filtros .= " (ART_TIPOFICHA = \"$fid\") ";
    }

    if ($fid_fil && defined $CFG_FIL_TAXPORT{$fid_fil}{'FIDS'}) {
        my @fidlist = @{$CFG_FIL_TAXPORT{$fid_fil}{'FIDS'}};
        my $filtro_fids;

        if (scalar @fidlist) {
            foreach my $filfid (@fidlist) {
                $filtro_fids .= "ART_TIPOFICHA = '$filfid' OR ";
            }

            $filtro_fids = substr($filtro_fids, 0, (length($filtro_fids)-3));

            $filtros .= " and " if ($filtros);
            $filtros .= "($filtro_fids)";
        }
    }

    $filtros .= " and " if ($filtros);

    if ($fid_fil && defined $CFG_FIL_TAXPORT{$fid_fil}{'FECHA_DESDE'} & $CFG_FIL_TAXPORT{$fid_fil}{'FECHA_DESDE'} ne '') {
        $filtros .= " (ART_FECHAP >= \"$CFG_FIL_TAXPORT{$fid_fil}{'FECHA_DESDE'}\") ";
    } else {
        $filtros .= " (ART_FECHAPHORAP <= \"$dt_system$hhmm_system\") ";
    }

    $filtros .= " and (ART_ALTA = \"1\") " if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS eq 'SI');

    if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
        $filtros .= " and ( (ART_FECHAEHORAE >= \"$dt_system$hhmm_system\") OR ( (ART_FECHAEHORAE < \"$dt_system$hhmm_system\") AND (ART_SOLOPORTADAS = \"1\") ) )";
    }

    return $filtros;
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
    }

    my $buffer = &glib_fildir_02::read_file($plt);
    my $dirmacros = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_PTEMA_MACROS";
    my $loop;

    $buffer = &lib_prontus::add_macros($buffer, $dirmacros) if(-d $dirmacros);

    if ($buffer =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
        $loop = $1;
    }

    # Carga en ram plantillas
    $BUF_PLT_LOOP{$key_hash} = $loop;
    $BUF_PLT{$key_hash} = $buffer;
    $LOADED_NAMES_PLT{$plt} = $key_hash;

    return $loop;
};

sub get_buffer_plt {
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
    }

    my $buffer = &glib_fildir_02::read_file($plt);
    my $dirmacros = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_PTEMA_MACROS";
    my $loop;

    $buffer = &lib_prontus::add_macros($buffer, $dirmacros) if(-d $dirmacros);

    if ($buffer =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
        $loop = $1;
    }

    # Carga en ram plantillas
    $BUF_PLT_LOOP{$key_hash} = $loop;
    $BUF_PLT{$key_hash} = $buffer;
    $LOADED_NAMES_PLT{$plt} = $key_hash;

    return $buffer;
};


# ---------------------------------------------------------------
sub write_pag {
    my ($tax_fixedurl, $fid, $secc_nom, $tot_artics, $nro_pag, $secc_id, $temas_id, $subtemas_id, $filas_hashref) = @_;
    my %filas = %$filas_hashref;

    # escribe pagina en todas las vistas incluida la normal
    my %vistas = %prontus_varglb::MULTIVISTAS;
    $vistas{''} = 1;

    foreach my $mv (keys %vistas) {
        foreach my $nombase_plt (keys %NOMBASE_PLTS) {
            next if ((!$filas{"$mv|$nombase_plt"}) && ($nro_pag > 1)); # para evitar pagina sobrante sin items
            # Obtiene plantilla, de acuerdo al nivel taxonomico especificado, fid y mv
            my $pagina = &get_buffer_plt($secc_id, $temas_id, $subtemas_id, $fid, $mv, $nombase_plt);
            next if (!$pagina);

            # Solo para filtros. Si estan configuradas las plantillas, solo se consideran esas.
            if ($fid =~ /^fil_/ && defined $CFG_FIL_TAXPORT{$fid}{'PLANTILLAS'} && !defined $CFG_FIL_TAXPORT{$fid}{'PLANTILLAS'}{$nombase_plt}) {
                next;
            }

            # En estos casos sólo es válida la primera página
            my $key_hash = "$secc_id|$temas_id|$subtemas_id|$fid|$mv|$nombase_plt";
            if ($BUF_PLT{$key_hash} =~ /%%_no_paginar%%/ && $nro_pag > 1) {
                next;
            }

            ($pagina, $MSGS{"$mv|$nombase_plt"}) = &carga_mensajes($pagina);
            $pagina =~ s/%%_totartics%%/$tot_artics/ig;

            my $reldir_port_dst = &obtieneRelDirDestino($fid, $mv);
            my ($nombase, $extension) = &lib_prontus::split_nom_y_extension($nombase_plt);

            $pagina =~ s/%%_plt_nom%%/$nombase/isg;
            $pagina =~ s/%%_plt_ext%%/$extension/isg;
            $pagina =~ s/%%_tax_fid%%/$fid/isg if ($fid);
            $pagina =~ s/%%_tax_fid%%/all/isg if (!$fid);

            $extension = '.' . $extension;
            $pagina =~ s/%%LOOP%%(.*?)%%\/LOOP%%/$filas{"$mv|$nombase_plt"}/isg;
            $pagina = &incluir_navbar($pagina, $secc_id, $temas_id, $subtemas_id, $mv, $reldir_port_dst, $extension, $nombase);
            $pagina = &incluir_nrosdepag($tot_artics, $pagina, $nro_pag, $secc_id, $temas_id, $subtemas_id, $mv, $reldir_port_dst, $extension, $nombase);
            $pagina =~ s/%%NOMSECC%%/$secc_nom/isg;
            # reemplazar nombre del prontus
            $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
            $pagina =~ s/%%_SERVER_NAME%%/$prontus_varglb::PUBLIC_SERVER_NAME/isg;

            $pagina =~ s/%%_nropagina%%/$nro_pag/isg;
            $pagina =~ s/%%_vista%%/$mv/isg;

            $tax_fixedurl = &lib_prontus::get_tax_link($tax_fixedurl, $mv);
            $pagina =~ s/%%_FIXED_URL%%/$tax_fixedurl/isg;

            # Lee el nombre de tema y subtema
            my ($temas_nom, $filler1, $filler2) = split (/\t\t/, $TABLA_TEM{$temas_id});
            my ($subtemas_nom, $filler3, $filler4) = split (/\t\t/, $TABLA_STEM{$subtemas_id});

            # Para poder hacer IF de seccion, tema y subtema
            my %claves = ('_tax_seccion' => $secc_id, '_tax_tema' => $temas_id, '_tax_subtema' => $subtemas_id,
                    '_tax_nom_seccion' => $secc_nom, '_tax_nom_tema' => $temas_nom, '_tax_nom_subtema' => $subtemas_nom);

            my %claves_compatibles = ('_seccion1' => $secc_id, '_tema1' => $temas_id, '_subtema1' => $subtemas_id,
                    '_nom_seccion1' => $secc_nom, '_nom_tema1' => $temas_nom, '_nom_subtema1' => $subtemas_nom,
                    '_vista' => $mv, '_nropagina' => $nro_pag, '_tax_fid' => $fid);

            $pagina = &lib_prontus::procesa_condicional($pagina, \%claves, \%claves_compatibles);

            # Se parsean todas las marcas de seccion, tema y subtema.
            # Esto se mantiene por compatibilidad
            $pagina =~ s/%%_SECCION[1-3]%%/$secc_id/isg;
            $pagina =~ s/%%_TEMA[1-3]%%/$temas_id/isg;
            $pagina =~ s/%%_SUBTEMA[1-3]%%/$subtemas_id/isg;
            $pagina =~ s/%%_NOM_SECCION[1-3]%%/$secc_nom/isg;
            $pagina =~ s/%%_NOM_TEMA[1-3]%%/$temas_nom/isg;
            $pagina =~ s/%%_NOM_SUBTEMA[1-3]%%/$subtemas_nom/isg;

            # Se parsean las nuevas marcas de taxport
            $pagina =~ s/%%_tax_seccion%%/$secc_id/isg;
            $pagina =~ s/%%_tax_tema%%/$temas_id/isg;
            $pagina =~ s/%%_tax_subtema%%/$subtemas_id/isg;
            $pagina =~ s/%%_tax_nom_seccion%%/$secc_nom/isg;
            $pagina =~ s/%%_tax_nom_tema%%/$temas_nom/isg;
            $pagina =~ s/%%_tax_nom_subtema%%/$subtemas_nom/isg;

            # Parsear el nombre de la s, t, st segun la vista.
            if ($mv) {
                my ($mv_nom_seccion1, $mv_nom_tema1, $mv_nom_subtema1) = &lib_prontus::get_nom4vistas($mv, $secc_id, $temas_id, $subtemas_id);
                $pagina =~ s/%%_tax_nom_seccion_$mv%%/$mv_nom_seccion1/isg;
                $pagina =~ s/%%_tax_nom_tema_$mv%%/$mv_nom_tema1/isg;
                $pagina =~ s/%%_tax_nom_subtema_$mv%%/$mv_nom_subtema1/isg;
                $pagina =~ s/%%_nom_seccion[1-3]_$mv%%/$mv_nom_seccion1/isg;
                $pagina =~ s/%%_nom_tema[1-3]_$mv%%/$mv_nom_tema1/isg;
                $pagina =~ s/%%_nom_subtema[1-3]_$mv%%/$mv_nom_subtema1/isg;
            };

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

            &glib_fildir_02::write_file($k, $pagina);

            # Solo hacer purge de taxport si está habilitado.
            if ($prontus_varglb::CACHE_PURGE_TAXPORT eq 'SI') {
                if ($prontus_varglb::CACHE_PURGE_TAXPORT_MV eq 'SI') {
                    &lib_prontus::purge_cache($k);
                } else {
                    # Si está desactivada la opción de hacer purge a la vistas, solo se hace a la principal.
                    if ($mv eq '') {
                        &lib_prontus::purge_cache($k);
                    }
                }
            }

            # print STDERR "writing [$k]\n";
        }
    }
};

# ---------------------------------------------------------------
sub obtiene_plt {
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
sub obtienePltPorTax {
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

    return '';
};

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

sub incluir_nrosdepag {
    my ($tot_artics, $pagina, $nro_pag, $secc_id, $temas_id, $subtemas_id, $mv, $reldir_port_dst, $extension, $nombase) = @_;
    my $msgs_aux = $MSGS{"$mv|$nombase$extension"};
    my %msgs = %$msgs_aux;

    my $tpl_nropag = '<a href="%%lnk%%">%%cnro_pag%%</a>';
    my $tpl_nropag2 = '<span class="actual">%%cnro_pag%%</span>';
    my $tpl_separador = '...';

    #~ my $cnro_pag = 0;
    my $html_nros_pag = '';
    my $i;

    # Carga configuaración.
    my %cfg_paginacion;
    while ($pagina =~ /<!--\s*CONFIG\s*(\w+)\s*=\s*(.*?)\s*-->/sg) {
        my $name = uc $1;
        my $value = $2;

        #print STDERR "name[$name] value[$value]\n";

        $tpl_nropag = $value if ($name eq 'HTML_NRO_PAG');
        $tpl_nropag2 = $value if ($name eq 'HTML_PAG_ACTUAL');
        $tpl_separador = $value if ($name eq 'HTML_SEPARADOR');
    };

    # Quitar comentarios de configuración.
    $pagina =~ s/<!--\s*CONFIG\s*(\w+)\s*=\s*(.+?)\s*-->//sg;

    my $nro_paginas_totales = ceil($tot_artics / $prontus_varglb::TAXPORT_ARTXPAG);
    my ($ini, $fin, $nextlink, $prevlink);

    if ($prontus_varglb::TAXPORT_TIPO_PAGINACION eq '1') {

        # Se procesan las paginas hacia abajo
        $ini = ($nro_pag - $prontus_varglb::TAXPORT_PAGCORTA_MAXPAGS);
        if($ini le 1) {
            $ini = 1;
        } else {
            $ini = $ini + 1;
            my $lnk = "$reldir_port_dst/$nombase" . '_'
                . $secc_id
                . '_' . $temas_id
                . '_' . $subtemas_id
                . '_' . 1
                . $extension;
            my $pag = '1';
            my $tpl_nropag_aux = $tpl_nropag;
            $tpl_nropag_aux =~ s/%%lnk%%/$lnk/;
            $tpl_nropag_aux =~ s/%%cnro_pag%%/$pag/;
            $prevlink =  $tpl_nropag_aux . ' ' . $tpl_separador . ' ';
        };

        # Se procesan las páginas hacia arriba
        $fin = ($nro_pag + $prontus_varglb::TAXPORT_PAGCORTA_MAXPAGS);
        if($fin >= $nro_paginas_totales) {
            $fin = $nro_paginas_totales;
        } else {
            $fin = $fin - 1;
            my $lnk = "$reldir_port_dst/$nombase" . '_'
                . $secc_id
                . '_' . $temas_id
                . '_' . $subtemas_id
                . '_' . $nro_paginas_totales
                . $extension;
            my $pag = $nro_paginas_totales;
            my $tpl_nropag_aux = $tpl_nropag;
            $tpl_nropag_aux =~ s/%%lnk%%/$lnk/;
            $tpl_nropag_aux =~ s/%%cnro_pag%%/$pag/;
            $nextlink =  ' ' . $tpl_separador . ' ' . $tpl_nropag_aux;
        };

    } else {
        $ini = 1;
        $fin = $nro_paginas_totales;
    }

    for (my $pag = $ini; $pag <= $fin; $pag++) {
        my $tpl_nropag_aux;
        if ($pag eq $nro_pag) {
            $tpl_nropag_aux = $tpl_nropag2;
        }else{
            $tpl_nropag_aux = $tpl_nropag;
        };
        my $lnk = "$reldir_port_dst/$nombase" . '_'
                . $secc_id
                . '_' . $temas_id
                . '_' . $subtemas_id
                . '_' . $pag
                . $extension;

        $tpl_nropag_aux =~ s/%%lnk%%/$lnk/;
        $tpl_nropag_aux =~ s/%%cnro_pag%%/$pag/;
        $html_nros_pag .= "$tpl_nropag_aux\n";
    };
    $html_nros_pag = $prevlink . $html_nros_pag . $nextlink;

    if ($html_nros_pag ne '') {
        $pagina =~ s/%%_HTML_NROS_PAG%%/ $html_nros_pag /ig;
    }
    else {
        $pagina =~ s/%%_HTML_NROS_PAG%%//ig;
        $pagina =~ s/%%_msg%%.*?%%\/_msg%%/$msgs{'no_results'}/is; # 1.8
    };

    return $pagina;
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

sub valida_param {
    $PARAMS{'s'} =~ s/[^0-9]//g;
    $PARAMS{'t'} =~ s/[^0-9]//g;
    $PARAMS{'st'} =~ s/[^0-9]//g;
    $PARAMS{'pag'} =~ s/[^0-9]//g;
    $PARAMS{'s'} = '' if ($PARAMS{'s'} eq '0');
    $PARAMS{'t'} = '' if ($PARAMS{'t'} eq '0');
    $PARAMS{'st'} = '' if ($PARAMS{'st'} eq '0');
    $PARAMS{'pag'} = 1 if ($PARAMS{'pag'} eq '');
};