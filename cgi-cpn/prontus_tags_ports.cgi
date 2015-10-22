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
# prontus_tags_ports.cgi

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
use glib_fildir_02;
use Artic;
use lib_tax;
use strict;
use DBI;

close STDOUT;
# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my ($LOOP, %FORM, $NOM_PRONTUS, %NOM_TAGS);
my %NOMBASE_PLTS;
my %CFG_FIL_TAGPORT;
# my %HASH_FILES;
my ($FILASXPAG);

if ( (! -d "$prontus_varglb::DIR_SERVER") || ($prontus_varglb::DIR_SERVER eq '') )  {
  print STDERR "\nError: Document root no valido.\n\nComo primer parametro debe indicar el path fisico al directorio raiz del servidor web, ejemplo: /sites/misitio/web \n";
  exit;
};
$FORM{'prontus'} = $ARGV[0]; # obligatorio
$FORM{'tags_id'} = $ARGV[1]; # obligatorio, uno o mas IDs separados por /
$FORM{'fid_especif'} = $ARGV[2]; # optativo

&valida_param();

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


# $prontus_varglb::TAGPORT_MAXARTICS = 500; # debug
# $prontus_varglb::TAGPORT_ARTXPAG = 5; # debug
use Time::HiRes qw ( time ); # debug

# ---------------------------------------------------------------
main:{
  my $ini_t = time; # debug
  $FILASXPAG = $prontus_varglb::TAGPORT_ARTXPAG;
  &generar_tagonomicas();
  my $delta_t = time - $ini_t;
  # print STDERR "exec_time[$delta_t]\n"; # debug

};
# ---------------------------------------------------------------
sub generar_tagonomicas {

    # Conectar a BD
    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        print STDERR "ERROR: $msg_err_bd\n";
        exit;
    };
    $base->{mysql_auto_reconnect} = 1;
    $base->{InactiveDestroy} = 1;

    &carga_nombase_plts();

    my %fids2process = &get_fids2process();
    my @tags2process = split(/ *\/ */, $FORM{'tags_id'});

    # Ver si existe col TAGS_NOM4VISTAS y si no, crearla.
    my $res_check_col = &glib_dbi_02::check_table_column($base, 'TAGS', 'TAGS_NOM4VISTAS', 'text');
    if (!$res_check_col) {
        print STDERR "ERROR: No se pudo crear la columna TAGS_NOM4VISTAS, DBI Error Code: [$DBI::err][$DBI::errstr]\n";
        exit;
    };

    foreach my $tag_id (@tags2process) {
        &generar_tagonomicas_thislevel($tag_id, \%fids2process, $base);
    };

    $base->disconnect;

};

# ---------------------------------------------------------------
sub get_tag_noms {
    my $base = shift;
    my $tag_id = shift;
    my %tag_noms;

    my $sql = "select TAGS_TAG, TAGS_NOM4VISTAS from TAGS where TAGS_ID = '$tag_id'";
    my $tag;
    my $nom4vistas;
    my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($tag, $nom4vistas));
    while ($salida->fetch) {
        $tag_noms{''} = &lib_prontus::escape_html($tag); # nombre en la vista default o ppal
        while ($nom4vistas =~ /(^|\n)(\w+)\t(.*?)($|\n)/sg) {
            my $vista = $2;
            my $nom = $3;
            $tag_noms{$vista} = &lib_prontus::escape_html($nom); # nombre en cada vista
        };
    };
    $salida->finish;
    return %tag_noms;
};

