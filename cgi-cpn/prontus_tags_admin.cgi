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
# prontus_secc_admin.pl.
#
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /prontus/.
#
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Administrador de Secciones de noticias.
#
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------------
# prontus_temas_admin.pl (link Ver en columna Temas).
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde /prontus4_nots/cpan/core/prontus_menu.html
#
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# Plantillas:
#   /prontus4_nots/cpan/core/mant_seccs/prontus_secc_admin.html.
#   /prontus4_nots/cpan/core/mant_seccs/mensajes.html (para mensajes de error).
#
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# Paginas web: No registra. El resultado se imprime directamente hacia el browser.
#
# ---------------------------------------------------------------
# Tablas.
# -------------------
# SECC - # PERSEMP.
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 16/10/2003 - YCH - Primera version.
# 1.1 - 16/10/2007 - YCH - Elimina link mapa del sitio (segun instruccion de ald).
# ---------------------------------------------------------------


# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

use DBI;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_dbi_02;
use glib_fildir_02;

use lib_prontus;
use strict;
use glib_cgi_04;
#use lib_secc;
use lib_tags;

$| = 1; # Sin buffer. Despliega a medida que va leyendo.

# ---------------------------------------------------------------
# MAIN.
# -------------

my ($BD, %FORM,);
my (%XML_VISTAS);

my $RELPATH_TEMPL = '/cpan/core/prontus_tags_admin.html';

main:{

    my $tags_max_display = $lib_tags::MAX_TAGS_SEARCH_RESULT;

    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    $FORM{'search'} = &glib_cgi_04::param('search');
    $FORM{'search'} = &glib_str_02::trim(&lib_prontus::despulga_item_tax($FORM{'search'}));

    $FORM{'vistas'} = &glib_cgi_04::param('vistas');
    $FORM{'vistas'} = 0 if $FORM{'vistas'} eq '';

    $FORM{'page'} = &glib_cgi_04::param('page');
    $FORM{'page'} = 0 if $FORM{'page'} eq '';
    $FORM{'page'}--;
    $FORM{'page'} = '0' if ($FORM{'page'}<=0);

    my $desde_nroreg = $FORM{'page'} * $tags_max_display;

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);

    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin o editor
    if ($prontus_varglb::USERS_PERFIL eq 'P') {
      &glib_html_02::print_pag_result('Acceso a Area Restringida','La funcionalidad requerida no está disponible para perfil Redactor',1,'exit=1,ctype=1');
    };

    print "Content-Type: text/html\n\n";

    # Conectar a BD
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_pag_result("Error",$msg_err_bd,1,'exit=1');
    };

    # Chequea el el campo Mostrar Tag exista:
    &check_col('TAGS', 'TAGS_MOSTRAR', "char(1) NOT NULL DEFAULT 1");
    # Chequea que el campo TAGS_NOM4VISTAS
    &check_col('TAGS', 'TAGS_NOM4VISTAS', "text");

    # Carga la plantilla
    my $pagina = &glib_fildir_02::read_file($prontus_varglb::DIR_SERVER . "$prontus_varglb::RELDIR_BASE/$prontus_varglb::PRONTUS_ID$RELPATH_TEMPL");

    $pagina = &lib_prontus::set_coreplt_ppal($pagina);

    my $sql;
    my $sql_count;
    $sql = "select TAGS_ID, TAGS_TAG, TAGS_COUNT, count(TAGSART_IDART), TAGS_MOSTRAR, TAGS_NOM4VISTAS from TAGS left join TAGSART on TAGS_ID = TAGSART_IDTAGS %%FILTRO%% group by TAGS_ID order by TAGS_TAG asc LIMIT $desde_nroreg, $tags_max_display";
    if ($FORM{'search'} ne '') {
        my $filtro = 'WHERE TAGS_TAG LIKE "%' . $FORM{'search'} . '%"';
        if ($FORM{'vistas'} eq 1) {
            $filtro = " WHERE TAGS_NOM4VISTAS REGEXP '(.*)\t(.*" . $FORM{'search'} . ".*)'";
        };
        $sql =~ s/%%FILTRO%%/$filtro/s;
        $sql_count = "SELECT COUNT(*) FROM TAGS $filtro";
        $pagina =~ s/<!--search_mode-->(.*?)<!--\/search_mode-->/\1/gsi;
    } else {
        $sql =~ s/%%FILTRO%%//s;
        $sql_count = 'SELECT COUNT(*) FROM TAGS';
        $pagina =~ s/<!--search_mode-->.*?<!--\/search_mode-->//gsi;
    };

    $pagina =~ /<!--item_loop-->(.*)<!--\/item_loop-->/is;
    my $loop = $1;

    my ($lista, $nro_filas) = &make_lista($sql, $loop);
    $pagina =~ s/<!--item_loop-->.*<!--\/item_loop-->/$lista/s;

    $BD->disconnect;

    $pagina =~ s/%%_path_conf%%/$FORM{'_path_conf'}/ig;
    $pagina =~ s/%%input_search%%/$FORM{'search'}/ig;
    $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/isg;

    if ($FORM{'vistas'} eq 1) {
        $pagina =~ s/%%vistas%%/ checked="checked"/ig;
    } else {
        $pagina =~ s/%%vistas%%//ig;
    };

    my $mv_count = (scalar keys %prontus_varglb::MULTIVISTAS);
    if ($mv_count == 0) {
        $pagina =~ s/<!--multivista-->.*<!--\/multivista-->//s;
    } else {
        $pagina =~ s/<!--multivista-->(.*)<!--\/multivista-->/\1/s;
    };

    my $count_tags;
    my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql_count, \($count_tags));
    $salida->fetch;
    $salida->finish;

    my $link_base = "prontus_tags_admin.cgi?_path_conf=$FORM{'_path_conf'}&amp;search=$FORM{'search'}";
    if ($FORM{'vistas'} eq 1) {
        $link_base .= "&vistas=1";
    };
    my $paginacion = &generate_pagination_links($FORM{'page'} + 1, $tags_max_display, $count_tags, $link_base, $desde_nroreg, $nro_filas);
    $pagina =~ s/%%links_paginacion%%/$paginacion/isg;

    $pagina = &parse_multivistas($pagina, '', 'vista_loop_nav');
    $pagina = &parse_multivistas($pagina, '', 'vista_loop_new');
    $pagina = &parse_multivistas($pagina, '', 'vista_loop_hidden1');
    $pagina = &parse_multivistas($pagina, '', 'vista_loop_hidden2');

    print $pagina;
}; # main

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
# rotulos tax
#sub load_data_multivistas {
#    my $tipo = shift;
#    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
#        # r:\prontus_development\web\prontus_toolbox\cpan\data\tax_multivista\pda\seccion.xml
#        my $path_xml_vista = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/tax_multivista/$mv/$tipo.xml";
#        $XML_VISTAS{$mv} = &glib_fildir_02::read_file($path_xml_vista);
#
#    };
#};

