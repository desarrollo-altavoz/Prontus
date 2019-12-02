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
# PROPOSITO.
# -----------
# Genera una pagina del listado de multitag, si existe una pagina
# generada anteriormente en el cache, entrega esa, sino genera una
# nueva
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# NO
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# solo web
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# Ninguna
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# MULTITAG_ART_S
# MULTITAG_ART_ST
# MULTITAG_ART_T
# MULTITAG_S
# MULTITAG_ST
# MULTITAG_T
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 26/11/2015 - JOR - Primera version.
# 1.1.0 - 23/02/2017 - EAG - Integracion a Prontus
#
# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibs = $Bin;
    unshift(@INC, $pathLibs);
    do '../dir_cgi.pm';
    $pathLibs =~ s/\/[^\/]+$//;
    $pathLibs =~ s/\/[^\/]+$/\/$DIR_CGI_CPAN/;
    unshift(@INC,$pathLibs);
};

use strict;
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_ipcheck;
use glib_html_02;
use glib_cgi_04;
use glib_fildir_02;
use lib_prontus;
use lib_maxrunning;
use Artic;
use lib_tax;
use POSIX qw(ceil);

my %FORM;
my $BD;
my $PLT_DIR;
my $CACHE_DIR;
my $PLT_DEFAULT;
my $RELDIR_ARTIC;
my $ITEM_X_PAG = 12;
my $CACHE = 1;
my $PLT = '';

main: {
    &glib_cgi_04::new();
    &set_valid_params();

    # Soporta un maximo de n copias corriendo.
    if (&lib_maxrunning::maxExcedido(200)) {
        print "Content-Type: text/html\n\n";
        exit;
    };

    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus_id'});
    my $path_conf = &lib_prontus::ajusta_pathconf($relpath_conf);

    # Carga variables de configuracion.
    &lib_prontus::load_config($path_conf);

    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();

    if (!ref($BD)) {
        print STDERR "Error conectar BD: $msg_err_bd\n";
        &msg_error("Ha ocurrido un error");
        exit;
    };

    # usa la misma configuracion de las portadas tagonomicas
    $ITEM_X_PAG = $prontus_varglb::TAGPORT_ARTXPAG;

    $PLT_DIR = $prontus_varglb::DIR_SERVER. $prontus_varglb::DIR_TEMP."/extra/multitag";
    $CACHE_DIR = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_MULTITAG;
    $PLT_DEFAULT = "$PLT_DIR/default.html";
    $RELDIR_ARTIC = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/%%DIRFECHA%%$prontus_varglb::DIR_PAG";

    $PLT = "$PLT_DIR/$FORM{'plantilla'}.html";
    $PLT = $PLT_DEFAULT if (!-f $PLT);

    if (!-f $PLT) {
        print STDERR "No se pudo localizar la plantilla[$PLT]\n";
        &msg_error("No se pudo localizar la plantilla");
    }
    if(!-e $CACHE_DIR){
        #si no existe el directorio se crea.
        mkdir $CACHE_DIR;
    }

    my ($nom_s, $id_s, $friendly_s) = &get_info_s();
    my ($nom_t, $id_t, $friendly_t) = &get_info_t();
    my ($nom_st, $id_st, $friendly_st) = &get_info_st();
    my $pagina = &glib_fildir_02::read_file($PLT);

    if ($FORM{'s'} && !$nom_s) {
        &msg_error("La seccion no existe.");
    };

    if ($FORM{'t'} && !$nom_t) {
        &msg_error("El tema no existe.");
    };

    if ($FORM{'st'} && !$nom_st) {
        &msg_error("El subtema no existe.");
    };

    $FORM{'id_s'} = $id_s;
    $FORM{'id_t'} = $id_t;
    $FORM{'id_st'} = $id_st;

    my $pagina_cache = &get_cache();

    if ($pagina_cache) {
        #~ print STDERR "from cache!\n";
        print "Content-Type: text/html\n\n";
        print $pagina_cache;
        exit;
    }

    $pagina = &buscar_articulos($pagina);
    $pagina =~ s/%%_prontus_id%%/$FORM{'prontus_id'}/isg;
    $pagina =~ s/%%_s%%/$FORM{'s'}/isg;
    $pagina =~ s/%%_t%%/$FORM{'t'}/isg;
    $pagina =~ s/%%_st%%/$FORM{'st'}/isg;

    $pagina =~ s/%%_nom_s%%/$nom_s/isg;
    $pagina =~ s/%%_nom_t%%/$nom_t/isg;
    $pagina =~ s/%%_nom_st%%/$nom_st/isg;

    $pagina =~ s/%%_friendly_s%%/$friendly_s/isg;
    $pagina =~ s/%%_friendly_t%%/$friendly_t/isg;
    $pagina =~ s/%%_friendly_st%%/$friendly_st/isg;

    my %campos = (
        '_s'                => $FORM{'s'},
        '_t'                => $FORM{'t'},
        '_t'                => $FORM{'st'},
        '_nom_s'            => $nom_s,
        '_nom_t'            => $nom_t,
        '_nom_st'           => $nom_st,
        '_friendly_s'       => $friendly_s,
        '_friendly_t'       => $friendly_t,
        '_friendly_st'      => $friendly_st
    );

    $pagina = &lib_prontus::procesa_condicional($pagina, \%campos);
    $pagina = &parse_include($pagina);

    # elimina marcas no parseadas
    $pagina =~ s/%%.*?%%//sg;

    &guarda_cache($pagina);

    print "Content-Type: text/html\n\n";
    print $pagina;
};