# ---------------------------------------------------------------
sub get_tpl {
# Obtiene nombre del q sera el tpl de la portada, es el primer archivo q se encuentre.
    my ($ruta_dir) = $_[0];
    my (@lisdir, $k);
    &glib_fildir_02::check_dir($ruta_dir) if (! -d $ruta_dir);
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
sub generar_tagonomicas_thislevel {
# Genera todas las portadas tax (de la 1..n) correspondientes
# a este nivel taxonomico, para todas las vistas declaradas y fids.


    my ($tag_id, $ref_hash, $base) = @_;

    my %fids2process = %$ref_hash;
    # si se invoca sin fid, considera el filtro sin fid
    $fids2process{''} = 1 if ($FORM{'fid_especif'} eq '');

    # para uso normal desde el fid, en donde se invoca siempre con fid. Entonces si viene tags_id, genera para esos tags con el fid, pero tb. para los tags sin fid especifico
    $fids2process{''} = 1 if ($FORM{'tags_id'});

    my %art_xml_fields;
    my %art_xdata_fields;

    my $dir_semaf = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/tagport_smf";
    &glib_fildir_02::check_dir($dir_semaf) if (! -d $dir_semaf);
    my $pid_propio = $$;

    foreach my $fid (keys %fids2process) {
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
    my %tag_noms = &get_tag_noms($base, $tag_id); # ret. hash indexado por la vista y value=nombre

    foreach my $fid (keys %fids2process) {
        my $id_level = $tag_id . '_' . $fid;
        if (-f "$dir_semaf/$id_level.$pid_propio") {
            # print STDERR "\n[$$] PROCESAR LEVEL[$id_level] iniciando\n";
        } else {
            # print STDERR "\n[$$] PROCESAR LEVEL[$id_level] hasta aca no mas llegamos!\n";
            return;
        };
        my $filtros = &genera_filtros_tagports($tag_id, $fid, $CURR_DTIME);
        my $tot_artics = &get_tot_artics($filtros, $base);
        # print STDERR "[$$] PROCESANDO LEVEL [$tag_id, $fid] - tot[$tot_artics]\n"; # - filtro[$filtros]\n";

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
sub get_buffer_plt {
    # Obtiene buffer del tpl de la portada tipo tema, de acuerdo a s, t y st.
    my ($tag_id, $fid, $mv, $nombase_plt) = @_;
    my ($dir_macros) = "$prontus_varglb::DIR_SERVER$RELDIR_PORT_MACROS";

    # Si fue cargado el tpl, lo retorna
    my $key_hash = "$tag_id|$fid|$mv|$nombase_plt";
    return $BUF_PLT{$key_hash} if ($BUF_PLT{$key_hash});

    # Si no, lo obtiene.
    my $plt = &obtiene_plt($tag_id, $fid, $mv, $nombase_plt);

    return '' if (!$plt);

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

    my ($tag_id, $fid, $mv, $nombase_plt) = @_;

    my ($dir_plt) = "$prontus_varglb::DIR_SERVER$RELDIR_PORT_TMP";
    &glib_fildir_02::check_dir($dir_plt) if (! -d $dir_plt);
    # Obtiene extension (con punto) de la plantilla a usar.
    my ($nombase, $ext_port_tmp) = &lib_prontus::split_nom_y_extension($nombase_plt);
    $ext_port_tmp = '.' . $ext_port_tmp;

    # deja guardada la extension de la plantilla, para usarla al grabar la pagina.
    my $key_hash = "$tag_id|$fid|$mv|$nombase_plt";
    $EXT_PORT_TMP{$key_hash} = $ext_port_tmp;

    my ($plt);
    # Intenta obtener plantilla para filtro por fid
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
sub carga_nombase_plts {
# Obtiene nombres de las multiples plantillas, las lee siempre del /all

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
sub obtienePltPorTag {
# Obtiene nombre de plantilla taxonomica, de acuerdo a s, t y st.
#  O sea, si taxonomia de entrada es:
#  seccion=sN
#  tema=tN
#  subtema=stN
#  Se busca si existe una plantilla que se llame taxport_sN_tN_stN.<ext>
#  Si no existe, se busca taxport_sN_tN.<ext>
#  Si no existe, se busca taxport_sN.<ext>
#  Si no existe, se usa taxport.<ext>
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
#            # debug
#            if (! exists $HASH_FILES{$k}) {
#                $HASH_FILES{$k} = 1;
#            } else {
#                print STDERR "escrito de nuevo!![$k]\n";
#            };



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
#sub incluir_navbar {
#    my ($pagina, $secc_id, $temas_id, $subtemas_id, $mv, $reldir_port_dst, $extension, $nombase) = @_;
#    # La navbar
#    my $secc_tema_stema_nom;
#    # secc
#    # my ($secc_nom, $secc_port) = &get_nombreyport('SECC', $secc_id, 'seccion', $mv); # rotulos tax
#    my ($secc_nom, $secc_port, $secc_nom4vistas) = split (/\t\t/, $TABLA_SECC{$secc_id});
#    $secc_nom = &lib_prontus::get_nomtax_envista($mv, $secc_nom4vistas) if ($mv);
#    $secc_nom = &lib_prontus::escape_html($secc_nom);
#
#    my $lnk_secc;
#    if ($secc_port) {
#        $lnk_secc = &lib_prontus::get_tax_link($secc_port);
#    }
#    else {
#        # $lnk_secc = "/$prontus_varglb::DIR_CGI_PUBLIC/prontus_taxport_lista.cgi?seccion=$secc_id&amp;_REL_PATH_PRONTUS=$FORM{'prontus'}&amp;_MV=$mv";
#        $lnk_secc = "$reldir_port_dst/$nombase" . '_'
#        . $secc_id
#        . '_'
#        . '_'
#        . '_' . '1'
#        . $extension;
#    };
#    $secc_tema_stema_nom = "<a href='$lnk_secc'>$secc_nom</a>";
#    # warn "slink[$secc_tema_stema_nom]";
#
#    # tem
#    # my ($tem_nom, $tem_port) = &get_nombreyport('TEMAS', $temas_id, 'tema-' . $secc_id, $mv); # rotulos tax
#    my ($tem_nom, $tem_port, $filler1, $tem_nom4vistas) = split (/\t\t/, $TABLA_TEM{$temas_id});
#    $tem_nom = &lib_prontus::get_nomtax_envista($mv, $tem_nom4vistas) if ($mv);
#    $tem_nom = &lib_prontus::escape_html($tem_nom);
#
#    if ($tem_nom) {
#        my $lnk_tem;
#        if ($tem_port) {
#            $lnk_tem = &lib_prontus::get_tax_link($tem_port);
#        }
#        else {
#            # $lnk_tem = "/$prontus_varglb::DIR_CGI_PUBLIC/prontus_taxport_lista.cgi?seccion=$secc_id&amp;tema=$temas_id&amp;_REL_PATH_PRONTUS=$FORM{'prontus'}&amp;_MV=$mv"; # rotulos tax
#            $lnk_tem = "$reldir_port_dst/$nombase" . '_'
#            . $secc_id
#            . '_' . $temas_id
#            . '_'
#            . '_' . '1'
#            . $extension;
#
#        };
#        $secc_tema_stema_nom .= " / <a href='$lnk_tem'>$tem_nom</a>";
#        # warn "tlink[$secc_tema_stema_nom]";
#    };
#
#    # stem
#    # my ($stem_nom, $stem_port) = &get_nombreyport('SUBTEMAS', $subtemas_id, 'subtema-' . $temas_id, $mv); # rotulos tax
#    my ($stem_nom, $stem_port, $filler2, $stem_nom4vistas) = split (/\t\t/, $TABLA_STEM{$subtemas_id});
#    $stem_nom = &lib_prontus::get_nomtax_envista($mv, $stem_nom4vistas) if ($mv);
#    $stem_nom = &lib_prontus::escape_html($stem_nom);
#
#    if ($stem_nom) {
#        my $lnk_stem;
#        if ($stem_port) {
#            $lnk_stem = &lib_prontus::get_tax_link($stem_port);
#        }
#        else {
#            # $lnk_stem = "/$prontus_varglb::DIR_CGI_PUBLIC/prontus_taxport_lista.cgi?seccion=$secc_id&amp;tema=$temas_id&amp;subtema=$subtemas_id&amp;_REL_PATH_PRONTUS=$FORM{'prontus'}&amp;_MV=$mv"; # rotulos tax
#            $lnk_stem = "$reldir_port_dst/$nombase" . '_'
#            . $secc_id
#            . '_' . $temas_id
#            . '_' . $subtemas_id
#            . '_' . '1'
#            . $extension;
#        };
#        $secc_tema_stema_nom .=  "/ <a href='$lnk_stem'>$stem_nom</a>";
#        # warn "stlink[$secc_tema_stema_nom]";
#    };
#
#    $pagina =~ s/%%_SECC_TEMA_STEMA_NOM%%/$secc_tema_stema_nom/isg;
#    return $pagina;
#
#};
# ---------------------------------------------------------------
sub incluir_nrosdepag {
    my ($tot_artics, $pagina, $nro_pag, $tag_id, $mv, $reldir_port_dst, $extension, $nombase) = @_;
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
sub valida_param {
    my $sintaxis = 'prontus_tags_ports.cgi {<prontus_id>} {<id tags separados por slash (/)>} [<fid>]';

    if ( (! -d "$prontus_varglb::DIR_SERVER/$FORM{'prontus'}") || ($FORM{'prontus'} eq '')  || ($FORM{'prontus'} =~ /^\//) )  {
        print STDERR "\nError: Directorio del publicador no es valido.";
        print STDERR "\nDebe indicar el nombre del Prontus a procesar (ej: prontus_noticias), como primer parametro de esta CGI\nSintaxis: $sintaxis\n";
        exit;
    };

    if ($FORM{'tags_id'} !~ /^[0-9]+(\/[0-9]+)*$/) {
        print STDERR "\nprontus_tags_ports.cgi: Ids de tags no es válido. Se aborta ejecucion.\nSintaxis: $sintaxis\n";
        exit;
    };

    if ($FORM{'fid_especif'} !~ /^[\w\-\.]*$/) {
        print STDERR "\nprontus_tags_ports.cgi: Fid no es válido. Se aborta ejecucion.\nSintaxis: $sintaxis\n";
        exit;
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
# Obtiene fids para los cuales se generaran portadas tagonomicas.
# Estos son solo los que cuenten con plantilla tagonomica en el dir correspondiente:
# /<_prontus_id>/plantillas/tag/port/<_fid>[-<_mv>]/tagport[_<_tag_id>].<ext>

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
                my $plt = &get_tpl($dir);
                next if ( (!-f "$dir/$plt") || (!$plt));
                $fids{$fid_name} = 1;
            };
        };
    };

    # Se agregan como fids los filtros para usar la misma logica.
    my @listado_filtros = &get_tagport_fil();

    foreach my $fil (@listado_filtros) {
        $fids{$fil} = $1;
    };

    return %fids;

};

#-----------------------------------------------------------------------
sub get_tagport_fil {
    my ($ruta_dir) = "$prontus_varglb::DIR_SERVER$RELDIR_PORT_TMP";
    my @listado = glob("$ruta_dir/fil_*");
    my @filtros;

    foreach my $dir (@listado) {
        if ($dir =~ /fil_(.*?)$/) {
            push @filtros, "fil_" . $1;
            &cargar_fil_cfg("$dir/filtros.cfg", "fil_" . $1);
        };

    };

    return @filtros;
};

#-----------------------------------------------------------------------
sub cargar_fil_cfg {
    my $file = $_[0];
    my $fil = $_[1];
    my $cfg = &glib_fildir_02::read_file($file);

    return if (exists $CFG_FIL_TAGPORT{$fil}); # para no cargarlo dos veces.

    if ($cfg =~ m/\s*TAGPORT_FIDS\s*=\s*("|')(.*?)("|')/s) {
        my $value = $2;

        # Se limpian los espacios.
        $value =~ s/\s+/ /sg;
        $value =~ s/^\s//sg;
        $value =~ s/\s$//sg;

        $value =~ s/[^a-zA-Z0-9_,]//sg; # dejar solo caracteres permitidos

        my @valores = split(',', $value);

        $CFG_FIL_TAGPORT{$fil}{'FIDS'} = \@valores;

        #print STDERR "CFG_FIL_TAGPORT! fil[$fil] value[$value]\n";
    };

    if ($cfg =~ m/\s*TAGPORT_PLANTILLAS\s*=\s*("|')(.*?)("|')/s) {
        my $value = $2;

        # Se limpian los espacios.
        $value =~ s/\s+/ /sg;
        $value =~ s/^\s//sg;
        $value =~ s/\s$//sg;

        $value =~ s/[^a-zA-Z0-9_\-,\.]//sg; # dejar solo caracteres permitidos

        my @valores = split(',', $value);

        foreach my $tpl (@valores) {
            $CFG_FIL_TAGPORT{$fil}{'PLANTILLAS'}{$tpl} = 1;
        };

        #print STDERR "CFG CFG_FIL_TAGPORT! fil[$fil] value[$value]\n";
    };

    if ($cfg =~ m/\s*TAGPORT_FECHA_DESDE\s*=\s*("|')(.*?)("|')/s) {
        my $value = $2;

        # Se limpian los espacios.
        $value =~ s/\s+/ /sg;
        $value =~ s/^\s//sg;
        $value =~ s/\s$//sg;

        $value =~ s/[^0-9]//sg; # dejar solo caracteres permitidos, numeros.

        $value = '' if ($value !~ /^(\d{8})$/); # formato debe ser YYYYMMDD

        $CFG_FIL_TAGPORT{$fil}{'FECHA_DESDE'} = $value;

        #print STDERR "CFG CFG_FIL_TAGPORT! fil[$fil] value[$value]\n";
    };

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
sub genera_filtros_tagports {
# Genera segmento variable del sql para encontrar los articulos.
# Aplica a portadas tax normales y a portadillas de calendarios taxonomicos

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

# -------------------------END SCRIPT----------------------
