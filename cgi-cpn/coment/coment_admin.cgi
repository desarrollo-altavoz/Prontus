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
# Administrador de coment.
#
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/coment/coment_admin.cgi
#
# PROPOSITO.
# -----------
# Lista los registros de tabla 'COMENT'.
#
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------------
# no registra.
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde Panel de Control.
#
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# Plantillas:
#   /cpan/modulos/coment/coment_admin.html.
#
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# Paginas web: No registra. El resultado se imprime directamente hacia el browser.
#
# ---------------------------------------------------------------


# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 11/2006 - YCH - Primera Version.
# 1.1 - 10/2007 - ych - ajuste para q funcione en cgi-px

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    $pathLibsProntus =~ s/\/coment$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus


};

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use DBI;
use coment_varglb;
use prontus_varglb; &prontus_varglb::init();
use glib_dbi_02;
use glib_cgi_04;
use glib_fildir_02;
use glib_html_02;

use lib_coment;
use lib_prontus;
use strict;

# ---------------------------------------------------------------
# MAIN.
# -------------
my ($BD, $LOOP, %FORM);
my ($CPAN_LIST_PAG) = '/cpan/core/coment/coment_admin.html';
my (%TABLA_SECC, %TABLA_TEMAS, %TABLA_SUBTEMAS);

my (%HASH_TIPOS, $VERTITLE, $VERNICK);

main: {
    # Rescatar parametros recibidos.
    &glib_cgi_04::new();
    $FORM{'_prontus_id'} = &glib_cgi_04::param('_prontus_id');

    $FORM{'OBJTIPO'} = &glib_cgi_04::param('OBJTIPO');
    $FORM{'OBJTIPO'} =~ s/[^\w]//sg;
    $FORM{'OBJID'} = &glib_cgi_04::param('OBJID');
    $FORM{'OBJID'} =~ s/[^\w\.\-]//sg;
    $FORM{'NICK'} = &glib_cgi_04::param('NICK');
    $FORM{'NICK'} =~ s/[^\w\.\-@]//sg;

    $FORM{'FILASXPAG_CPAN'} = &glib_cgi_04::param('FILASXPAG_CPAN');
    $FORM{'FILASXPAG_CPAN'} =~ s/[^\d]//sg;
    $FORM{'FILASXPAG_CPAN'} = 30 if (!$FORM{'FILASXPAG_CPAN'});

    $FORM{'STATUS'} = &glib_cgi_04::param('STATUS');    # 1: con alta / 0:  sin alta
    $FORM{'OBJTIT_SEARCH'} = &glib_cgi_04::param('OBJTIT_SEARCH');


    if ($FORM{'_prontus_id'} !~ /^\w+$/) {
        &glib_html_02::print_pag_result("Error",'Error en los datos enviados - 901',0,'exit=1,ctype=1');
    };
    if (! -d "$coment_varglb::DIR_SERVER/$FORM{'_prontus_id'}") {
        &glib_html_02::print_pag_result("Error",'Error en los datos enviados - 902',0,'exit=1,ctype=1');
    };

    # Carga variables de configuracion.
    $FORM{'_path_conf'} = "$coment_varglb::DIR_SERVER/$FORM{'_prontus_id'}/cpan/$FORM{'_prontus_id'}.cfg";
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0


    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    # lee cfg especifico de coments
    my ($options_tipo, $msg_err, $hash_tipos_ref) = &lib_coment::get_objtipos($coment_varglb::DIR_SERVER, $FORM{'OBJTIPO'}, $FORM{'_prontus_id'}); # desde el cfg
    if ($msg_err) {
        &glib_html_02::print_pag_result("Error",$msg_err,0,'exit=1,ctype=1,link=nolink');
    };
    %HASH_TIPOS = %$hash_tipos_ref;
    my ($pagina) = &generar_listado();

    # Parseos comunes
    $pagina = &lib_prontus::set_coreplt_ppal($pagina);

    $pagina =~ s/%%OBJTIPO%%/$options_tipo/;

    if (($FORM{'OBJID'}) && ($VERTITLE)) {
        $pagina =~ s/%%COMENT_OBJTIT%%/$VERTITLE/ig;
        $pagina =~ s/<!\/?--vertit-->//isg;
    } else {
        $pagina =~ s/<!--vertit-->.*?<!--\/vertit-->//isg;
    };

    if ($FORM{'OBJTIT_SEARCH'}) {
        my $objtit_search_escaped = &lib_coment::basic_escape_html($FORM{'OBJTIT_SEARCH'});
        $pagina =~ s/%%OBJTIT_SEARCH%%/$objtit_search_escaped/ig;
        $pagina =~ s/<!\/?--OBJTIT_SEARCH-->//isg;
    } else {
        $pagina =~ s/<!--OBJTIT_SEARCH-->.*?<!--\/OBJTIT_SEARCH-->//isg;
    };

    if (($FORM{'NICK'}) && ($VERNICK)) {
        $pagina =~ s/%%COMENT_NICK%%/$VERNICK/ig;
        $pagina =~ s/<!\/?--vernick-->//isg;
    } else {
        $pagina =~ s/<!--vernick-->.*?<!--\/vernick-->//isg;
    };

    print "Content-Type: text/html\n\n";
    print $pagina;
};