# Buscar articulos en las tablas segun corresponda.
# Un articulo puede estar en todas las tablas.
#
sub buscar_articulos {
    my $pagina = $_[0];
    my $loop;
    my $output;
    my $art_id;
    my $loopcounter = 1;

    if ($pagina =~ /%%loop%%(.*?)%%\/loop%%/isg) {
        $loop = $1;
    }

    my ($sql, @params) = &get_query();
    my $total = &get_total($sql, @params);
    my ($filtro, $total_pags) = &get_filtro_paginacion($total);

    $sql = "$sql $filtro";

    # print STDERR "sql[$sql] $total filtro[$filtro] total_pags[$total_pags]\n";

    my $salida = &glib_dbi_02::ejecutar_sql_bind_param($BD, $sql, \@params, \($art_id));

    while ($salida->fetch) {
        my ($fila_content, $auxref, $auxref2) = &lib_tax::generar_fila($RELDIR_ARTIC, $art_id, "html", $loop, $loopcounter, $total);
        $output .= $fila_content;
        $loopcounter++;
    }

    $salida->finish;

    $pagina =~ s/%%loop%%.*?%%\/loop%%/$output/isg;

    if (!$output) {
        $pagina =~ s/<!--resultados-->.*?<!--\/resultados-->//isg;
    } else {
        $pagina =~ s/<!--sin_resultados-->.*?<!--\/sin_resultados-->//isg;
    }

    $pagina = &parsea_paginacion($pagina, $total_pags);

    return $pagina;
};

sub parsea_paginacion {
    my $pagina = $_[0];
    my $total = $_[1];

    if ($pagina =~ /%%paginacion%%(.*?)%%\/paginacion%%/isg) {
        my $paginacion = $1;
        my $output;

        for (my $x = 1; $x <= $total; $x++) {
            my $tmp = $paginacion;
            my $link = "/cgi-bin/multitag/prontus_multitag_list.cgi" . &get_query_string() . "&p=$x";
            my $link_friendly = &get_link_friendly() . "/p/$x";

            $tmp =~ s/%%link%%/$link/isg;
            $tmp =~ s/%%link_friendly%%/$link_friendly/isg;
            $tmp =~ s/%%pag%%/$x/isg;

            if ($FORM{'p'} == $x) {
                $tmp =~ s/%%current%%/actual/isg;
            } else {
                $tmp =~ s/%%current%%//isg;
            }

            $output .= $tmp;
        }

        $pagina =~ s/%%paginacion%%.*?%%\/paginacion%%/$output/isg;
    }

    return $pagina;
};

sub get_total {
    my $sql = shift;
    my @params = @_;

    $sql =~ s/SELECT .*? FROM/SELECT COUNT\(*\) FROM/sg;

    my $tot;
    my $salida = &glib_dbi_02::ejecutar_sql_bind_param($BD, $sql, \@params, \($tot));
    $salida->fetch;
    $salida->finish;

    return $tot;
};

sub get_filtro_paginacion {
    my $total = $_[0];
    my $sql;
    my $num_pags = POSIX::ceil($total / $ITEM_X_PAG);

    $FORM{'p'} = $num_pags if ($num_pags && $FORM{'p'} > $num_pags);

    my $p = (int $FORM{'p'}) - 1;
    my $limit = $p * $ITEM_X_PAG;

    $sql = " LIMIT $limit, $ITEM_X_PAG";

    # print STDERR "[$total / $ITEM_X_PAG] num_pags[$num_pags]\n";
    return ($sql, $num_pags);
};

