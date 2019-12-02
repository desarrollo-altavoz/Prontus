#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

#-------------------------------COMENTARIO GLOBAL---------------
#---------------------------------------------------------------
# PROPOSITO.
#-----------
# Funciones para generar la taxonomia.

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 01   : 12/2003 - YCH - Primera version.
# 1.1   : 01/2004 - YCH - Adaptaciones DRs.
# 1.2.0 - 28/07/2015 - JOR - Ordena codigo
#                          - Se agrega total de articulos a relacionados.

#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package lib_tax;

use glib_dbi_02;
use glib_fildir_02;
use glib_hrfec_02;
use strict;
use prontus_varglb;
use lib_prontus;
use Artic;
use DBI;
use POSIX qw(strftime ceil);

# Limite maximo permitido.
our $MAX_LIMIT = 50;
our $RELDIR_ARTIC;

our $RELDIR_ARTIC_RELAC;
our $NUM_RELAC_DEFAULT;

our $RELDIR_DST_ARTIC_RELAC;
our $CONTROLAR_ALTA_ARTICULOS;
our %CFG_FIL_TAXPORT;
# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub set_vars {
    my ($dir_contenido, $dir_artic, $dir_pag, $dir_temp, $dir_taxonomia, $num_relac_default, $controlar_alta_articulos) = @_;

    $RELDIR_ARTIC = $dir_contenido . $dir_artic . '/%%DIRFECHA%%' . $dir_pag;

    $RELDIR_ARTIC_RELAC = $dir_temp . $dir_taxonomia;

    $RELDIR_DST_ARTIC_RELAC = $dir_contenido . $dir_taxonomia;

    $NUM_RELAC_DEFAULT = $num_relac_default;

    $CONTROLAR_ALTA_ARTICULOS = $controlar_alta_articulos;

};

# --------------------------------------------------------------------
sub get_taxonomia {
    # Obtiene seccion, tema, stema del articulo desde la base de datos.
    my ($id) = $_[0];
    my ($base) = $_[1];
    my ($nivel) = $_[2];
    my ($secc, $tem, $stem);

    $nivel = 1 if (!$nivel);
    $nivel = 3 if ($nivel > 3);

    my $sql = "select ART_IDSECC$nivel, ART_IDTEMAS$nivel, ART_IDSUBTEMAS$nivel from ART where ART_ID = '$id'";
    my $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($secc, $tem, $stem));

    $salida->fetch;
    $salida->finish;

    if ($secc) {
        $tem = '0' if ($tem eq '');
        $stem = '0' if ($stem eq '');

        return ($secc, $tem, $stem);
        } else {
            return ('-1','0','0');
        };
    };

# ---------------------------------------------------------------
sub get_tot_artics {
    my ($filtros) = shift;
    my $base = shift;
    my $maxartics = shift;
    my ($sql, $salida, $tot);
    my ($count_art);
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
    $count_art = $maxartics if ($count_art > $maxartics);

    return $count_art;
};

