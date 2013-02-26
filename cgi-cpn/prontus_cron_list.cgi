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
# prontus_cron_lista.cgi
#
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/.
#
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Generar listados de artículos bajo cierto criterios en modo batch
#
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------
# No registra
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# como cron, con lo sgtes. params:
# $ARGV[0] : Nombre del prontus (ej. prontus_noticias)
# $ARGV[1] : s/t/st a procesar, optativo
#
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# Plantillas:
# /<_prontus_id>/plantillas/list/port/
# Se procesan todas las plantillas del directorio.
# Dentro de la plantilla iran marcas para indicar que irá en dicho listado.
# Formato de las Marcas: <!-- CONFIG <name>=<value> -->
# names posibles: LIST_MAXARTICS,LIST_SECCION,LIST_TEMA,LIST_SUBTEMA,LIST_FIDS,LIST_ORDEN,
#
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# /<prontus_dir>/site/list/port/
#
# ---------------------------------------------------------------
# Tablas.
# ------------------------
# BD: la configurada en Prontus. Tablas: 'ART', 'SECC', 'TEMAS', 'SUBTEMAS'
# ---------------------------------------------------------------
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 06/2012 - CVI - Primera Version.
#
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    use FindBin '$Bin';
    unshift(@INC,$Bin); # Para dejar disponibles las librerias
};

use strict;
use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use glib_dbi_02;
use glib_fildir_02;
use Artic;
use lib_tax;
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

close STDOUT;
# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my ($LOOP, %FORM, $NOM_PRONTUS, %TABLA_TEM, %TABLA_STEM, %TABLA_SECC);
my %NOMBASE_PLTS;
my %CONTENT_PLTS;
my %CONFIG_PLTS;

# my %HASH_FILES;
# cd /sites/prontus_development/web/cgi-cpn
# perl /sites/prontus_development/web/cgi-cpn/prontus_cron_taxport.cgi prontus_toolbox

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

my ($RELDIR_ARTIC) = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/%%DIRFECHA%%$prontus_varglb::DIR_PAG";
my ($RELDIR_LIST_DST) = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_LIST";
my ($RELDIR_LIST_TMP) = "$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_LIST";
my ($RELDIR_LIST_MACROS) = "$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_LIST_MACROS";
my (%EXT_PORT_TMP, %BUF_PLT, %BUF_PLT_LOOP, %MSGS, %LOADED_NAMES_PLT);
my ($CURR_DTIME) = &glib_hrfec_02::get_dtime_pack4();

my (%ART_XML_FIELDS, %ART_XDATA_FIELDS);

#if (&lib_maxrunning::maxExcedido(1)) {
#  die "[$CURR_DTIME] prontus_cron_taxport en proceso, se aborta ejecucion de [prontus_cron_taxport.cgi $FORM{'prontus'} $FORM{'params_especif'}]\n";
#}

# $prontus_varglb::TAXPORT_MAXARTICS = 500; # debug
use Time::HiRes qw ( time ); # debug

