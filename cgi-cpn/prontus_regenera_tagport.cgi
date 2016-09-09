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
# prontus_regenera_tagport.cgi

# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/.

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Script encargado de regenerar todas las portadas tagonómicas.
# Por un tema de performance, no debe usarse como cron. Debe usarse para eventuales
# migraciones u otros eventos por el estilo.
#
#
# $ARGV[0] : Nombre del Prontus (ej. prontus_noticias)
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 06/04/2016 - MPG - Primera Version, basado en prontus_regenera_taxport_jor.cgi
# 1.0.1 - 09/07/2016 - SCT - Se agrega paginación custom
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
use lib_tags;
use lib_tax;
use glib_hrfec_02;
use glib_dbi_02;
use glib_cgi_04;
use glib_fildir_02;
use strict;
use DBI;

# Soporta sólo 1 copia andando
use lib_maxrunning;
if (&lib_maxrunning::maxExcedido(1)) {
    print "Error: Servidor ocupado. Intente otra vez mas tarde.\n";
    exit;
};


# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%FORM, %TABLA_TAGS, %NOMBASE_PLTS, %CFG_FIL_TAGPORT, %TAGS2PROCESS, %FIDS2PROCESS);
my ($FILASXPAG, $base);
my $tagport_counter = 0;

$FORM{'prontus'} = $ARGV[0];
$FORM{'fid2process'} = $ARGV[1];

if ( (! -d "$prontus_varglb::DIR_SERVER") || ($prontus_varglb::DIR_SERVER eq '') )  {
    print "Error: Document root no valido.\n";
    exit;
};
if ( (! -d "$prontus_varglb::DIR_SERVER/$FORM{'prontus'}") || ($FORM{'prontus'} eq '')  || ($FORM{'prontus'} =~ /^\//) )  {
    print "\nError: Directorio del publicador no es valido.";
    print "\nDebe indicar el nombre del Prontus a procesar (ej: prontus_noticias), como parametro de esta CGI\n";
    exit;
};

my $DIR_TAGPORT = '/tag/port';
my $DIR_TAGPORT_MACRO = '/tag/macros';

# Carga variables de configuracion de prontus.
my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus'});
&lib_prontus::load_config( &lib_prontus::ajusta_pathconf($relpath_conf) );

my ($RELDIR_ARTIC) = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/%%DIRFECHA%%$prontus_varglb::DIR_PAG";
my ($RELDIR_PORT_DST) = "$prontus_varglb::DIR_CONTENIDO$DIR_TAGPORT";
my ($RELDIR_PORT_TMP) = "$prontus_varglb::DIR_TEMP$DIR_TAGPORT";
my ($RELDIR_PORT_MACROS) = "$prontus_varglb::DIR_TEMP$DIR_TAGPORT_MACRO";
my (%EXT_PORT_TMP, %BUF_PLT, %BUF_PLT_LOOP, %MSGS, %LOADED_NAMES_PLT);
my ($CURR_DTIME) = &glib_hrfec_02::get_dtime_pack4();



main:{
    my $ini_t = time; # debug
    # Conectar a BD
    $base = &conecta_db();

    $FILASXPAG = $prontus_varglb::TAGPORT_ARTXPAG;

    # Se cargan todos los tags, de manera inteligente
    &cargar_tagports();

    # Se cargan las plantillas
    &carga_nombase_plts();

    # Se gegeneran las tagport
    &generar_tagonomicas();

    $base->disconnect;
};

# ---------------------------------------------------------------
sub conecta_db {

    # Conectar a BD
    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        print "ERROR: $msg_err_bd\n";
        exit;
    };
    $base->{mysql_auto_reconnect} = 1;

    return $base;
};
# ---------------------------------------------------------------
sub cargar_tagports {
    # precarga tabla de tags en hash global para uso posterior reiterado.
    %TABLA_TAGS = &lib_tags::get_all_tags($base);
    %FIDS2PROCESS = &get_fids2process($base);

    # tag
    my $pid;
    my (@pid) = (); # PIDs de los procesos hijos.
    foreach my $tag_id (keys %TABLA_TAGS) {
        my ($tag_nom) = $TABLA_TAGS{$tag_id};
        if(! exists $TAGS2PROCESS{"$tag_id"}) {
            $TAGS2PROCESS{"$tag_id"} = 1;
        };
    };
};
# ---------------------------------------------------------------
# Obtiene fids para los cuales se generaran portadas tagonomicas.
# Estos son solo los que cuenten con plantilla tagonomica en el dir correspondiente:
# /<_prontus_id>/plantillas/tag/port/<_fid>[-<_mv>]/taxport[_<_seccion>][_<_tema>][_<_subtema>].<ext>
sub get_fids2process {

    my $base = $_[0];
    my %fids;
    my %fidswithtag;
    my $fid;

    foreach my $key (keys %prontus_varglb::FORM_PLTS) { # key = 'fid_general:General(general.php)'
        my $fid_name;
        next if ($key !~ /^(\w+) *:/);
        $fid_name = $1;
        $fids{$fid_name} = 1;
    };

    my $sql = "select ART.ART_TIPOFICHA from ART JOIN TAGSART where ART.ART_ID=TAGSART.TAGSART_IDART group by ART.ART_TIPOFICHA";
    my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($fid));
    while ($salida->fetch) {
        if($fids{$fid}) {
            $fidswithtag{$fid} = 1;
        };
    };

    # Si viene por parametro el fid, se utiliza solo ese.
    if ($FORM{'fid2process'}) {

        if (!defined $fids{$FORM{'fid2process'}}) {
            print "ERROR: El FID [$FORM{'fid2process'}] no existe en la configuracion de Prontus.\n";
            exit;
        }

        if (defined $fidswithtag{$FORM{'fid2process'}}) {
            return ($FORM{'fid2process'} => 1);
        } else {
            print "ERROR: No hay articulos con tagonomia con FID [$FORM{'fid2process'}].\n";
            exit;
        }
    }

    return %fidswithtag;
};