# ---------------------------------------------------------------
sub generar_relacionados {
    my ($id_secc1, $id_tema1, $id_subtema1, $base, $mv) = @_;

    if ($id_secc1 eq '0') {
        $id_secc1 = '';
    }
    if ($id_tema1 eq '0') {
        $id_tema1 = '';
    }
    if ($id_subtema1 eq '0') {
        $id_subtema1 = '';
    }

    # Procesa Plantillas que hayan en el dir.
    my ($plantilla, $pagina, $loop, $lista);
    my ($ruta_dir) = $prontus_varglb::DIR_SERVER . $RELDIR_ARTIC_RELAC;

    $ruta_dir =~ s/\/taxonomia\/pags/\/taxonomia\/pags-$mv/ if ($mv);

    my (@lisdir) = &glib_fildir_02::lee_dir($ruta_dir) if (-d $ruta_dir);
    my ($limit) = $NUM_RELAC_DEFAULT;

    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

    foreach my $k (@lisdir) {
        if (-f "$ruta_dir/$k") {
            # print STDERR "DIR[$ruta_dir/$k]\n";
            $plantilla = "$ruta_dir/$k";
            $pagina = &glib_fildir_02::read_file($plantilla);

            if ($pagina =~ /%%_NUM_RELAC=(\d+)%%/is) {
                $limit = $1;
            }

            # %%_TAX_LEVEL=seccion-tema-subtema%%
            my $taxlevel;
            if ($pagina =~ /%%_TAX_LEVEL=(seccion|seccion-tema|seccion-tema-subtema)%%/i) {
                $taxlevel = $1;
            } else {
                $taxlevel = 'seccion-tema-subtema'; # lo por defecto
            }

            $pagina =~ s/%%_TAX_LEVEL=[\w\-]+%%//ig; # borra marca
            $pagina =~ s/%%_NUM_RELAC=.*?%%//ig; # borra marca

            my ($exclude_port, $exclude_port_area, $fids);

            if ($pagina =~ /%%_EXCLUDE_PORT=(.*?)%%/is) {
                $exclude_port = $1;

                $exclude_port = $prontus_varglb::DIR_SERVER
                . $prontus_varglb::DIR_CONTENIDO
                . $prontus_varglb::DIR_EDIC
                . $prontus_varglb::DIR_UNICAEDIC
                . "/xml/$exclude_port";

                # TODO: Entender y arreglar esto!
                if ($exclude_port !~ /\.xml$/) {
                } elsif (!-f $exclude_port) {
                    $exclude_port = '';
                }
            }

            $pagina =~ s/%%_EXCLUDE_PORT=.*?%%//ig; # borra marca

            if ($pagina =~ /%%_EXCLUDE_PORT_AREA=(.*?)%%/is) {
                $exclude_port_area = $1;
                $exclude_port_area =~ s/[^\d,]//isg;
                $exclude_port_area =~ s/,{2,}/,/g;
                $exclude_port_area =~ s/^,+//g;
                $exclude_port_area =~ s/,+$//g;

                #print STDERR "exclude_port_area[$exclude_port_area]\n";
            }

            $pagina =~ s/%%_EXCLUDE_PORT_AREA=.*?%%//ig; # borra marca

            if ($pagina =~ /%%_FIDS=(.*?)%%/is) {
                $fids = $1;
                $fids =~ s/,{2,}/,/g;
                $fids =~ s/^,+//g;
                $fids =~ s/,+$//g;

                #print STDERR "fids[$fids]\n";
            }

            $pagina =~ s/%%_FIDS=.*?%%//ig; # borra marca

            if ($pagina =~ /%%LOOP%%(.*?)%%\/LOOP%%/is) {
                $loop = $1;
            }

            $limit++;

            if ($limit > $MAX_LIMIT) {
                $limit = $MAX_LIMIT;
            }

            my $nom_tabla_exclude;
            if ($exclude_port) {
                $nom_tabla_exclude = &lib_prontus::set_exclude_port_table($exclude_port, $exclude_port_area, $base);
            }

            # Generar lista.
            my $hay_mas = 0;
            ($lista, $hay_mas) = &make_lista($id_secc1, $id_tema1, $id_subtema1, $loop, $limit, $base, $mv, $taxlevel, $fids, $nom_tabla_exclude); # parche fiap agrega $mv
            $limit--;
            $pagina =~ s/%%_NUM_RELAC%%/$limit/isg;
            # print STDERR "lista[$lista]\n";
            &parse_and_write($id_secc1, $id_tema1, $id_subtema1, $lista, $pagina, $loop, $k, $hay_mas, $mv);
        }
    }
}