main: {
    my $ini_t = time; # debug

    &generar_lists();

    my $delta_t = time - $ini_t;
    #~ print STDERR "exec_time[$delta_t]\n"; # debug
};
# ---------------------------------------------------------------
sub generar_lists {

    # Conectar a BD
    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        print STDERR "ERROR: $msg_err_bd\n";
        exit;
    };
    $base->{mysql_auto_reconnect} = 1;
    $base->{InactiveDestroy} = 1;

    #~ precarga tabla de temas en hash global para uso posterior reiterado.
    %TABLA_SECC = &lib_tax::carga_tabla_seccion($base);
    %TABLA_TEM = &lib_tax::carga_tabla_temas($base);
    %TABLA_STEM = &lib_tax::carga_tabla_subtemas($base);

    &carga_nombase_plts();

    &carga_plantillas();

    foreach my $plt (keys %NOMBASE_PLTS) {

        if($CONTENT_PLTS{$plt}) {
            my $hash_ref = $CONFIG_PLTS{$plt};
            my %config = %$hash_ref;

            my $maxartics   = $config{'LIST_MAXARTICS'};
            #~ my $artxpags = $config{'LIST_ARTXPAG'};
            my $orden       = $config{'LIST_ORDEN'};
            my $seccion     = $config{'LIST_SECCION'};
            my $tema        = $config{'LIST_TEMA'};
            my $subtema     = $config{'LIST_SUBTEMA'};
            my $fids        = $config{'LIST_FIDS'};

            if($FORM{'params_especif'}) {

                next if(!&test_taxo($FORM{'seccion_especif'}, $seccion));
                next if(!&test_taxo($FORM{'tema_especif'}, $tema));
                next if(!&test_taxo($FORM{'subtema_especif'}, $subtema));

                if($FORM{'fid_especif'} eq '' || $fids ne '') {
                    my $res = grep(/^$FORM{'fid_especif'}$/, split(/,/, $fids));
                    unless($res) {
                        next;
                    }
                }
            }
            #~ print STDERR "Procesando: $seccion, $tema, $subtema, $fids... \n";
            &procesar_plantilla($seccion, $tema, $subtema, $fids, $plt, $maxartics, $orden, $base);
        } else {
            print STDERR "Plantilla vacia: $plt\n";
        }
    }

    $base->disconnect;
};

# ---------------------------------------------------------------
sub procesar_plantilla {
# Genera todas las portadas tax (de la 1..n) correspondientes
# a este nivel taxonomico, para todas las vistas declaradas y fids.

    my ($secc_id, $temas_id, $subtemas_id, $fids, $nombase_plt, $maxartics, $orden, $base) = @_;

    #TODO Queda pendiente el manejo de semáforos

    my (%filas);

    my $filtros = &crear_filtros_list($secc_id, $temas_id, $subtemas_id, $fids, $CURR_DTIME);
    # print STDERR "[$$] PROCESANDO LEVEL [$secc_id, $temas_id, $subtemas_id, $fid] - tot[$tot_artics]\n"; # - filtro[$filtros]\n";
    my ($secc_nom, $filler) = split (/\t\t/, $TABLA_SECC{$secc_id});

    my $sql = "select ART_ID, ART_FECHAP, ART_HORAP, ART_TITU, "
    . "ART_DIRFECHA, ART_EXTENSION, ART_TIPOFICHA, ART_IDTEMAS1, ART_BAJA from ART "
    . "%%FILTRO%% order by $orden LIMIT 0, $maxartics";

    if ($filtros ne '') {
        $sql =~ s/%%FILTRO%%/ where $filtros /;

    } else {
        $sql =~ s/%%FILTRO%%/$filtros/;
    };

    my ($art_id, $art_fecha, $art_horap, $art_titu, $art_dirfecha, $art_extension,
        $art_tipoficha, $art_idtemas1, $art_baja);
    #~ print STDERR "sql[$sql]\n";
    my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($art_id, $art_fecha, $art_horap, $art_titu,
                                                                $art_dirfecha, $art_extension,
                                                                $art_tipoficha, $art_idtemas1, $art_baja));

    my $tot_artics = &get_tot_artics($filtros, $base);
    my $nro_filas = 0;

    my $buffer = $CONTENT_PLTS{$nombase_plt};
    my $loop_plt;
    if ($buffer =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
        $loop_plt = $1;
    };
    if (!$loop_plt) {
        &write_pag($nombase_plt, $secc_id, $temas_id, $subtemas_id, $tot_artics, \%filas);
        print STDERR "Plantilla sin LOOP: $nombase_plt\n";
        return;
    }

    while ($salida->fetch) {
        $nro_filas++;

        # parsea esta fila en todas las multivistas
        my ($tem, $filler1, $filler2) = split (/\t\t/, $TABLA_TEM{$art_idtemas1});
        my $mv = '';

        my $fila_content;
        my ($auxref, $auxref2);

        # print STDERR "art[$art_id][$art_xml_fields{$art_id}]\n";
        ($fila_content, $auxref, $auxref2) = &lib_tax::generar_fila($RELDIR_ARTIC, $art_id, $art_extension, $loop_plt, $nro_filas, $tot_artics, $ART_XML_FIELDS{$art_id}, $ART_XDATA_FIELDS{$art_id});

        $ART_XML_FIELDS{$art_id} = $auxref if (! exists $ART_XML_FIELDS{$art_id}); # para no leer 2 veces un xml
        $ART_XDATA_FIELDS{$art_id} = $auxref2 if (! exists $ART_XDATA_FIELDS{$art_id}); # para no leer 2 veces un xml

        $filas{"$mv|$nombase_plt"} .= $fila_content;

    };
    #~ print "nombase_plt[$nombase_plt]\n";
    &write_pag($nombase_plt, $secc_id, $temas_id, $subtemas_id, $tot_artics, \%filas);
    $salida->finish;
};