# ---------------------------------------------------------------
# Obtiene nombres de las multiples plantillas, las lee siempre del /all
sub carga_nombase_plts {

    my ($ruta_dir) = "$prontus_varglb::DIR_SERVER$RELDIR_PORT_TMP/all";
    &glib_fildir_02::check_dir($ruta_dir) if (! -d $ruta_dir);
    my @lisdir = &glib_fildir_02::lee_dir($ruta_dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..


    foreach my $k (@lisdir) {
        if ((-f "$ruta_dir/$k") && ($k =~ /^([a-z]+\.\w+)$/)) {
            $NOMBASE_PLTS{$1} = 1;
        };
    };

};


# ---------------------------------------------------------------
sub generar_tagonomicas {

    # Ver si existe col TAGS_NOM4VISTAS y si no, crearla.
    my $res_check_col = &glib_dbi_02::check_table_column($base, 'TAGS', 'TAGS_NOM4VISTAS', 'text');
    if (!$res_check_col) {
        print STDERR "ERROR: No se pudo crear la columna TAGS_NOM4VISTAS, DBI Error Code: [$DBI::err][$DBI::errstr]\n";
        exit;
    };

    foreach my $tag_id (keys %TAGS2PROCESS) {
        &generar_tagonomicas_thislevel($tag_id);
    };



};
# ---------------------------------------------------------------
# Genera todas las portadas tax (de la 1..n) correspondientes
# a este nivel taxonomico, para todas las vistas declaradas y fids.
sub generar_tagonomicas_thislevel {

    my ($tag_id) = @_;

    # si se invoca sin fid, considera el filtro sin fid
    $FIDS2PROCESS{''} = 1 if ($FORM{'fid2process'} eq '');

    # para uso normal desde el fid, en donde se invoca siempre con fid.
    # Entonces si viene tags_id, genera para esos tags con el fid, pero tb. para los tags sin fid especifico
    $FIDS2PROCESS{''} = 1 if ($FORM{'fid2process'});

    my %art_xml_fields;
    my %art_xdata_fields;

    my $dir_semaf = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/tagport_smf";
    &glib_fildir_02::check_dir($dir_semaf) if (! -d $dir_semaf);
    my $pid_propio = $$;

    foreach my $fid (keys %FIDS2PROCESS) {
        # Escribe los semaforos de los id levels q va a utilizar (en realidad solo cambia el fid)
        # y borra los escritos por otros procesos para este mismo level, para provocar q aborten
        my $id_level = $tag_id . '_' . $fid;
        my @files2delete = glob("$dir_semaf/$id_level" . '.*');

        foreach my $file2delete (@files2delete) {
            if ($file2delete !~ /\.$pid_propio$/) {
                unlink $file2delete;
                # print STDERR "\n[$$] hice abortar al: $file2delete !\n";
            };
        };
        &glib_fildir_02::write_file("$dir_semaf/$id_level.$pid_propio", '1');
    };

    # Obtiene nombre del tag y tb en las vistas
    my %tag_noms = &lib_tags::get_tag_noms($base, $tag_id); # ret. hash indexado por la vista y value=nombre
    foreach my $fid (keys %FIDS2PROCESS) {
        $tagport_counter++;
        my $id_level = $tag_id . '_' . $fid;
        if (-f "$dir_semaf/$id_level.$pid_propio") {
            # print STDERR "\n[$$] PROCESAR LEVEL[$id_level] iniciando\n";
        } else {
            # print STDERR "\n[$$] PROCESAR LEVEL[$id_level] hasta aca no mas llegamos!\n";
            return;
        };
        my $filtros = &genera_filtros_tagports($tag_id, $fid, $CURR_DTIME);
        my $tot_artics = &get_tot_artics($filtros, $base);
        print STDERR "[$tagport_counter]\tProcesando[$tag_id, $fid] - tot[$tot_artics]\n"; #"- filtro[$filtros]\n";

        my $sql = "select ART_ID, ART_FECHAP, ART_HORAP, ART_TITU, "
                . "ART_DIRFECHA, ART_EXTENSION, ART_TIPOFICHA from ART, TAGSART "
                . "%%FILTRO%% order by $prontus_varglb::TAGPORT_ORDEN LIMIT 0, $prontus_varglb::TAGPORT_MAXARTICS";

        if ($filtros ne '') {
            $sql =~ s/%%FILTRO%%/ where $filtros /;
        }
        else {
            $sql =~ s/%%FILTRO%%/$filtros/;
        };

        my ($art_id, $art_fecha, $art_horap, $art_titu, $art_dirfecha, $art_extension, $art_tipoficha);
        my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($art_id, $art_fecha, $art_horap, $art_titu,
                                                                    $art_dirfecha, $art_extension, $art_tipoficha));
        my $nro_filas = 0;
        my $nro_pag = 0;
        my %filas;
        # print STDERR "[$$] FETCHING:\n";
        while ($salida->fetch) {
            my $nro_pag_to_write;
            $nro_filas++;
            if (-f "$dir_semaf/$id_level.$pid_propio") {
                $nro_pag_to_write = $nro_pag + 1;
                # print STDERR "\r                   pag[$nro_pag_to_write] row[$nro_filas]";
                # sleep (1) if ($nro_filas > 98);
            } else {
                # print STDERR "\n[$$] FETCHING: hasta aca no mas llegamos!\n";
                return;
            };

            # parsea en todas las multivistas
            my $mv;
            my %vistas; # incluye las mv y la normal
            %vistas = %prontus_varglb::MULTIVISTAS;
            $vistas{''} = 1; # vista default
            foreach $mv (keys %vistas) {
                foreach my $nombase_plt (keys %NOMBASE_PLTS) {
                    # Obtiene plantilla, de acuerdo al nivel taxonomico especificado, fid y mv
                    my $loop_plt = &get_loop_plt($tag_id, $fid, $mv, $nombase_plt);
                    next if (!$loop_plt);
                    my $fila_content;
                    my ($auxref, $auxref2);

                    # print STDERR "art[$art_id][$art_xml_fields{$art_id}]\n";
                    ($fila_content, $auxref, $auxref2) = &lib_tax::generar_fila($RELDIR_ARTIC, $art_id, $art_extension, $loop_plt, $nro_filas, $tot_artics, $art_xml_fields{$art_id}, $art_xdata_fields{$art_id}, $nro_pag_to_write);

                    $art_xml_fields{$art_id} = $auxref if (! exists $art_xml_fields{$art_id}); # para no leer 2 veces un xml
                    $art_xdata_fields{$art_id} = $auxref2 if (! exists $art_xdata_fields{$art_id}); # para no leer 2 veces un xml
                    $filas{"$mv|$nombase_plt"} .= $fila_content;
                };
            };

            # escribir la pag actual y cambiar a la pagina siguiente
            if ($nro_filas >= $FILASXPAG) {
                $nro_pag++; # avanza pag
                &write_pag($fid, $tot_artics, $nro_pag, $tag_id, \%filas, \%tag_noms);
                $nro_filas = 0; # resetea conta de filas para empezar del ppio en la pagina que viene.
                %filas = ();
            };
        };


        $nro_pag++; # avanza pag
        &write_pag($fid, $tot_artics, $nro_pag, $tag_id, \%filas, \%tag_noms);


        $salida->finish;
        if (-f "$dir_semaf/$id_level.$pid_propio") {
            unlink "$dir_semaf/$id_level.$pid_propio";
            # print STDERR "\n[$$] PROCESAR LEVEL[$id_level] proceso completado OK!\n";
        };
    };
};