# ---------------------------------------------------------------
sub make_lista {
    # Construye listas de articulos relacionados, para ser considerados, deben tener seccion a lo menos.
    my ($id_secc1, $id_tema1, $id_subtema1, $loop, $limit, $base, $mv, $taxlevel, $fids, $nom_tabla_exclude) = @_;
    my ($art_id, $art_fecha, $art_horap, $art_titu, $art_dirfecha, $art_extension, $art_tipoficha);

    my $dthr_system = &glib_hrfec_02::get_dtime_pack4();
    $dthr_system =~ /^(\d{8})(\d\d\d\d)/;
    my $hhmm_system = $2;
    my $dt_system = $1;


    my ($filtros) = &genera_filtros($id_secc1, $id_tema1, $id_subtema1, $dt_system, $hhmm_system, $taxlevel);

    my ($sql) = "select ART_ID, ART_FECHAP, ART_HORAP, ART_TITU, ART_DIRFECHA, ART_EXTENSION, "
    . "ART_TIPOFICHA from ART %%FILTRO%% order by ART_FECHAP desc, ART_HORAP desc LIMIT $limit";

    if ($nom_tabla_exclude) {
        $filtros .= " AND ART_ID NOT IN (SELECT EXCLUDE_ART_ID FROM $nom_tabla_exclude)" if ($filtros);
        $filtros = " WHERE ART_ID NOT IN (SELECT EXCLUDE_ART_ID FROM $nom_tabla_exclude)" if (!$filtros);
    };

    if ($fids) {
        my @arrfids = split /,/, $fids;
        my $str;

        foreach my $f (@arrfids) {
            $str = $str . "ART_TIPOFICHA = \"$f\" or ";
        };

       $str =~ s/ or $//;
       $filtros .= " AND ($str) " if ($filtros);
       $filtros = " WHERE ($str) " if (!$filtros);
    };

    if ($filtros ne '') {
        $sql =~ s/%%FILTRO%%/ where $filtros /;
    } else {
        return '';
    };

    my $tot_artics = &get_tot_artics($filtros, $base, ($limit-1));
    my ($salida) = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($art_id, $art_fecha, $art_horap, $art_titu, $art_dirfecha, $art_extension, $art_tipoficha));
    my ($nro_filas) = 1;
    my ($filas);
    my $hay_mas = 0;
    my $loopcounter = 0;

    while ($salida->fetch) {
        if ($nro_filas >= $limit) {
            $hay_mas = 1;
            last;
        };

        $loopcounter++;
        my ($una_fila, $filler, $filler2) = &generar_fila($RELDIR_ARTIC, $art_id, $art_extension, $loop, $loopcounter, $tot_artics);

        $filas .= $una_fila;
        $nro_filas++;
    };
    $salida->finish;

    return ($filas, $hay_mas);
};

# ---------------------------------------------------------------
sub generar_fila {
    # Genera y retorna cada fila de la tabla.
    my ($reldir_artic, $art_id, $art_extension, $loop, $loopcounter, $tot_artics, $refhash_campos_xml, $refhash_campos_xdata, $nro_pag) = @_;

    my (%campos_xml, %claves_adicionales);
    my $fila = $loop;

    if ($art_id ne '') {

        my $artic_obj = Artic->new(
            'prontus_id'=>$prontus_varglb::PRONTUS_ID,
            'public_server_name'=>$prontus_varglb::PUBLIC_SERVER_NAME,
            'cpan_server_name'=>$prontus_varglb::IP_SERVER,
            'document_root'=>$prontus_varglb::DIR_SERVER,
            'ts'=>$art_id,
            'campos'=>{}) || die "Error inicializando objeto articulo: $Artic::ERR\n";

        if ((! ref $refhash_campos_xml) || ($campos_xml{'_txt_titular'} eq '')) {
            %campos_xml = $artic_obj->get_xml_content();
        } else {
            %campos_xml = %$refhash_campos_xml;
        };

        if (! ref $refhash_campos_xdata) {
            %claves_adicionales = $artic_obj->get_xdata();
        } else {
            %claves_adicionales = %$refhash_campos_xdata;
        };

        $claves_adicionales{_nropagina} = $nro_pag;
        $claves_adicionales{_ts} = $art_id;
        $claves_adicionales{_loopcounter} = $loopcounter;
        $claves_adicionales{_totartics} = $tot_artics;

        $fila = &lib_prontus::procesa_loop_artic($fila,'##');
        $fila = &lib_prontus::procesa_condicional($fila, \%campos_xml, \%claves_adicionales);
        $fila = &procesar_condicional_extra($fila, $loopcounter);
        my $art_dirfecha = &lib_prontus::get_dirfecha_by_ts($art_id);
        $reldir_artic =~ s/%%DIRFECHA%%/$art_dirfecha/ig;
        $reldir_artic =~ s/%%_FECHAC%%/$art_dirfecha/ig;
        my $lnk = "$reldir_artic/$art_id" . '.' . $art_extension;
        my $fullpath_vista = $lnk;
        $fila = $artic_obj->parse_artic_data($fullpath_vista, $fila, \%campos_xml, \%claves_adicionales);
        $fila = &lib_prontus::parser_custom_function($fila);

        # Borra marcas no sustituidas
        $fila =~ s/%%.+?%%//g;

    } else {
        # Armar la fila sin datos.
        $fila = '';
    };

    my $p = \%campos_xml;
    my $x = \%claves_adicionales;
    return ($fila, $p, $x);
};