# ---------------------------------------------------------------
# rotulos tax
sub parse_multivistas {
    my ($fila, $nom4vistas, $nom_loop) = @_;

    # nom4vistas --> $mv\t$nom\n$mv\t$nom\n$mv\t$nom

    my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d| |\s/;
    my $mv;
    $fila =~ /<!--$nom_loop-->(.*?)<!--\/$nom_loop-->/s;
    my $loop_mv = $1;
    my $loops;
    my $hide = ' style="display: none;"';
    my $count = 0;
    foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
        # parsea nombre de la vista
        my $loop = $loop_mv;
        $loop =~ s/%%_nom_vista%%/$mv/g;

        # Parsea nombre de la categ, para esta vista
        my $nom = &lib_prontus::get_nomtax_envista($mv, $nom4vistas);
        $nom = &lib_prontus::escape_html($nom);

        $loop =~ s/%%_nom_item_vista%%/$nom/g;
        if ($count > 0) {
            $loop =~ s/%%_vista_style%%/$hide/g;
        } else {
            $loop =~ s/%%_vista_style%%//g;
        }
        $count++;
        $loops .= $loop;
    };
    if ($count == 1) {
        $fila =~ s/<!--vista_flechas-->.*?<!--\/vista_flechas-->//sg;
    }
    $fila =~ s/<!--$nom_loop-->.*?<!--\/$nom_loop-->/$loops/sg;
    return $fila;
};
# ---------------------------------------------------------------
sub make_lista {
    # Genera y retorna las filas de la tabla.
    my ($sentencia) = shift;
    my ($loop) = shift;


    my ($tags_id, $tags_tag, $tags_count, $tags_tot, $tags_mostrar, $nom4vistas);
    my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sentencia, \($tags_id, $tags_tag, $tags_count, $tags_tot, $tags_mostrar, $nom4vistas));
    my ($filas);
    my $count;
    while($salida->fetch){
        $tags_tag = &lib_prontus::escape_html($tags_tag);
        $filas .= &generar_fila($loop, $tags_id, $tags_tag, $tags_count, $tags_tot, $tags_mostrar, $nom4vistas);
        $count++;
    };

    $salida->finish;

    return ($filas, $count);
};