sub get_query {
    my $sql;
    my @params;
    my $dthhmm_system = substr(&glib_hrfec_02::get_dtime_pack4(), 0, 12);

    my $filtro_publicacion = " AND ART_FECHAPHORAP <= ?";
    if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
        $filtro_publicacion .= " AND ( ART_FECHAEHORAE >= ? OR ART_SOLOPORTADAS = '1' )";
    }

    # Solo seccion.
    if ($FORM{'s'} ne '' && $FORM{'t'} eq '' && $FORM{'st'} eq '') {
        $sql = "SELECT MULTITAG_ART_S_ART_ID FROM MULTITAG_ART_S LEFT JOIN ART ON (ART_ID=MULTITAG_ART_S_ART_ID) LEFT JOIN MULTITAG_S ON (MULTITAG_ART_S_ID=MULTITAG_S_ID)";
        $sql .= " WHERE ART_ALTA = '1' AND MULTITAG_S_FRIENDLY = ? $filtro_publicacion ORDER BY ART_FECHAP desc, ART_HORAP desc";
        push(@params, $FORM{'s'});
    # Solo tema.
    } elsif ($FORM{'s'} eq '' && $FORM{'t'} ne '' && $FORM{'st'} eq '') {
        $sql = "SELECT MULTITAG_ART_T_ART_ID FROM MULTITAG_ART_T LEFT JOIN ART ON (ART_ID=MULTITAG_ART_T_ART_ID) LEFT JOIN MULTITAG_T ON (MULTITAG_ART_T_ID=MULTITAG_T_ID)";
        $sql .= " WHERE ART_ALTA = '1' AND MULTITAG_T_FRIENDLY = ? $filtro_publicacion ORDER BY ART_FECHAP desc, ART_HORAP desc";
        push(@params, $FORM{'t'});
    # Solo subtema.
    } elsif ($FORM{'s'} eq '' && $FORM{'t'} eq '' && $FORM{'st'} ne '') {
        $sql = "SELECT MULTITAG_ART_ST_ART_ID FROM MULTITAG_ART_ST LEFT JOIN ART ON (ART_ID=MULTITAG_ART_ST_ART_ID) LEFT JOIN MULTITAG_ST ON (MULTITAG_ART_ST_ID=MULTITAG_ST_ID)";
        $sql .= " WHERE ART_ALTA = '1' AND MULTITAG_ST_FRIENDLY = ? $filtro_publicacion ORDER BY ART_FECHAP desc, ART_HORAP desc";
        push(@params, $FORM{'st'});
    # seccion y tema.
    } elsif ($FORM{'s'} ne '' && $FORM{'t'} ne '' && $FORM{'st'} eq '') {
        $sql = "SELECT MULTITAG_ART_S_ART_ID FROM MULTITAG_ART_S LEFT JOIN MULTITAG_ART_T ON (MULTITAG_ART_S_ART_ID = MULTITAG_ART_T_ART_ID)";
        $sql .= " LEFT JOIN ART ON (ART_ID=MULTITAG_ART_S_ART_ID) LEFT JOIN MULTITAG_S ON (MULTITAG_ART_S_ID=MULTITAG_S_ID)  LEFT JOIN MULTITAG_T ON (MULTITAG_ART_T_ID=MULTITAG_T_ID)";
        $sql .= " WHERE ART_ALTA = '1' AND MULTITAG_S_FRIENDLY = ? AND MULTITAG_T_FRIENDLY = ? $filtro_publicacion ORDER BY ART_FECHAP desc, ART_HORAP desc";
        push(@params, $FORM{'s'});
        push(@params, $FORM{'t'});
    # seccion y subtema.
    } elsif ($FORM{'s'} ne '' && $FORM{'t'} eq '' && $FORM{'st'} ne '') {
        $sql = "SELECT MULTITAG_ART_S_ART_ID FROM MULTITAG_ART_S LEFT JOIN MULTITAG_ART_ST ON (MULTITAG_ART_S_ART_ID = MULTITAG_ART_ST_ART_ID)";
        $sql .= " LEFT JOIN ART ON (ART_ID=MULTITAG_ART_S_ART_ID) LEFT JOIN MULTITAG_S ON (MULTITAG_ART_S_ID=MULTITAG_S_ID) LEFT JOIN MULTITAG_ST ON (MULTITAG_ART_ST_ID=MULTITAG_ST_ID)";
        $sql .= " WHERE ART_ALTA = '1' AND MULTITAG_S_FRIENDLY = ? AND MULTITAG_ST_FRIENDLY = ? $filtro_publicacion ORDER BY ART_FECHAP desc, ART_HORAP desc";
        push(@params, $FORM{'s'});
        push(@params, $FORM{'st'});
    # tema y subtema.
    } elsif ($FORM{'s'} eq '' && $FORM{'t'} ne '' && $FORM{'st'} ne '') {
        $sql = "SELECT MULTITAG_ART_T_ART_ID FROM MULTITAG_ART_T LEFT JOIN MULTITAG_ART_ST ON (MULTITAG_ART_T_ART_ID = MULTITAG_ART_ST_ART_ID)";
        $sql .= " LEFT JOIN ART ON (ART_ID=MULTITAG_ART_T_ART_ID) LEFT JOIN MULTITAG_T ON (MULTITAG_ART_T_ID=MULTITAG_T_ID) LEFT JOIN MULTITAG_ST ON (MULTITAG_ART_ST_ID=MULTITAG_ST_ID)";
        $sql .= " WHERE ART_ALTA = '1' AND MULTITAG_T_FRIENDLY = ? AND MULTITAG_ST_FRIENDLY = ? $filtro_publicacion ORDER BY ART_FECHAP desc, ART_HORAP desc";
        push(@params, $FORM{'t'});
        push(@params, $FORM{'st'});
    # seccion, tema y subtema.
    } elsif ($FORM{'s'} ne '' && $FORM{'t'} ne '' && $FORM{'st'} ne '') {
        $sql = "SELECT MULTITAG_ART_S_ART_ID FROM MULTITAG_ART_S LEFT JOIN MULTITAG_ART_T ON (MULTITAG_ART_S_ART_ID = MULTITAG_ART_T_ART_ID)";
        $sql .= " LEFT JOIN MULTITAG_ART_ST ON (MULTITAG_ART_T_ART_ID = MULTITAG_ART_ST_ART_ID) LEFT JOIN ART ON (ART_ID=MULTITAG_ART_S_ART_ID)";
        $sql .= " LEFT JOIN MULTITAG_S ON (MULTITAG_ART_S_ID=MULTITAG_S_ID) LEFT JOIN MULTITAG_T ON (MULTITAG_ART_T_ID=MULTITAG_T_ID)";
        $sql .= " LEFT JOIN MULTITAG_ST ON (MULTITAG_ART_ST_ID=MULTITAG_ST_ID) WHERE ART_ALTA = '1' AND MULTITAG_S_FRIENDLY = ?";
        $sql .= "  AND MULTITAG_T_FRIENDLY = ? AND MULTITAG_ST_FRIENDLY = ? $filtro_publicacion ORDER BY ART_FECHAP desc, ART_HORAP desc";
        push(@params, $FORM{'s'});
        push(@params, $FORM{'t'});
        push(@params, $FORM{'st'});
    }

    # parametro del filtro de publicacion, es el ultimo del query aunque se arma primero
    push(@params, $dthhmm_system);
    push(@params, $dthhmm_system) if ($prontus_varglb::CONTROL_FECHA eq 'SI');

    return ($sql, @params);
}