# ---------------------------------------------------------------
sub parse_and_write {
    my ($id_secc1, $id_tema1, $id_subtema1, $lista, $pagina, $loop, $nomfile, $hay_mas, $mv) = @_;

    if ($lista eq '')  {
        $pagina =~ s/%%_VERMAS%%.*?%%\/_VERMAS%%//isg;
        $lista = 'Sin art&iacute;culos relacionados.';
    };

    if (!$hay_mas) {
        $pagina =~ s/%%_VERMAS%%.*?%%\/_VERMAS%%//isg;
    };

    $pagina =~ s/%%LOOP%%.*?%%\/LOOP%%/$lista/isg;
    $pagina =~ s/%%_SECCION1%%/$id_secc1/ig;
    $pagina =~ s/%%_TEMA1%%/$id_tema1/ig;
    $pagina =~ s/%%_SUBTEMA1%%/$id_subtema1/ig;

    $pagina =~ s/%%_SERVER_NAME%%/$prontus_varglb::PUBLIC_SERVER_NAME/ig;
    $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/ig;

    if ($id_secc1 eq '-1') {
        $id_secc1 = '';
        $lista = '';
    };

    my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;

    $pagina =~ s/$crlf/\x0a/sg;

    $pagina = &lib_prontus::parser_custom_function($pagina);

    # Eliminar comentarios html sobrantes.
    $pagina =~ s/<!--\w+-->//sg;
    $pagina =~ s/<!--\/\w+-->//sg;
    $pagina =~ s/%%.*?%%//sg;

    # Escribe pagina en el disco.
    my $reldir_dst_artic_relac = $RELDIR_DST_ARTIC_RELAC;

    if ($mv) {
        $reldir_dst_artic_relac =~ s/\/taxonomia\/pags/\/taxonomia\/pags-$mv/;

        &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$reldir_dst_artic_relac");
    };

    my $dst2write = "$prontus_varglb::DIR_SERVER$reldir_dst_artic_relac/" . $id_secc1 . '_' . $id_tema1 . '_' . $id_subtema1 . '_' . $nomfile;

    &glib_fildir_02::write_file($dst2write, $pagina);
    &lib_prontus::purge_cache($dst2write) if ($prontus_varglb::CACHE_PURGE_ART_RELAC eq 'SI');
};

# ---------------------------------------------------------------
sub genera_filtros {
    # Genera segmento variable del sql para encontrar los articulos relacionados.
    my ($id_secc1, $id_tema1, $id_subtema1, $dt_system, $hhmm_system, $taxlevel) = @_;
    # taxlevel: seccion | seccion-tema | seccion-tema-subtema, siempre al menos es "seccion"
    my ($filtros);

    if ($id_secc1) {
        $filtros = "(ART_IDSECC1 = \"$id_secc1\" or ART_IDSECC2 = \"$id_secc1\" or ART_IDSECC3 = \"$id_secc1\")" if $filtros eq '';
        if (($id_tema1) && (lc $taxlevel ne 'seccion')) {
            $filtros .= " and (ART_IDTEMAS1 = \"$id_tema1\" or ART_IDTEMAS2 = \"$id_tema1\" or ART_IDTEMAS3 = \"$id_tema1\")" if $filtros ne '';
            if (($id_subtema1) && (lc $taxlevel ne 'seccion') && (lc $taxlevel ne 'seccion-tema')) {
                $filtros .= " and (ART_IDSUBTEMAS1 = \"$id_subtema1\" or ART_IDSUBTEMAS2 = \"$id_subtema1\" or ART_IDSUBTEMAS3 = \"$id_subtema1\")" if $filtros ne '';
            };
        };

        $filtros .= " and (ART_FECHAPHORAP <= '$dt_system$hhmm_system') ";
        $filtros .= " and (ART_ALTA = '1') " if ($CONTROLAR_ALTA_ARTICULOS eq 'SI');

        if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
            $filtros .= " and ( (ART_FECHAEHORAE >= '$dt_system$hhmm_system') OR ( (ART_FECHAEHORAE < '$dt_system$hhmm_system') AND (ART_SOLOPORTADAS = '1') ) )";
        };

        return $filtros;
    } else {
        return '';
    };

}; # genera_filtros.