# ---------------------------------------------------------------
sub generar_fila {
    # Genera y retorna cada fila de la lista de Areas de Cargo.
    my ($loop_row, $tags_id, $tags_tag, $tags_count, $tags_tot, $tags_mostrar, $nom4vistas) = @_;
    my $mostrar_ico;
    if ($tags_mostrar) {
        $mostrar_ico = 'btn_ticket_green';
    } else {
        $mostrar_ico = 'btn_ticket_red';
    };
    $tags_mostrar = 0 unless($tags_mostrar eq 1);

    $loop_row =~ s/%%_tags_id%%/$tags_id/g;
    $loop_row =~ s/%%_tags_tag%%/$tags_tag/g;
    $loop_row =~ s/%%_tags_tot%%/$tags_tot/g;
    $loop_row =~ s/%%_tags_count%%/$tags_count/g;
    $loop_row =~ s/%%_tags_mostrar%%/$tags_mostrar/g;
    $loop_row =~ s/%%_mostrar%%/$mostrar_ico/g;

    $loop_row = &parse_multivistas($loop_row, $nom4vistas, 'vista_loop_row');
    $loop_row = &parse_multivistas($loop_row, $nom4vistas, 'vista_loop_edit');

    return $loop_row;
}; # generar_fila.

# ---------------------------------------------------------------
sub check_col {
    my ($tabla, $colname, $coldef) = @_;
    my $res_check_col = &glib_dbi_02::check_table_column($BD, $tabla, $colname, $coldef);
    &glib_html_02::print_pag_result("Error","No se pudo crear la columna $colname",1,'exit=1') if (!$res_check_col);
};

# ---------------------------------------------------------------
sub generate_pagination_links {
  my $nav_max_side_links = 5;
  my ($page, $pageSize, $totalRecords, $lnk_base, $desde_nroreg, $nro_filas) = @_;

  if ($desde_nroreg >= $totalRecords) {
      return "<strong>Resultados:</strong> Sin resultados";
  };

  my ($hasta_nroreg) = $nro_filas;
  if ($hasta_nroreg == $pageSize) {
    $hasta_nroreg = $desde_nroreg + $pageSize;
  }
  else {
    $hasta_nroreg = $totalRecords;
  };
  if ($desde_nroreg eq 0) {
      $desde_nroreg++;
  };

  my $maxPages = int($totalRecords  / $pageSize);
  $maxPages++ if (($maxPages * $pageSize) < $totalRecords);

  # el link actual
  # my $links = "<span class=\"navCurrentPage\">$page</span>";
  my $links = $page;

  my $leftmin = $page;
  my $rightmax = $page;

  # avanza uno a uno lado a lado hasta el máximo
  my $i;

  for ($i=1; $i<=$nav_max_side_links; $i++)
  {
    if ( ($page - $i) > 0)
    {
      $links = "<a href=\"$lnk_base&amp;page=" .
              ($page - $i) . "\"><strong>" . ($page - $i) . "</strong></a>&nbsp;" .
              '|&nbsp;' . $links;
      $leftmin = $page - $i;
    }
    if ( ($page + $i) <= $maxPages)
    {
      $links = $links . '&nbsp;|' .
              "&nbsp;<a href=\"$lnk_base&amp;page=" .
              ($page + $i) . "\"><strong>" . ($page + $i) . "</strong></a>";
      $rightmax = $page + $i;
    }
  }

  # ellipsis en los extremos, si fuera

  $links = ' ... ' . $links if ($leftmin > 1);

  $links .= ' ... ' if ($rightmax < $maxPages);
  # la anterior y la siguiente, si aplican
  if ($page > 1) {
    $links = "<a href=\"$lnk_base&amp;page=" .
              ($page - 1) . "\"><strong>&laquo; Anterior</strong></a>&nbsp;&nbsp;" .
              $links;
  };

  if ($page < $maxPages) {
    $links = $links .
             "&nbsp;&nbsp;<a href=\"$lnk_base&amp;page=" .
             ($page + 1) . "\"><strong>Siguiente &raquo;</strong></a>";
  };

  $links = "<strong>Resultados:</strong> $desde_nroreg a $hasta_nroreg de $totalRecords<br/><strong>P&aacute;ginas</strong>: $links";

  return $links;
};
# ----------------------------------------------------------------
# -------------------------END SCRIPT----------------------