sub set_valid_params {
    $FORM{'prontus_id'} = &glib_cgi_04::param('prontus_id');
    $FORM{'plantilla'} = &glib_cgi_04::param('plt');
    $FORM{'s'} = &glib_cgi_04::param('s');
    $FORM{'t'} = &glib_cgi_04::param('t');
    $FORM{'st'} = &glib_cgi_04::param('st');
    $FORM{'p'} = &glib_cgi_04::param('p');

    $FORM{'p'} = 1 if ($FORM{'p'} !~ /^\d+$/);
    $FORM{'p'} = 1 if (!$FORM{'p'});

    # deja solo letras y guiones
    $FORM{'s'} =~ s/[^\w\-]+//sg;
    $FORM{'t'} =~ s/[^\w\-]+//sg;
    $FORM{'st'} =~ s/[^\w\-]+//sg;

    if ($FORM{'prontus_id'} eq '') {
        &msg_error("No se especificó una instancia de Prontus.");
    }

    if ($FORM{'s'} eq '' && $FORM{'t'} eq '' && $FORM{'st'} eq '') {
        &msg_error("No se especificó una seccion, tema o subtema.");
    }

};

sub get_query_string {
    my $querystr = "?prontus_id=$FORM{'prontus_id'}";
    $querystr .= "&plt=$FORM{'plantilla'}" if ($FORM{'plantilla'});
    $querystr .= "&s=$FORM{'s'}" if ($FORM{'s'});
    $querystr .= "&t=$FORM{'t'}" if ($FORM{'t'});
    $querystr .= "&st=$FORM{'st'}" if ($FORM{'st'});

    return $querystr;
};