# ---------------------------------------------------------------
sub generar_relacionados_manualtax {
    my ($tax) = $_[0];
    my ($dst_dir) = $_[1];
    my ($ts) = $_[2];
    my ($base) = $_[3];
    my ($mv) = $_[4];

    # borra extension, en caso de que venga con ella
    $ts =~ s/\..+$//;

    my ($ruta_dir) = $prontus_varglb::DIR_SERVER . $RELDIR_ARTIC_RELAC;
    $ruta_dir =~ s/\/taxonomia\/pags/\/taxonomia\/pags-$mv/ if ($mv);
    $dst_dir =~ s/(\d{8})\/pags/$1\/pags-$mv/ if ($mv);

    my (@lisdir) = &glib_fildir_02::lee_dir($ruta_dir) if (-d $ruta_dir);
    my ($pagina, $k, $plantilla, $loop);

    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

    foreach $k (@lisdir) {
        if (-f "$ruta_dir/$k") {
            $plantilla = "$ruta_dir/$k";
            $pagina = &glib_fildir_02::read_file($plantilla);

            if ($pagina =~ /%%LOOP%%(.*?)%%\/LOOP%%/is) {
                $loop = $1;
            };

            # Geenerar listas con los articulos especificados manualmente
            my ($lista) = &make_lista_manualtax($tax, $loop, $base);
            # print STDERR "lista[$lista]\n";

            $pagina =~ s/%%_NUM_RELAC%%//isg; # no aplica cuando hay manual tax.
            # Parsear y escribir paginas para incluir en articulos.
            &parse_and_write_manualtax($lista, $pagina, $dst_dir, $ts, $k);
        };
    };

};

# ---------------------------------------------------------------
sub borrar_relacionados_manualtax {
    my ($dst_dir) = $_[0];
    my ($ts) = $_[1];

    my $pat = $dst_dir . '/' . $ts . '_*.*'; # Borra imagenes
    my $res = unlink glob($pat);
};

# ---------------------------------------------------------------
sub parse_and_write_manualtax {
    my ($lista, $pagina, $dst_dir, $ts, $nomfile) = @_;
    # print STDERR "[$ts, $nomfile]\n";
    $pagina =~ s/%%LOOP%%.*?%%\/LOOP%%/$lista/isg;

    $pagina =~ s/%%_VERMAS%%.*?%%\/_VERMAS%%//isg;

    my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;

    $pagina =~ s/$crlf/\x0a/sg;

    $pagina = &lib_prontus::parser_custom_function($pagina);

    # Eliminar comentarios html sobrantes.
    $pagina =~ s/<!--\w+-->//sg;
    $pagina =~ s/<!--\/\w+-->//sg;
    $pagina =~ s/%%.*?%%//sg;


    # Escribe pagina en el disco.
    &glib_fildir_02::check_dir($dst_dir);
    &glib_fildir_02::write_file("$dst_dir/" . $ts . '_' . $nomfile , $pagina);
};

# ---------------------------------------------------------------
sub genera_filtros_manualtax {
    # Genera segmento variable del sql para encontrar los articulos.
    my ($tax, $dt_system, $hhmm_system) = @_;
    my ($filtros);

    $tax =~ s/[^0-9\,]//sg;
    my @autoincs = split(/\,/, $tax); # 10,20,35,112
    my $autoinc;
    $filtros = '(ART_AUTOINC = 0';

    foreach $autoinc (@autoincs) {
        if ($autoinc !~ /^\d+$/) {
            next;
        }
        $filtros .= " or ART_AUTOINC = $autoinc ";
    };

    $filtros .= ')';

    # $filtros .= " and (ART_FECHAPHORAP <= '$dt_system$hhmm_system') ";
    # $filtros .= " and (ART_ALTA = '1') " if ($CONTROLAR_ALTA_ARTICULOS eq 'SI');
    # $filtros .= " and (ART_FECHAEHORAE >= '$dt_system$hhmm_system') " if ($prontus_varglb::CONTROL_FECHA eq 'SI');

    return $filtros;
}; # genera_filtros.