# ---------------------------------------------------------------
# Genera segmento variable del sql para encontrar los articulos.
# Aplica a portadas tax normales y a portadillas de calendarios taxonomicos
sub genera_filtros_tagports {

    my ($tag_id, $fid, $curr_dtime) = @_;
    my $fid_fil = $fid;

    if ($fid =~ /^fil_/) {
        $fid = '';
    };

    $curr_dtime =~ /^(\d{8})(\d\d\d\d)/;
    my $dt_system = $1;
    my $hhmm_system = $2;

    my ($filtros);

    if ($tag_id) {
        $filtros = "(ART_ID = TAGSART_IDART and TAGSART_IDTAGS = \"$tag_id\")";
    };

    if ($fid) {
        $filtros .= " and " if ($filtros);
        $filtros .= " (ART_TIPOFICHA = \"$fid\") ";
    };

    if ($fid_fil && defined $CFG_FIL_TAGPORT{$fid_fil}{'FIDS'}) {
        my @fidlist = @{$CFG_FIL_TAGPORT{$fid_fil}{'FIDS'}};
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

    if ($fid_fil && defined $CFG_FIL_TAGPORT{$fid_fil}{'FECHA_DESDE'} && $CFG_FIL_TAGPORT{$fid_fil}{'FECHA_DESDE'} ne '') {
        $filtros .= " (ART_FECHAP >= \"$CFG_FIL_TAGPORT{$fid_fil}{'FECHA_DESDE'}\") ";
    } else {
        $filtros .= " (ART_FECHAPHORAP <= \"$dt_system$hhmm_system\") ";
    };

    $filtros .= " and (ART_ALTA = \"1\") " if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS eq 'SI');

    if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
        $filtros .= " and ( (ART_FECHAEHORAE >= \"$dt_system$hhmm_system\") OR ( (ART_FECHAEHORAE < \"$dt_system$hhmm_system\") AND (ART_SOLOPORTADAS = \"1\") ) )";
    };

    return $filtros;

};
# ---------------------------------------------------------------
sub get_tot_artics {
    my ($filtros) = shift;
    my $base = shift;
    my ($sql, $salida, $tot);
    my ($count_art);
    $sql = "select count(ART_ID) from ART, TAGSART %%FILTRO%%";

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
    $count_art = $prontus_varglb::TAGPORT_MAXARTICS if ($count_art > $prontus_varglb::TAGPORT_MAXARTICS);
    return $count_art;

};