sub get_link_friendly {
    my $link = '/'.$FORM{'prontus_id'};

    $link .= "/seccion/$FORM{'s'}" if ($FORM{'s'});
    $link .= "/tema/$FORM{'t'}" if ($FORM{'t'});
    $link .= "/subtema/$FORM{'st'}" if ($FORM{'st'});

    return $link;
};

sub msg_error {
    my $msg = $_[0];

    print "Content-Type: text/html\n\n";
    print "<strong>ERROR</strong>: $msg\n\n";
    exit;
};

sub get_info_s {
    my ($sql, $salida, $nom, $id, $friendly);

    return '' if (!$FORM{'s'});

    my @params = ($FORM{'s'});
    $sql = "SELECT MULTITAG_S_NOMBRE,MULTITAG_S_ID,MULTITAG_S_FRIENDLY FROM MULTITAG_S WHERE MULTITAG_S_FRIENDLY = ? ";
    $salida = &glib_dbi_02::ejecutar_sql_bind_param($BD, $sql, \@params, \($nom, $id, $friendly));
    $salida->fetch;
    $salida->finish;

    return ($nom, $id, $friendly);
};

sub get_info_t {
    my ($sql, $salida, $nom, $id, $friendly);

    return '' if (!$FORM{'t'});

    my @params = ($FORM{'t'});
    $sql = "SELECT MULTITAG_T_NOMBRE,MULTITAG_T_ID,MULTITAG_T_FRIENDLY FROM MULTITAG_T WHERE MULTITAG_T_FRIENDLY = ? ";
    $salida =  &glib_dbi_02::ejecutar_sql_bind_param($BD, $sql, \@params, \($nom, $id, $friendly));
    $salida->fetch;
    $salida->finish;

    return ($nom, $id, $friendly);
};

sub get_info_st {
    my ($sql, $salida, $nom, $id, $friendly);

    return '' if (!$FORM{'st'});

    my @params = ($FORM{'st'});
    $sql = "SELECT MULTITAG_ST_NOMBRE,MULTITAG_ST_ID,MULTITAG_ST_FRIENDLY FROM MULTITAG_ST WHERE MULTITAG_ST_FRIENDLY = ? ";
    $salida =  &glib_dbi_02::ejecutar_sql_bind_param($BD, $sql, \@params, \($nom, $id, $friendly));
    $salida->fetch;
    $salida->finish;

    return ($nom, $id, $friendly);
};

sub get_cache {
    my $filter = "$FORM{'id_s'}_$FORM{'id_t'}_$FORM{'id_st'}_$FORM{'p'}";
    my $nombre_plt = 'default.html';

    return '' if (!$CACHE);

    if ($PLT =~ /\/multitag\/(\w+\.\w+)$/) {
        $nombre_plt = $1;
    }

    my $cache_file = "$CACHE_DIR/$filter\_$nombre_plt";
    my $mtime = (stat($cache_file))[9];
    my $diff = time - $mtime;

    if ($diff >= 300) {
        unlink $cache_file;
        return '';
    }

    if (-f $cache_file) {
        my $pagina = &glib_fildir_02::read_file($cache_file);

        return $pagina;
    }

    return '';
};

sub guarda_cache {
    my $pagina = $_[0];
    my $filter = "$FORM{'id_s'}_$FORM{'id_t'}_$FORM{'id_st'}_$FORM{'p'}"; # crear el archivo con los ids en vez de friendly.
    my $nombre_plt = 'default.html';

    return '' if (!$CACHE);

    if ($PLT =~ /\/multitag\/(\w+\.\w+)$/) {
        $nombre_plt = $1;
    }

    my $output_file = "$CACHE_DIR/$filter\_$nombre_plt";
    &glib_fildir_02::write_file($output_file, $pagina);
};

sub parse_include {
    my $pagina = $_[0];

    while ($pagina =~ /(%%include\("(.*?)"\)%%)/isg) {
        my $include = $1;
        my $file = "$prontus_varglb::DIR_SERVER$2";
        my $buffer;

        $include =~ s/\//\\\//g;
        $include =~ s/\(/\\\(/g;
        $include =~ s/\)/\\\)/g;

        if (-f $file) {
            $buffer = &glib_fildir_02::read_file($file);
        }

        $pagina =~ s/$include/$buffer/sig;
    }
    return $pagina;
};