# ---------------------------------------------------------------
sub make_lista_manualtax {
    my ($tax, $loop, $base) = @_;
    my ($art_id, $art_fecha, $art_horap, $art_titu, $art_dirfecha, $art_extension, $art_tipoficha);

    my $dthr_system = &glib_hrfec_02::get_dtime_pack4();
    $dthr_system =~ /^(\d{8})(\d\d\d\d)/;
    my $hhmm_system = $2;
    my $dt_system = $1;

    my ($filtros) = &genera_filtros_manualtax($tax, $dt_system, $hhmm_system);
    my ($sql) = "select ART_ID, ART_FECHAP, ART_HORAP, ART_TITU, ART_DIRFECHA, ART_EXTENSION, ART_TIPOFICHA from ART %%FILTRO%% order by ART_FECHAP desc, ART_HORAP desc  LIMIT $MAX_LIMIT";

    $sql =~ s/%%FILTRO%%/ where $filtros  /;

    my $tot_artics = &get_tot_artics($filtros, $base, $MAX_LIMIT);
    my ($salida) = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($art_id, $art_fecha, $art_horap, $art_titu, $art_dirfecha, $art_extension, $art_tipoficha));
    my ($nro_filas) = 0;
    my ($filas);
    my $loopcounter = 0;

    while ($salida->fetch) {
        $loopcounter++;
        # print STDERR "\n$art_fecha $art_horap Y $dt_system $hhmm_system\n";
        my ($una_fila, $filler) = &generar_fila($RELDIR_ARTIC, $art_id, $art_extension, $loop, $loopcounter, $tot_artics);

        $filas .= $una_fila;
        $nro_filas++;
    };

    $salida->finish;

    return $filas;
};

# ---------------------------------------------------------------
sub carga_tabla_temas {
    my $base = shift;
    my ($sql, $salida, $nom, $id, $port, $idparent, $nom4vistas);
    my %tabla_tem;
    $sql = "select TEMAS_ID, TEMAS_NOM, TEMAS_PORT, TEMAS_IDSECC, TEMAS_NOM4VISTAS from TEMAS ";
    $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($id, $nom, $port, $idparent, $nom4vistas));

    while ($salida->fetch) {
        $tabla_tem{$id} = "$nom\t\t$port\t\t$idparent\t\t$nom4vistas";
    };

    $salida->finish;
    return %tabla_tem;
};

# ---------------------------------------------------------------
sub carga_tabla_subtemas {
    my $base = shift;
    my ($sql, $salida, $nom, $port, $id, $idparent, $nom4vistas);
    my %tabla_stem;
    $sql = "select SUBTEMAS_ID, SUBTEMAS_NOM, SUBTEMAS_PORT, SUBTEMAS_IDTEMAS, SUBTEMAS_NOM4VISTAS from SUBTEMAS ";
    $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($id, $nom, $port, $idparent, $nom4vistas));

    while ($salida->fetch) {
        $tabla_stem{$id} = "$nom\t\t$port\t\t$idparent\t\t$nom4vistas";
    };

    $salida->finish;
    return %tabla_stem;
};

# ---------------------------------------------------------------
sub carga_tabla_seccion {
    my $base = shift;
    my ($sql, $salida, $nom, $port, $id, $nom4vistas);
    my %tabla_secc;
    $sql = "select SECC_ID, SECC_NOM, SECC_PORT, SECC_NOM4VISTAS from SECC ";
    $salida = &glib_dbi_02::ejecutar_sql_bind($base, $sql, \($id, $nom, $port, $nom4vistas));

    while ($salida->fetch) {
        $tabla_secc{$id} = "$nom\t\t$port\t\t$nom4vistas";
    };

    $salida->finish;
    return %tabla_secc;
};