# ---------------------------------------------------------------
sub generar_listado {
  # Generar pagina final (loopeando una fila modelo)
  my $pagina = &glib_fildir_02::read_file("$coment_varglb::DIR_SERVER/$FORM{'_prontus_id'}$CPAN_LIST_PAG");
  $pagina =~ /<!--LOOP-->(.*?)<!--\/LOOP-->/isg;
  $LOOP = $1;

  my ($lista, $paginacion) = &make_lista();
  $pagina =~ s/<!--LOOP-->(.*?)<!--\/LOOP-->/$lista/isg;
  if ($paginacion) {
    $pagina =~ s/%%PAGINACION%%/$paginacion/;
  }
  else {
    $pagina =~ s/%%PAGINACION%%/<strong>Sin resultados.<\/strong>/;
  };

  return $pagina;
};
# ---------------------------------------------------------------
sub make_lista {
  my ($sql, $lnk);
  my ($salida, $filas);
  my (%hash_data);

  # Abrir BD.
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_pag_result("Error",$msg_err_bd,0,'exit=1,ctype=1,link=nolink');
    };

    &carga_tabla_secc();
    &carga_tabla_temas();
    &carga_tabla_subtemas();

#  my $filtros;
#  if ($FORM{'OBJID'}) {
#    $filtros = "where COMENT_OBJTIPO = \"$FORM{'OBJTIPO'}\" and COMENT_OBJID = \"$FORM{'OBJID'}\" ";
#  }
#  elsif ($FORM{'OBJTIPO'}) {
#    $filtros = "where COMENT_OBJTIPO = \"$FORM{'OBJTIPO'}\" ";
#  };
#
#  if ($FORM{'NICK'}) {
#    $filtros = "where LOWER(COMENT_NICK) = LOWER(\"$FORM{'NICK'}\") ";
#  };
#
#  if (($FORM{'STATUS'} eq 0 ) || ($FORM{'STATUS'} eq 1)) {
#    $filtros = "where COMENT_STATUS  = \"$FORM{'STATUS'}\" ";
#  };


  my $filtros;
  my %hash_cond;

  $hash_cond{'OBJTIPO'} = " COMENT_OBJTIPO = \"$FORM{'OBJTIPO'}\" ";
  $hash_cond{'STATUS'} = " COMENT_STATUS  = \"$FORM{'STATUS'}\" ";
  $hash_cond{'OBJID'} = " COMENT_OBJID = \"$FORM{'OBJID'}\" ";
  $hash_cond{'NICK'} = " LOWER(COMENT_NICK) = LOWER(\"$FORM{'NICK'}\") ";
  $hash_cond{'EMAIL'} = " COMENT_EMAIL = \"$FORM{'EMAIL'}\" ";
  my $tit_search = $BD->quote($FORM{'OBJTIT_SEARCH'});
  $tit_search =~ s/^'/'%/;
  $tit_search =~ s/'$/%'/;
  $hash_cond{'OBJTIT_SEARCH'} = " COMENT_OBJTIT like $tit_search ";


  if ($FORM{'OBJTIPO'}) { # con condicion base
    $filtros = $hash_cond{'OBJTIPO'};
      if ($FORM{'OBJID'}) {
        $filtros .= ' and ' . $hash_cond{'OBJID'};
      } elsif ($FORM{'NICK'}) {
        $filtros .= ' and ' . $hash_cond{'NICK'};
      } elsif ($FORM{'OBJTIT_SEARCH'}) {
        $filtros .= ' and ' . $hash_cond{'OBJTIT_SEARCH'};
      } elsif (($FORM{'STATUS'} eq 0 ) || ($FORM{'STATUS'} eq 1))  {
        $filtros .= ' and ' . $hash_cond{'STATUS'};
      };
  } else { # sin condicion base
      if ($FORM{'OBJID'}) {
        $filtros = $hash_cond{'OBJID'};
      } elsif ($FORM{'NICK'}) {
        $filtros = $hash_cond{'NICK'};
      } elsif ($FORM{'OBJTIT_SEARCH'}) {
        $filtros = $hash_cond{'OBJTIT_SEARCH'};
      } elsif (($FORM{'STATUS'} eq 0 ) || ($FORM{'STATUS'} eq 1))  {
        $filtros = $hash_cond{'STATUS'};
      };
  };

  $filtros = ' where ' . $filtros if ($filtros);

  my $from = 'COMENT';
  # --- BEGIN:instrucciones paginacion ---
  my $limit;
  my $filasxpag = $FORM{'FILASXPAG_CPAN'};
  my ($tot_artics, $desde_nroreg, $page);
  ($tot_artics, $limit, $desde_nroreg, $page) = &activa_paginacion($filasxpag, $filtros, $from);
  # --- END:instrucciones paginacion ---

  #Valida si existe la columna, si no la crea
  my $ret = &glib_dbi_02::check_table_column($BD, "COMENT", "COMENT_EMAIL", "VARCHAR(100) NOT NULL DEFAULT ''");

  # Generar la lista. # custom
  $sql = "SELECT "
       . "COMENT_ID, "
       . "COMENT_STATUS, "
       . "COMENT_DATETIME, "
       . "COMENT_OBJTIPO, "
       . "COMENT_OBJTIT, "
       . "COMENT_OBJID, "
       . "COMENT_TEXTO, "
       . "COMENT_NICK, "
       . "COMENT_EMAIL, "
       . "ART_IDSECC1, "
       . "ART_IDTEMAS1, "
       . "ART_IDSUBTEMAS1 "
       . "from COMENT left join ART on COMENT_OBJID = ART_ID %%filtros%% order by COMENT_ID desc " . $limit;


  $sql =~ s/%%filtros%%/$filtros/;

  # print $sql;
  # custom
  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \(
           $hash_data{'COMENT_ID'},
           $hash_data{'COMENT_STATUS'},
           $hash_data{'COMENT_DATETIME'},
           $hash_data{'COMENT_OBJTIPO'},
           $hash_data{'COMENT_OBJTIT'},
           $hash_data{'COMENT_OBJID'},
           $hash_data{'COMENT_TEXTO'},
           $hash_data{'COMENT_NICK'},
           $hash_data{'COMENT_EMAIL'},
           $hash_data{'ART_IDSECC1'},
           $hash_data{'ART_IDTEMAS1'},
           $hash_data{'ART_IDSUBTEMAS1'}
           ));

  my $nro_filas = 0;
  while ($salida->fetch) {
    $nro_filas++;
    $filas .= &generar_fila(\%hash_data);
  };
  $salida->finish;

  # $filas = &generar_fila(\%hash_data) if (!$filas);

  # --- BEGIN:instrucciones paginacion ---
  return ($filas, '') if (!$nro_filas);
  # links de paginacion
  my $filtro2send = $FORM{'FILTRO'};
  $filtro2send =~ s/=/%3d/g;

  my $lnk_base = "coment_admin.cgi?_prontus_id=$FORM{'_prontus_id'}&amp;FILASXPAG_CPAN=$FORM{'FILASXPAG_CPAN'}&amp;STATUS=$FORM{'STATUS'}&amp;OBJTIT_SEARCH=$FORM{'OBJTIT_SEARCH'}&amp;OBJTIPO=$FORM{'OBJTIPO'}&amp;OBJID=$FORM{'OBJID'}&amp;NICK=$FORM{'NICK'}"; # a este link solo se le agrega despues el page=nn
  my $paginacion = &generate_pagination_links($page + 1, $filasxpag, $tot_artics, $lnk_base, $desde_nroreg, $nro_filas);
  # --- END:instrucciones paginacion ---

  $BD->disconnect;
  return ($filas, $paginacion);
};