# ---------------------------------------------------------------
sub write_pag {

    my ($nombase_plt, $secc_id, $temas_id, $subtemas_id, $tot_artics, $filas_hashref) = @_;
    my %filas = %$filas_hashref;

    my $pagina = $CONTENT_PLTS{$nombase_plt};
    if (!$pagina) {
        print STDERR "Plantilla vacia: $nombase_plt";
        return;
    }

    $pagina =~ s/%%_totartics%%/$tot_artics/ig;
    #~ my $key_hash = "$secc_id|$temas_id|$subtemas_id|$fid|$mv|$nombase_plt";
    # warn "$key_hash lista[$lista]";
    my ($nombase, $extension) = &lib_prontus::split_nom_y_extension($nombase_plt);
    $extension = '.' . $extension;
    #~ $pagina =~ s/%%LOOP%%(.*?)%%\/LOOP%%/$filas{"$mv|$nombase_plt"}/isg;
    $pagina =~ s/%%LOOP%%(.*?)%%\/LOOP%%/$filas{"|$nombase_plt"}/isg;
    #~ $pagina = &incluir_navbar($pagina, $secc_id, $temas_id, $subtemas_id, $RELDIR_LIST_DST, $extension, $nombase);
    #~ $pagina = &incluir_nrosdepag($tot_artics, $pagina, $nro_pag, $secc_id, $temas_id, $subtemas_id, $RELDIR_LIST_DST, $extension, $nombase);
    #~ $pagina =~ s/%%NOMSECC%%/$secc_nom/isg;
    # reemplazar nombre del prontus
    $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
    $pagina =~ s/%%_SERVER_NAME%%/$prontus_varglb::PUBLIC_SERVER_NAME/isg;


    #~ $tax_fixedurl = &lib_prontus::get_tax_link($tax_fixedurl, $mv);
    #~ $pagina =~ s/%%_FIXED_URL%%/$tax_fixedurl/isg;

    # Se parsean todas las marcas de seccion, tema y subtema.
    $pagina =~ s/%%_SECCION[1-3]%%/$secc_id/isg;
    $pagina =~ s/%%_TEMA[1-3]%%/$temas_id/isg;
    $pagina =~ s/%%_SUBTEMA[1-3]%%/$subtemas_id/isg;

    my ($secc_nom, $filler1, $filler2) = split (/\t\t/, $TABLA_SECC{$secc_id});
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
    my $fullpath_dir = "$prontus_varglb::DIR_SERVER$RELDIR_LIST_DST";

    &glib_fildir_02::check_dir($fullpath_dir) if (! -d $fullpath_dir);
    my $nomfile = "$fullpath_dir/" . $nombase_plt;
    #~ print STDERR "writing [$nomfile]\n";

    &glib_fildir_02::write_file($nomfile, $pagina);
    &lib_prontus::purge_cache($nomfile);


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
    $count_art = $prontus_varglb::LIST_MAXARTICS if ($count_art > $prontus_varglb::LIST_MAXARTICS);
    return $count_art;

};

# ---------------------------------------------------------------
sub carga_plantillas {

    my ($ruta_dir) = "$prontus_varglb::DIR_SERVER$RELDIR_LIST_TMP";
    my ($dir_macros) = "$prontus_varglb::DIR_SERVER$RELDIR_LIST_MACROS";

    foreach my $k (keys %NOMBASE_PLTS) {

        my $tmpl = "$ruta_dir/$k";
        if(-f $tmpl) {
            my $buffer = &glib_fildir_02::read_file($tmpl);
            $buffer = &lib_prontus::add_macros($buffer, $dir_macros);
            $CONTENT_PLTS{$k} = $buffer

        } else {
            print STDERR "Plantilla vacía: $ruta_dir/$k\n";
            $CONTENT_PLTS{$k} = '';
        };
    };
    &carga_config();
};