# ---------------------------------------------------------------
sub carga_hash_seccion {
    my $base = shift;
    my $only_enabled = shift;
    my ($sql, $salida, %hash_datos);
    $sql = "select SECC_ID, SECC_NOM, SECC_PORT, SECC_NOM4VISTAS from SECC ";
    if ($only_enabled) {
        $sql .= "where SECC_MOSTRAR = '1'";
    }
    $salida = &glib_dbi_02::ejecutar_sql($base, $sql);

    while (my $row = $salida->fetchrow_hashref) {
        my @vistas = split(/\n/, $row->{'SECC_NOM4VISTAS'});
        my %hash_temp = ();
        foreach my $vista (@vistas) {
            my @temp = split(/\t/, $vista);
            $hash_temp{$temp[0]} = $temp[1];
        }
        $hash_datos{$row->{'SECC_ID'}}{'nombre'} = $row->{'SECC_NOM'};
        $hash_datos{$row->{'SECC_ID'}}{'port'} = $row->{'SECC_PORT'};
        $hash_datos{$row->{'SECC_ID'}}{'vistas'} = \%hash_temp;
    }

    $salida->finish;
    return %hash_datos;
}
# ---------------------------------------------------------------
sub carga_hash_temas {
    my $base = shift;
    my $only_enabled = shift;
    my $id_padre = shift;
    my ($sql, $salida, %hash_datos, @filtros);
    $sql = "select TEMAS_ID, TEMAS_NOM, TEMAS_PORT, TEMAS_IDSECC, TEMAS_NOM4VISTAS from TEMAS ";

    if ($id_padre) {
        push(@filtros, "TEMAS_IDSECC='$id_padre'");
    }
    if ($only_enabled) {
        push(@filtros, "TEMAS_MOSTRAR = '1'");
    }
    if (scalar(@filtros) > 0) {
        $sql .= 'where ' .join(' and ', @filtros);
    }
    $salida = &glib_dbi_02::ejecutar_sql($base, $sql);

    while (my $row = $salida->fetchrow_hashref) {
        my @vistas = split(/\n/, $row->{'TEMAS_NOM4VISTAS'});
        my %hash_temp = ();
        foreach my $vista (@vistas) {
            my @temp = split(/\t/, $vista);
            $hash_temp{$temp[0]} = $temp[1];
        }
        $hash_datos{$row->{'TEMAS_ID'}}{'id_padre'} = $row->{'TEMAS_IDSECC'} if (!$id_padre);
        $hash_datos{$row->{'TEMAS_ID'}}{'nombre'} = $row->{'TEMAS_NOM'};
        $hash_datos{$row->{'TEMAS_ID'}}{'port'} = $row->{'TEMAS_PORT'};
        $hash_datos{$row->{'TEMAS_ID'}}{'vistas'} = \%hash_temp;
    }

    $salida->finish;
    return %hash_datos;
}

# ---------------------------------------------------------------
sub carga_hash_subtemas {
    my $base = shift;
    my $only_enabled = shift;
    my $id_padre = shift;
    my ($sql, $salida, %hash_datos, @filtros);
    $sql = "select SUBTEMAS_ID, SUBTEMAS_NOM, SUBTEMAS_PORT, SUBTEMAS_IDTEMAS, SUBTEMAS_NOM4VISTAS from SUBTEMAS ";
    if ($id_padre) {
        push(@filtros, "SUBTEMAS_IDTEMAS='$id_padre'");
    }
    if ($only_enabled) {
        push(@filtros, "SUBTEMAS_MOSTRAR = '1'");
    }
    if (scalar(@filtros) > 0) {
        $sql .= 'where ' .join(' and ', @filtros);
    }
    $salida = &glib_dbi_02::ejecutar_sql($base, $sql);

    while (my $row = $salida->fetchrow_hashref) {
        my @vistas = split(/\n/, $row->{'SUBTEMAS_NOM4VISTAS'});
        my %hash_temp = ();
        foreach my $vista (@vistas) {
            my @temp = split(/\t/, $vista);
            $hash_temp{$temp[0]} = $temp[1];
        }
        $hash_datos{$row->{'SUBTEMAS_ID'}}{'id_padre'} = $row->{'SUBTEMAS_IDTEMAS'} if (!$id_padre);
        $hash_datos{$row->{'SUBTEMAS_ID'}}{'nombre'} = $row->{'SUBTEMAS_NOM'};
        $hash_datos{$row->{'SUBTEMAS_ID'}}{'port'} = $row->{'SUBTEMAS_PORT'};
        $hash_datos{$row->{'SUBTEMAS_ID'}}{'vistas'} = \%hash_temp;
    }
    $salida->finish;
    return %hash_datos;
}