# ---------------------------------------------------------------
sub generar_fila {
# Genera y retorna cada fila de la tabla.
  my $aux = $_[0]; my %hash_data = %$aux;
  my ($fila);

  $fila = $LOOP;

  # custom
  if ($hash_data{'COMENT_ID'}) {
    # Armar la fila.
    $hash_data{'COMENT_DATETIME'} = &lib_coment::print_date_and_time($hash_data{'COMENT_DATETIME'});
    $fila =~ s/%%COMENT_DATETIME%%/$hash_data{'COMENT_DATETIME'}/ig;

    # Tipo obj
    my $tipo = $HASH_TIPOS{$hash_data{'COMENT_OBJTIPO'}}{'NOM'};
    $fila =~ s/%%TIPO%%/$tipo/ig;

    # tit linkeado
    # Si viene la URL, se usa esa, si no viene se asume prontus y ahi se usa $hash_tipos{$id}{'ARTIC_EXTENSION'}
    my $url = $HASH_TIPOS{$hash_data{'COMENT_OBJTIPO'}}{'URL'};

    $url =~ s/<idobj>/$hash_data{'COMENT_OBJID'}/ig;
    if ($url eq '') {
        my $fec = substr($hash_data{'COMENT_OBJID'},0, 8);
        my $artic_extension = $HASH_TIPOS{$hash_data{'COMENT_OBJTIPO'}}{'ARTIC_EXTENSION'};
        $url = "/$FORM{'_prontus_id'}/site/artic/$fec/pags/$hash_data{'COMENT_OBJID'}.$artic_extension";
        # CVI - 29/03/2011 - Para habilitar las friendly urls en el admin de comentarios
        if ($prontus_varglb::FRIENDLY_URLS eq 'SI') {
          $url = &lib_prontus::parse_filef('%%_FILEURL%%', $hash_data{'COMENT_OBJTIT'}, $hash_data{'COMENT_OBJID'}, $FORM{'_prontus_id'}, $url,
          $TABLA_SECC{$hash_data{'ART_IDSECC1'}}, $TABLA_TEMAS{$hash_data{'ART_IDTEMAS1'}}, $TABLA_SUBTEMAS{$hash_data{'ART_IDSUBTEMAS1'}});
        }
    }
    my $lnk_tit = "<a href=\"$url\" target=\"_blank\">$hash_data{'COMENT_OBJTIT'}</a>";

    $fila =~ s/%%LNK_TIT%%/$lnk_tit/ig;

    $hash_data{'COMENT_TEXTO'} = &lib_coment::basic_escape_html($hash_data{'COMENT_TEXTO'});
    $fila =~ s/%%COMENT_TEXTO%%/$hash_data{'COMENT_TEXTO'}/ig;
    $fila =~ s/%%COMENT_NICK%%/$hash_data{'COMENT_NICK'}/ig;
    $fila =~ s/%%COMENT_EMAIL%%/$hash_data{'COMENT_EMAIL'}/ig;
    $VERNICK = $hash_data{'COMENT_NICK'};

    # ver solo opin. de este item
    # my $lnk_vermas = "<a href=\"/cgi-cpn/coment/coment_admin.cgi?OBJID=$hash_data{'COMENT_OBJID'}\"><img src=\"/coment/cpan/imag/ver.gif\" width=\"23\" height=\"14\" border=\"0\" /></a>";
    # my $lnk_vermas = "<a href=\"/cgi-cpn/coment/coment_admin.cgi?OBJTIPO=$hash_data{'COMENT_OBJTIPO'}&OBJID=$hash_data{'COMENT_OBJID'}\"><div class=\"vermas\"></div></a>";
    my $lnk_vermas = "<a title=\"Ver m&aacute;s\" href=\"coment_admin.cgi?OBJTIPO=$hash_data{'COMENT_OBJTIPO'}&amp;OBJID=$hash_data{'COMENT_OBJID'}&amp;_prontus_id=$FORM{'_prontus_id'}\"><span class=\"vermas\"></span></a>";
    $fila =~ s/%%LNK_VERMAS%%/$lnk_vermas/ig;

    # status
    my $img_status = 'btn_ticket_red';
    $img_status = 'btn_ticket_green' if ($hash_data{'COMENT_STATUS'});
    # my $lnk_status = "<a href=\"javascript:cambia_st_ajax($hash_data{'COMENT_ID'})\"><img name=\"status$hash_data{'COMENT_ID'}\" id=\"status$hash_data{'COMENT_ID'}\" src=\"/coment/cpan/imag/$img_status\" width=\"20\" height=\"15\" border=\"0\" alt=\" \" /></a>";
    $fila =~ s/%%STATUS%%/$img_status/ig;
    print STDERR "COMENT_ID[$hash_data{'COMENT_ID'}] img_status[$img_status]\n";

    $fila =~ s/%%COMENT_OBJID%%/$hash_data{'COMENT_OBJID'}/ig;
    $fila =~ s/%%COMENT_ID%%/$hash_data{'COMENT_ID'}/ig;

    # my $lnk_del = "<a href=\"javascript:borra_item_ajax('COMENT_ID', $hash_data{'COMENT_ID'})\" onclick=\"return confirm('¿Está seguro de eliminar este comentario?')\"><img id =\"tarro$hash_data{'COMENT_ID'}\" src=\"/coment/cpan/imag/borrar.gif\" width=\"17\" height=\"19\" border=\"0\"></a>";
    # my $lnk_del = "<a href=\"javascript:borra_item_ajax('COMENT_ID', $hash_data{'COMENT_ID'})\" onclick=\"return confirm('¿Está seguro de eliminar este comentario?')\"><div id =\"tarro$hash_data{'COMENT_ID'}\" class=\"tarro\"></div></a>";

    # $fila =~ s/%%LNK_BORRAR%%/$lnk_del/ig;

    $VERTITLE = $hash_data{'COMENT_OBJTIT'};

  }else {
    # Armar la fila sin datos.
    $fila =~ s/%%\w+?%%/&nbsp;/ig;
  };
  return $fila;
};