# ---------------------------------------------------------------
sub carga_nombase_plts {
# Obtiene nombres de las multiples plantillas, las lee siempre del /all

    my ($ruta_dir) = "$prontus_varglb::DIR_SERVER$RELDIR_LIST_TMP";

    #~ print STDERR "ruta_dir: $ruta_dir\n";
    if(! -d $ruta_dir) {
        print STDERR "\nEl directorio de plantillas no existe [$ruta_dir]\n";
        exit;
    }
    my @lisdir = &glib_fildir_02::lee_dir($ruta_dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y .. y lo que empiece con punto

    foreach my $k (@lisdir) {
        #~ print STDERR "NOMBASE_PLTS: $k\n";
        if ((-f "$ruta_dir/$k") && ($k =~ /^(\w+\.\w+)$/)) {
            $NOMBASE_PLTS{$1} = 1;
        }
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
# -------------------------------------------------------------------------#
sub carga_config {
# Busca, inicializa y elimina mensajes dentro de la plantilla.
# Carga hash de configuraciones: MAXARTICS,SECCION,TEMA,SUBTEMA,FIDS,ORDEN
#     <!-- CONFIG xxx = xxx -->
    my %config_default;
    $config_default{'LIST_MAXARTICS'} = $prontus_varglb::LIST_MAXARTICS;
    #~ $config_default{'LIST_ARTXPAG'} = $prontus_varglb::LIST_ARTXPAG;
    $config_default{'LIST_SECCION'} = '';
    $config_default{'LIST_TEMA'} = '';
    $config_default{'LIST_SUBTEMA'} = '';
    $config_default{'LIST_FIDS'} = '';
    $config_default{'LIST_ORDEN'} = $prontus_varglb::LIST_ORDEN;

    foreach my $k (keys %CONTENT_PLTS) {
        my %config = %config_default;
        my $plantilla = $CONTENT_PLTS{$k};
        while ($plantilla =~ /<!--\s*CONFIG\s*(\w+)\s*=\s*(.*?)\s*-->/sg) {
            my $name = $1;
            my $value = $2;
            if($name eq 'LIST_ORDEN') {
                $value = &get_taxport_orden($value);

            } elsif($name eq 'LIST_MAXARTICS') {
                $value =~ s/[^\d]//ig;
                $value = $prontus_varglb::LIST_MAXARTICS unless($value);

            } elsif($name eq 'LIST_SECCION' || $name eq 'LIST_TEMA' || $name eq 'LIST_SUBTEMA') {
                $value =~ s/[^\d,]//isg;
                $value =~ s/,{2,}/,/g;
                $value =~ s/^,+//g;
                $value =~ s/,+$//g;
            }
            $config{$name} = $value;
        }
        # Elimina mensajes de la plantilla.
        $plantilla =~ s/<!--\s*CONFIG\s*(\w+)\s*=\s*(.+?)\s*-->//sg;
        $CONTENT_PLTS{$k} = $plantilla;
        $CONFIG_PLTS{$k} = \%config;
    }

    #~ foreach my $plt (keys %CONFIG_PLTS) {
        #~ my %config = %{$CONFIG_PLTS{$plt}};
        #~ print "$plt\n";
        #~ foreach my $cfg (keys %config) {
            #~ print "\t$cfg -> ".$config{$cfg}."\n";
        #~ }
    #~ }
};

# ---------------------------------------------------------------
sub crear_filtros_list {
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
        $filtros .= "ART_IDSECC1 IN ($id_secc1)";
        $filtros .= " or ART_IDSECC2 IN ($id_secc1)" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
        $filtros .= " or ART_IDSECC3 IN ($id_secc1)" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
        $filtros .= ")";

        if ($id_tema1) { # Distinto de todos.
            if ($filtros ne '') {
                # $filtros .= " and (ART_IDTEMAS1 = \"$id_tema1\" or ART_IDTEMAS2 = \"$id_tema1\" or ART_IDTEMAS3 = \"$id_tema1\")";
                $filtros .= "and (";
                $filtros .= "ART_IDTEMAS1 IN ($id_tema1)";
                $filtros .= " or ART_IDTEMAS2 IN ($id_tema1)" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
                $filtros .= " or ART_IDTEMAS3 IN ($id_tema1)" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
                $filtros .= ")";
            };
            if ($id_subtema1) { # Distinto de todos.
                if ($filtros ne '') {
                    # $filtros .= " and (ART_IDSUBTEMAS1 = \"$id_subtema1\" or ART_IDSUBTEMAS2 = \"$id_subtema1\" or ART_IDSUBTEMAS3 = \"$id_subtema1\")";
                    $filtros .= "and (";
                    $filtros .= "ART_IDSUBTEMAS1 IN ($id_subtema1)";
                    $filtros .= " or ART_IDSUBTEMAS2 IN ($id_subtema1)" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
                    $filtros .= " or ART_IDSUBTEMAS3 IN ($id_subtema1)" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
                    $filtros .= ")";
                };
            };
        };
    };

    if ($fid) {
        my @arrfids = split /,/, $fid;
        my $str;
        foreach my $f (@arrfids) {
           $str = $str . "ART_TIPOFICHA = \"$f\" or ";
        }
        $str =~ s/ or $//;
        $filtros .= " and " if ($filtros);
        $filtros .= " ($str) ";
    };

    $filtros .= " and " if ($filtros);

    $filtros .= " (ART_FECHAPHORAP <= \"$dt_system$hhmm_system\") ";
    $filtros .= " and (ART_ALTA = \"1\") " if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS eq 'SI');

    if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
        $filtros .= " and ( (ART_FECHAEHORAE >= \"$dt_system$hhmm_system\") OR ( (ART_FECHAEHORAE < \"$dt_system$hhmm_system\") AND (ART_SOLOPORTADAS = \"1\") ) )";
    };

    return $filtros;

};
# ---------------------------------------------------------------
sub get_taxport_orden {

    my $taxport_orden = $_[0];
    my $orden_default = $_[1];

    my $taxport_orden_new;
    my $taxport_orden_err;

    if ($taxport_orden =~ /^(PUBLICACION|TITULAR|CREACION)\((ASC|DESC)\)$/) {
        if ($1 eq 'PUBLICACION') {
            $taxport_orden_new = "ART_FECHAP $2, ART_HORAP $2";
        } elsif ($1 eq 'TITULAR') {
            $taxport_orden_new = "ART_TITU $2";
        } elsif ($1 eq 'CREACION') {
            $taxport_orden_new = "ART_AUTOINC $2";
        } else {
            $taxport_orden_err = 1;
        };
    } else {
        $taxport_orden_err = 1;
    };

    if ($taxport_orden_err) {
        print STDERR "Error en CFG: seteo de variable TAXPORT_ORDEN contiene un valor no v&aacute;lido.<br>Valores posibles: 'PUBLICACION(ASC|DESC)', 'TITULAR(ASC|DESC)', 'CREACION(ASC|DESC)', Por omisi&oacute;n es: 'PUBLICACION(DESC)'\n";
        return $orden_default;
    };
    if(! $taxport_orden_new) {
        $taxport_orden_new = $orden_default;
    }

    return $taxport_orden_new;
}
# ---------------------------------------------------------------
sub valida_param {

    $FORM{'seccion_especif'} =~ s/[^\d]//g;

    $FORM{'tema_especif'} =~ s/[^\d]//g;

    $FORM{'subtema_especif'} =~ s/[^\d]//g;

    $FORM{'fid_especif'}  =~ s/[^\w]//g;
}
# ---------------------------------------------------------------
sub test_taxo {

    my ($secc, $strseccs) = @_;
    return 1 unless($secc);
    return 1 if($strseccs eq '');
    my $res = grep(/^$secc$/, split(/,/, $strseccs));
    if($res) {
        return 1;
    }
    return 0;
}
# -------------------------END SCRIPT----------------------