# ---------------------------------------------------------------
sub get_loop_plt {
    # Obtiene buffer del loop del tpl de la portada tipo tema, de acuerdo a s, t y st + fid y mv.
    my ($tag_id, $fid, $mv, $nombase_plt) = @_;
    my ($dir_macros) = "$prontus_varglb::DIR_SERVER$RELDIR_PORT_MACROS";

    # Si fue cargado el tpl, lo retorna
    my $key_hash = "$tag_id|$fid|$mv|$nombase_plt";
    return $BUF_PLT_LOOP{$key_hash} if ($BUF_PLT_LOOP{$key_hash});

    # Si no, lo obtiene.
    my $plt = &obtiene_plt($tag_id, $fid, $mv, $nombase_plt);

    return '' if (!$plt);
    # print STDERR "determinando plt para s[$secc_id]t[$temas_id]st[$subtemas_id]fid[$fid]mv[$mv] -> plt[$plt]\n";

    if ($LOADED_NAMES_PLT{$plt}) { # si ya fue leida esta plt para algun otro key_hash, lo saco de ahi
        my $key_hash_anterior = $LOADED_NAMES_PLT{$plt};
        $BUF_PLT_LOOP{$key_hash} = $BUF_PLT_LOOP{$key_hash_anterior};
        $BUF_PLT{$key_hash} = $BUF_PLT{$key_hash_anterior};
        return $BUF_PLT_LOOP{$key_hash};
    };

    my $buffer = &glib_fildir_02::read_file($plt);

    $buffer = &lib_prontus::add_macros($buffer, $dir_macros);

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
# Obtiene nombre del que sera el tpl de la portada tagonomica, de acuerdo a nombre de plantilla e id de tag
#  Se busca si existe una plantilla que se llame tagport.html
# La plantilla es del tipo:
# /<_prontus_id>/plantillas/tag/port/(all|<_fid>)[-<_mv>]/[<nom_plt>][_<tag_id>.<ext>
sub obtiene_plt {

    my ($tag_id, $fid, $mv, $nombase_plt) = @_;

    my ($dir_plt) = "$prontus_varglb::DIR_SERVER$RELDIR_PORT_TMP";
    &glib_fildir_02::check_dir($dir_plt) if (! -d $dir_plt);

    # Obtiene extension (con punto) de la plantilla a usar.
    my ($nombase, $ext_port_tmp) = &lib_prontus::split_nom_y_extension($nombase_plt);
    $ext_port_tmp = '.' . $ext_port_tmp;

    # deja guardada la extension de la plantilla, para usarla al grabar la pagina.
    my $key_hash = "$tag_id|$fid|$mv|$nombase_plt";
    $EXT_PORT_TMP{$key_hash} = $ext_port_tmp;

    # Intenta obtener plantilla para filtro por fid
    my ($plt);
    if ($fid) {
        my $dir_plt_fid = $dir_plt . "/$fid";
        if ($mv) {
            my $dir_plt_fid_vista = $dir_plt_fid . '-' . $mv;
            $plt = &obtienePltPorTag($tag_id, $dir_plt_fid_vista, $ext_port_tmp, $nombase);

            return $plt if (-f $plt);
            # return ''; # si no hay plantilla para la vista, retorna vacio
        } else {
            $plt = &obtienePltPorTag($tag_id, $dir_plt_fid, $ext_port_tmp, $nombase);
            return $plt if ( -f $plt);
        };
    };

    # Ahora la intenta obtener sin filtro de fid
    my $dir_plt_all = $dir_plt . '/all';

    if ($mv) {
        # Intenta con la vista
        my $dir_plt_all_vista = $dir_plt_all . '-' . $mv;
        $plt = &obtienePltPorTag($tag_id, $dir_plt_all_vista, $ext_port_tmp, $nombase);
        return $plt if (-f $plt);
        return ''; # si no hay plantilla para la vista, retorna vacio
    } else {
        # intenta obtener plantilla estandar
        $plt = &obtienePltPorTag($tag_id, $dir_plt_all, $ext_port_tmp, $nombase);
        return $plt if (-f $plt);
    };

    # No se enontro ninguna plantilla
    return '';

};
# ---------------------------------------------------------------
# Obtiene nombre de plantilla taxonomica, de acuerdo a nombre y tag_id
#  Se busca si existe una plantilla que se llame <nom_plt>_<tag_id>.<ext>
#  Si no existe, se usa tagport.<ext>
sub obtienePltPorTag {
    my ($tag_id, $ruta_dir, $ext_port_tmp, $nombase) = @_;
    my $tpl;

    # Busca de la plantilla mas especifica a la mas general
    $tpl = "$ruta_dir/$nombase\_$tag_id" . $ext_port_tmp;
    return $tpl if (-f $tpl);

    $tpl = "$ruta_dir/$nombase$ext_port_tmp";
    return $tpl if (-f $tpl);

    # return $ruta_dir;
    return '';

};


# ---------------------------------------------------------------
sub write_pag {

    my ($fid, $tot_artics, $nro_pag, $tag_id, $filas_hashref, $tag_noms_hashref) = @_;
    my %filas = %$filas_hashref;
    my %tag_noms = %$tag_noms_hashref;

    # escribe pagina en todas las vistas incluida la normal
    my %vistas; # incluye las mv y la normal
    %vistas = %prontus_varglb::MULTIVISTAS;
    $vistas{''} = 1;
    my $mv;
    foreach $mv (keys %vistas) {
        foreach my $nombase_plt (keys %NOMBASE_PLTS) {
            next if ((!$filas{"$mv|$nombase_plt"}) && ($nro_pag > 1)); # para evitar pagina sobrante sin items
            # Obtiene plantilla, de acuerdo al nivel taxonomico especificado, fid y mv
            my $pagina = &get_buffer_plt($tag_id, $fid, $mv, $nombase_plt);
            next if (!$pagina);

            # Solo para filtros. Si estan configuradas las plantillas, solo se consideran esas.
            if ($fid =~ /^fil_/ && defined $CFG_FIL_TAGPORT{$fid}{'PLANTILLAS'} && !defined $CFG_FIL_TAGPORT{$fid}{'PLANTILLAS'}{$nombase_plt}) {
                next;
            };

            ($pagina, $MSGS{"$mv|$nombase_plt"}) = &carga_mensajes($pagina); # 1.8
            $pagina =~ s/%%_totartics%%/$tot_artics/ig;
            my $key_hash = "$tag_id|$fid|$mv|$nombase_plt";
            # warn "$key_hash lista[$lista]";
            my $reldir_port_dst = &obtieneRelDirDestino($fid, $mv);
            my ($nombase, $extension) = &lib_prontus::split_nom_y_extension($nombase_plt);

            $pagina =~ s/%%_plt_nom%%/$nombase/isg;
            $pagina =~ s/%%_plt_ext%%/$extension/isg;
            $pagina =~ s/%%_tag_fid%%/$fid/isg if ($fid);
            $pagina =~ s/%%_tag_fid%%/all/isg if (!$fid);

            $extension = '.' . $extension;
            $pagina =~ s/%%LOOP%%(.*?)%%\/LOOP%%/$filas{"$mv|$nombase_plt"}/isg;
            # $pagina = &incluir_navbar($pagina, $tag_id, $mv, $reldir_port_dst, $extension, $nombase);
            $pagina = &incluir_nrosdepag($tot_artics, $pagina, $nro_pag, $tag_id, $mv, $reldir_port_dst, $extension, $nombase);

            # reemplazar nombre del prontus
            $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
            $pagina =~ s/%%_SERVER_NAME%%/$prontus_varglb::PUBLIC_SERVER_NAME/isg;

            $pagina =~ s/%%_nropagina%%/$nro_pag/isg;
            $pagina =~ s/%%_vista%%/$mv/isg;

            $pagina =~ s/%%_tag_id%%/$tag_id/isg;

            my $tag_nom = $tag_noms{$mv};
            $pagina =~ s/%%_tag_nom%%/$tag_nom/isg;

            my %claves = ('_nropagina' => $nro_pag, '_vista' => $mv, '_tag_id' => $tag_id,
                    '_tag_nom' => $tag_nom, '_tag_fid' => $fid);

            $pagina = &lib_prontus::procesa_condicional($pagina, \%claves);

            my $path_include = &lib_prontus::get_path_croncgi();
            $pagina = &lib_prontus::parser_custom_function($pagina, $path_include);

            $pagina = &lib_prontus::parse_includes($prontus_varglb::DIR_SERVER, $pagina);

            $pagina =~ s/%%.*?%%//isg;

            # Escribe pagina
            my $fullpath_dir = "$prontus_varglb::DIR_SERVER$reldir_port_dst";

            &glib_fildir_02::check_dir($fullpath_dir) if (! -d $fullpath_dir);
            my $k = "$fullpath_dir/$nombase" . '_'
                                        . $tag_id
                                        . '_' . $nro_pag
                                    . $extension;
            ## debug
            #if (! exists $HASH_FILES{$k}) {
            #    $HASH_FILES{$k} = 1;
            #} else {
            #    print STDERR "escrito de nuevo!![$k]\n";
            #};

            &glib_fildir_02::write_file($k, $pagina);

            if ($prontus_varglb::CACHE_PURGE_TAGPORT eq 'SI') {
                if ($prontus_varglb::CACHE_PURGE_TAGPORT_MV eq 'SI') {
                    &lib_prontus::purge_cache($k);
                } else {
                    # Si está desactivada la opción de hacer purge a la vistas, solo se hace a la principal.
                    if ($mv eq '') {
                        &lib_prontus::purge_cache($k);
                    }
                }
            }
            # print STDERR "writing [$k]\n";

        };

    };

};
# ---------------------------------------------------------------
# Obtiene buffer del tpl de la portada tagonomica, de acuerdo a nombre y tag_id.
sub get_buffer_plt {
    my ($tag_id, $fid, $mv, $nombase_plt) = @_;
    my ($dir_macros) = "$prontus_varglb::DIR_SERVER$RELDIR_PORT_MACROS";

    # Si fue cargado el tpl, lo retorna
    my $key_hash = "$tag_id|$fid|$mv|$nombase_plt";
    return $BUF_PLT{$key_hash} if ($BUF_PLT{$key_hash});

    # Si no, lo obtiene.
    my $plt = &obtiene_plt($tag_id, $fid, $mv, $nombase_plt);
    return '' if (!$plt);
    print STDERR "\tplt[$plt]\n";

    # si ya fue leida esta plt para algun otro key_hash, lo saco de ahi para no leer de nuevo de FS
    if ($LOADED_NAMES_PLT{$plt}) {
        my $key_hash_anterior = $LOADED_NAMES_PLT{$plt};
        $BUF_PLT_LOOP{$key_hash} = $BUF_PLT_LOOP{$key_hash_anterior};
        $BUF_PLT{$key_hash} = $BUF_PLT{$key_hash_anterior};
        return $BUF_PLT{$key_hash};
    };

    my $buffer = &glib_fildir_02::read_file($plt);

    $buffer = &lib_prontus::add_macros($buffer, $dir_macros);


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
# -------------------------------------------------------------------------#
# Busca, inicializa y elimina mensajes dentro de la plantilla.
# Carga hash de mensajes
#     <!-- MSG xxx = xxx -->
sub carga_mensajes {

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
# Obtiene directorio de destino (relativo al doc root) donde sera almacenada
# la portada taxonomica generada
sub obtieneRelDirDestino {
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
sub incluir_nrosdepag {
    my ($tot_artics, $pagina, $nro_pag, $tag_id, $mv, $reldir_port_dst, $extension, $nombase) = @_;
    my $msgs_aux = $MSGS{"$mv|$nombase$extension"};
    my %msgs = %$msgs_aux;

    my ($tpl_nropag) = '<a href="%%lnk%%">%%cnro_pag%%</a>';
    my ($tpl_nropag2) = '<span class="actual">%%cnro_pag%%</span>';
    my ($tpl_separador) = '...';

    my $cnro_pag = 0;
    my $html_nros_pag = '';
    my $i;

    # Carga configuaracion.
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

    my $nro_paginas_totales = ceil($tot_artics / $prontus_varglb::TAGPORT_ARTXPAG);
    my ($ini, $fin, $nextlink, $prevlink);

    $ini = 1;
    $fin = $nro_paginas_totales;

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
                    . $tag_id
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
# -------------------------END SCRIPT----------------------