# ---------------------------------------------------------------
sub get_tot_artics {
  my ($filtros) = $_[0];
  my ($from) = $_[1];
  my ($sql, $salida, $tot);
  my ($count_art);
  $sql = "select count(COMENT_ID) from $from %%FILTRO%% ";
  if ($filtros ne '') {
    $sql =~ s/%%FILTRO%%/ $filtros /;
  }
  else {
    $sql =~ s/%%FILTRO%%//;
  };
  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($count_art));
  $salida->fetch;
  $salida->finish;
  $count_art = '0' if $count_art eq '';
  return $count_art;

};

# ---------------------------------------------------------------
sub activa_paginacion {
  my ($filasxpag, $filtros, $from) = @_;
  my $tot_artics = &get_tot_artics($filtros, $from);

  # Nro. de la Pagina que hay q desplegar
  my $page = &glib_cgi_04::param('page');
  $page--;
  $page = '0' if ($page<=0);

  # Generar la lista de articulos de esta pagina.
  my $desde_nroreg = $page * $filasxpag;
  my $limit;
  $limit = "LIMIT $desde_nroreg, $filasxpag";
  return ($tot_artics, $limit, $desde_nroreg, $page);

};
# ---------------------------------------------------------------
sub generate_pagination_links {
  my $nav_max_side_links = 5;
  my ($page, $pageSize, $totalRecords, $lnk_base, $desde_nroreg, $nro_filas) = @_;

  my ($hasta_nroreg) = $nro_filas;
  if ($hasta_nroreg == $pageSize) {
    $hasta_nroreg = $desde_nroreg + $pageSize;
  }
  else {
    $hasta_nroreg = $totalRecords;
  };
  $desde_nroreg++;

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

  $links = "<strong>Resultados:</strong> $desde_nroreg a $hasta_nroreg de $totalRecords (M&aacute;s recientes primero)<br/><strong>P&aacute;ginas</strong>: $links";

  return $links;
};

# ---------------------------------------------------------------
sub carga_tabla_secc {
  my ($sql, $salida, $nom, $id);

  $sql = "select SECC_ID, SECC_NOM from SECC ";
  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id, $nom));
  while ($salida->fetch) {
    $TABLA_SECC{$id} = $nom;
  };
  $salida->finish;
};

# ---------------------------------------------------------------
sub carga_tabla_temas {
  my ($sql, $salida, $nom, $id);

  $sql = "select TEMAS_ID, TEMAS_NOM from TEMAS ";
  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id, $nom));
  while ($salida->fetch) {
    $TABLA_TEMAS{$id} = $nom;
  };
  $salida->finish;
};

# ---------------------------------------------------------------
sub carga_tabla_subtemas {
  my ($sql, $salida, $nom, $id);

  $sql = "select SUBTEMAS_ID, SUBTEMAS_NOM from SUBTEMAS ";
  $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($id, $nom));
  while ($salida->fetch) {
    $TABLA_SUBTEMAS{$id} = $nom;
  };
  $salida->finish;
};


# -------------------------------END SCRIPT----------------------