# ---------------------------------------------------------------
sub procesar_condicional_extra {
    my ($buffer, $loopcounter) = @_;
    my $localbuf = $buffer;

    while ($buffer =~ /%%IFV\((\d+)\, *(\d+)\)%%.+?%%\/IFV%%/isg) {
        my $div = $1;
        my $res = $2;
        my $mod = $loopcounter % $div;
        if ($mod != $res) {
            $localbuf =~ s/%%(IFV\($div\, *$res\))%%(.+?)%%\/(IFV)%%//is;

        };
    };

    while ($buffer =~ /%%NIFV\((\d+)\, *(\d+)\)%%.+?%%\/NIFV%%/isg) {
        my $div = $1;
        my $res = $2;
        my $mod = $loopcounter % $div;
        if ($mod == $res) {
            $localbuf =~ s/%%(NIFV\($div\, *$res\))%%(.+?)%%\/(NIFV)%%//is;

        };
    };

    return $localbuf;
};

# ---------------------------------------------------------------
# carga configuracion propia del servidor si esta disponible
# sobreescribe los valores definidos en el cpan de prontus
sub carga_configuracion_local {
    my $buffer = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER/$prontus_varglb::DIR_CGI_CPAN/prontus_taxport_conf.cfg");
    if ($buffer ne '') {
        if ($buffer =~ m/\s*TAXPORT_MAX_WORKERS\s*=\s*["']([0-9]+?)["']/) {
            $prontus_varglb::TAXPORT_MAX_WORKERS = $1;
        }
        if ($buffer =~ m/\s*TAXPORT_MAX_MASTERS\s*=\s*["']([0-9]+?)["']/) {
            $prontus_varglb::TAXPORT_MAX_MASTERS = $1;
        }
    }
}
# ---------------------------------------------------------------
# genera los filtros para los listados de taxport
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
        $filtros = "(";
        $filtros .= "ART_IDSECC1 <> \"\"";
        $filtros .= " or ART_IDSECC2 <> \"\"" if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^(2|3)$/);
        $filtros .= " or ART_IDSECC3 <> \"\"" if ($prontus_varglb::TAXONOMIA_NIVELES eq '3');
        $filtros .= ")";
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

# ---------------------------------------------------------------
# cargo los filtros para los taxport filtradas
sub cargar_fil_cfg {
    my $file = $_[0];
    my $fil = $_[1];

    return if (!-f $file); # no se hace nada si no existe el directorio y archivo del filtro.
    return if (exists $CFG_FIL_TAXPORT{$fil}); # para no cargarlo dos veces.

    my $cfg = &glib_fildir_02::read_file($file);

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

# -------------------------------------------------------------------------
# Se buscan los directorios que comiencen con fil_ en las plantillas de taxport.
sub load_taxport_fil {
    my $ruta_dir = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_PTEMA";
    my @listado = glob("$ruta_dir/fil_*");

    foreach my $dir (@listado) {
        if ($dir =~ /fil_(.*?)$/) {
            &lib_tax::cargar_fil_cfg("$dir/filtros.cfg", "fil_" . $1);
        }
    }
};
# ---------------------------------------------------------------
sub check_taxport_running {
    my($res) = qx/ps axww | grep 'prontus_cron_taxport.cgi' | grep -v grep | grep -v 'sh -c' | grep -v tail | wc -l/;

    $res =~ s/\D//gs;
    $res += 0; # para forzar el casteo a numero
    return $res;
}
# ---------------------------------------------------------------
sub check_worker_running {
    my($res) = qx/ps axww | grep 'prontus_cron_taxport_worker.cgi' | grep -v grep | grep -v 'sh -c' | grep -v tail | wc -l/;

    $res =~ s/\D//gs;
    $res += 0; # para forzar el casteo a numero
    return $res;
}

return 1;
