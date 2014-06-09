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
# PROPOSITO .
# -----------
# Realiza la busqueda de asset (fotos, videos, fotos) en todos los artículos
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
#
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
#
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.1 - 03/07/2009 - PRB - Primera version
# 1.0.1 - 18/05/2010 - YCC - En Begin{} usa $Bin para determinar ruta de las libs CGI
# 1.1.0 - 01/09/2010 - CPN - Se agrega funcionalidad para que accedan todos los usuarios logeados en el publicador, Admin, Editores, Redactores.


# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);

    $pathLibsProntus =~ s/\/dam$//;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use glib_fildir_02;
use lib_prontus;
use lib_dam;
use dam_varglb;
use strict;

my $LOOP_COUNTER = 0;

# ---------------------------------------------------------------
# MAIN.
# -------------
my (%FORM, $LOOP, $BD);
my (%TABLA_SECC, %TABLA_TEMAS, %TABLA_SUBTEMAS);

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'path_conf'}            = &glib_cgi_04::param('path_conf');
    $FORM{'asset_search_type'}    = &glib_cgi_04::param('asset_search_type');
    $FORM{'asset_search_wordkey'} = &glib_cgi_04::param('asset_search_wordkey');
    $FORM{'asset_search_popup'}   = &glib_cgi_04::param('asset_search_popup');
    $FORM{'asset_search_orden'}   = &glib_cgi_04::param('asset_search_orden');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'path_conf'});  # Prontus 6.0

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);

    # Acceso permitido para admin, publicador, redactor CPN
    if (($prontus_varglb::USERS_PERFIL ne 'A') && ($prontus_varglb::USERS_PERFIL ne 'P') && ($prontus_varglb::USERS_PERFIL ne 'E')){
        print "Content-Type: text/html\n\n";
        &glib_html_02::print_pag_result("Acceso a Area Restringida","La funcionalidad requerida está disponible sólo para usuarios registrados.");
        exit;
    };

    # Corrigte el orden
    if($FORM{'asset_search_orden'} !~ /(text_asc|text_desc|pub_asc|pub_desc|creac_asc|creac_desc)/) {
        $FORM{'asset_search_orden'} = 'creac_desc';
    }

    # Arma path de plantilla
    my $plantilla = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID
                . $dam_varglb::DIR_TMPL . $dam_varglb::TMPL_SEARCH;

    my $pagina = &generar_listado($plantilla);

    $pagina = &lib_prontus::set_coreplt_ppal($pagina);

    if($FORM{'asset_search_popup'}) {
        $pagina =~ s/%%POPUP%%(.*?)%%\/POPUP%%//igs;
        $pagina =~ s/%%asset_search_popup%%/1/igs;
    } else {
        $pagina =~ s/%%POPUP%%(.*?)%%\/POPUP%%/\1/igs;
        $pagina =~ s/%%asset_search_popup%%/0/igs;
    }

    $pagina =~ s/%%ASSET_TYPE_FORM%%/$FORM{'asset_search_type'}/ig;

    # Setea filtro
    if ($FORM{'asset_search_type'}) {
        $pagina =~ s/%%sel_$FORM{'asset_search_type'}%%/selected/;
        $pagina =~ s/%%asset_search_type%%/$FORM{'asset_search_type'}/g;
    };

    if ($FORM{'asset_search_wordkey'}) {
        $pagina =~ s/%%asset_search_wordkey%%/$FORM{'asset_search_wordkey'}/;
        $pagina =~ s/<!--search_mode-->(.*?)<!--\/search_mode-->/\1/gsi;
    } else {
        $pagina =~ s/<!--search_mode-->.*?<!--\/search_mode-->//gsi;
    }

    # Setea el orden
    $pagina =~ s/%%asset_search_orden%%/$FORM{'asset_search_orden'}/isg;

    # CVI - 16/06/2011
    my $open_fid_in_pop = 'open_normally';
    if($prontus_varglb::ABRIR_FIDS_EN_POP eq 'SI') {
        $open_fid_in_pop = 'open_in_pop';
    }
    $pagina =~ s/%%_class_open_fid%%/$open_fid_in_pop/ig;
    $pagina =~ s/%%\w+?%%//g;

    print "Cache-Control: no-cache\n";
    print "Cache-Control: max-age=0\n";
    print "Cache-Control: no-store\n";
    print "Content-Type: text/html\n\n";
    print $pagina;


}; # main

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
# ---------------------------------------------------------------
sub generar_listado {
    my $plantilla = $_[0];
    my $pagina = &glib_fildir_02::read_file($plantilla);

    # Elimina las secciones que no son de este tipo
    foreach my $tp (@dam_varglb::TIPOS) {
        # warn('buscando... ' . $tp);
        if($FORM{'asset_search_type'} eq $tp) {
            $pagina =~ s/<!--$tp-->(.*?)<!--\/$tp-->/\1/isg;
        } else {
            $pagina =~ s/<!--$tp-->(.*?)<!--\/$tp-->//isg;
        };
    };

    $pagina =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg;
    $LOOP = $1;

    my ($lista, $paginacion) = &make_lista();
    $pagina =~ s/%%LOOP%%(.*?)%%\/LOOP%%/$lista/isg;
    if ($paginacion) {
        $pagina =~ s/%%_paginacion%%/$paginacion/;
    } else {
        $pagina =~ s/%%_paginacion%%/<strong>Sin resultados.<\/strong>/;
    };

    return $pagina;
};
# ---------------------------------------------------------------
sub make_lista {

    my ($sql, $lnk);
    my ($salida, $filas);
    my (%hash_data);

    # Si no vienen filtros retorna vacio
    if (($FORM{'asset_search_type'} eq '') && ($FORM{'asset_search_wordkey'} eq '')) {
        return ('', '');
    };

    # Conectar a BD
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_pag_result("Error",$msg_err_bd,1,'ctype=1');
    };

    &carga_tabla_secc();
    &carga_tabla_temas();
    &carga_tabla_subtemas();

    # Filtros
    my $filtros = '';
    my $where = 0;
    if ($FORM{'asset_search_wordkey'}) {
        $filtros = "where MATCH (ASSET_SEARCH_WORDKEY) AGAINST (\"$FORM{'asset_search_wordkey'}\" IN BOOLEAN MODE) ";
        $where = 1;
    };

    if ($FORM{'asset_search_type'}) {
        my $concatena = ($where)?'and':'where';
        $filtros .= $concatena . " ASSET_TYPE = \"$FORM{'asset_search_type'}\" ";
    };

    # Orden
    my $orderby = 'ASSET_SEARCH_WORDKEY ASC';
    if($FORM{'asset_search_orden'} =~ /(\w+)_(asc|desc)/) {
        my $field = $1;
        my $ord = $2;
        if($field eq 'text') {
            $orderby = 'ASSET_SEARCH_WORDKEY ' . $ord ;
        } elsif($field eq 'creac') {
            $orderby = 'ASSET_ART_ID ' . $ord;
        } else {
            $orderby = 'ASSET_SEARCH_WORDKEY ' . $ord;
        };
    };

    # Si es foto, aplicar group by al filtro... para que el conteo de resultados sea correcto.
    if ($FORM{'asset_search_type'} eq 'foto') {
        $filtros .= " GROUP BY ASSET_ART_ID";
    };

    # Paginacion
    my $filasxpag = $dam_varglb::FILASXPAG;
    my ($tot_artics, $limit, $desde_nroreg, $page) = &activa_paginacion($filasxpag, $filtros, 'ASSET');

    # Si el tipo es foto, se debe usar un query especial, donde el listado de fotos se agrupe.
    # Por defecto, solo se mostrarán 4 fotos como máximo.
    # * Nota: se me había ocurrido retornalas todas y dejarlas en divs ocultos pero el largo del resultado
    # de mysql no puede exceder un cierto limite. Se puede aumentar, pero no es la idea.
    if ($FORM{'asset_search_type'} eq 'foto') {
        $sql = "SELECT ASSET_ART_ID, ART_IDSECC1, ART_IDTEMAS1, ART_IDSUBTEMAS1, ASSET_SEARCH_WORDKEY,
                ASSET_ART_FID, ASSET_ART_FILE,
                SUBSTRING_INDEX(
                    GROUP_CONCAT(ASSET_FILE,'|',ASSET_ART_WFOTO,'|',ASSET_ART_HFOTO,'|',ASSET_SEARCH_TEXTO,'|',ASSET_SEARCH_FOTO SEPARATOR '\t'),
                    '\t', 4) as ASSET_LIST
                FROM ASSET LEFT JOIN ART ON (ASSET_ART_ID=ART_ID) " . $filtros . " order by " . $orderby . " " . $limit;

        $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \(
            $hash_data{'ASSET_ART_ID'}, $hash_data{'ART_IDSECC1'}, $hash_data{'ART_IDTEMAS1'},
            $hash_data{'ART_IDSUBTEMAS1'}, $hash_data{'ASSET_SEARCH_WORDKEY'}, $hash_data{'ASSET_ART_FID'},
            $hash_data{'ASSET_ART_FILE'}, $hash_data{'ASSET_LIST'}
        ));

    # Aca se utiliza la query antigua.
    } elsif (($FORM{'asset_search_type'} eq 'video') || ($FORM{'asset_search_type'} eq 'audio')) {
        $sql = 'select ASSET_ART_ID, ASSET_FILE, ASSET_SEARCH_WORDKEY, ASSET_SEARCH_TEXTO, ASSET_SEARCH_FOTO, ASSET_TYPE, ASSET_ART_WFOTO,'
             . ' ASSET_ART_HFOTO, ASSET_ART_FID, ASSET_ART_FILE, ART_IDSECC1, ART_IDTEMAS1, ART_IDSUBTEMAS1 from ASSET left join ART on ASSET_ART_ID = ART_ID ' . $filtros
             . ' order by ' . $orderby . ' ' . $limit;

        $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \(
            $hash_data{'ASSET_ART_ID'}, $hash_data{'ASSET_FILE'}, $hash_data{'ASSET_SEARCH_WORDKEY'},
            $hash_data{'ASSET_SEARCH_TEXTO'}, $hash_data{'ASSET_SEARCH_FOTO'}, $hash_data{'ASSET_TYPE'},
            $hash_data{'ASSET_ART_WFOTO'}, $hash_data{'ASSET_ART_HFOTO'}, $hash_data{'ASSET_ART_FID'},
            $hash_data{'ASSET_ART_FILE'}, $hash_data{'ART_IDSECC1'}, $hash_data{'ART_IDTEMAS1'}, $hash_data{'ART_IDSUBTEMAS1'},
        ));
    } else {
        return ('', '');
    };


    my $nro_filas = 0;
    while ($salida->fetch) {
        $nro_filas++;
        $filas .= &generar_fila(\%hash_data);
    };

    $salida->finish;
    my $path_conf = $prontus_varglb::DIR_CPAN . '/' . $prontus_varglb::PRONTUS_ID . '.cfg';
    my $lnk_base = 'prontus_dam_search.cgi?path_conf=' . $path_conf
                 . '&amp;asset_search_type=' . $FORM{'asset_search_type'}
                 . '&amp;asset_search_wordkey=' . $FORM{'asset_search_wordkey'}
                 . '&amp;asset_search_popup=' . $FORM{'asset_search_popup'};
    my $paginacion = &generate_pagination_links($page + 1, $filasxpag, $tot_artics, $lnk_base, $desde_nroreg, $nro_filas);
    return ($filas, $paginacion);

};

# ---------------------------------------------------------------
sub generar_fila {
    # Genera y retorna cada fila de la tabla.
    my $aux = $_[0];
    my %hash_data = %$aux;
    my ($fila, $titular);

    $fila = $LOOP;
    if ($hash_data{'ASSET_ART_ID'}) {
        $fila =~ s/%%ASSET_ART_ID%%/$hash_data{'ASSET_ART_ID'}/g;
        # $fila =~ s/%%ASSET_FILE%%/$hash_data{'ASSET_FILE'}/g;
        # $fila =~ s/%%ASSET_TYPE%%/$hash_data{'ASSET_TYPE'}/g;

        # $fila =~ s/%%ASSET_SEARCH_TEXTO%%/$hash_data{'ASSET_SEARCH_TEXTO'}/g;
        # $fila =~ s/%%ASSET_SEARCH_FOTO%%/$hash_data{'ASSET_SEARCH_FOTO'}/g;

        # Extrae titular
        $hash_data{'ASSET_SEARCH_WORDKEY'} =~ /\|(.*)\|/;
        $titular = $1;
        my $titular2 = $titular;
        $titular2 =~ s/"/&quot;/g;
        $titular2 =~ s/\n/ /g;
        $titular2 =~ s/ +/ /g;
        $fila =~ s/%%ASSET_TITULAR%%/$titular2/g;
        my $titular3 = $titular;
        $titular3 = &lib_prontus::ajusta_nchars($titular3, 80);
        $fila =~ s/%%ASSET_TITULAR_SHORT%%/$titular3/g;

        # Directorio de articulo
        $hash_data{'ASSET_ART_ID'} =~ /^(\d{8})\d{6}$/;
        my $dir_fecha = $1;

        # Genera link para abrir FID
        my $tipo_ficha = $hash_data{'ASSET_ART_FID'};
        my $path_conf = $prontus_varglb::DIR_CPAN . '/' . $prontus_varglb::PRONTUS_ID . '.cfg';
        my $link_fid = $prontus_varglb::SERVER_NAME . '/' . $prontus_varglb::DIR_CGI_CPAN
                     . '/prontus_art_ficha.' . $prontus_varglb::EXTENSION_CGI
                     . '?_file='. $hash_data{'ASSET_ART_FILE'}
                     . '&amp;_fid=' . $tipo_ficha
                     . '&amp;_path_conf=' . $path_conf
                     . '&amp;fotosvtxt=/1/2/3/4';
        $fila =~ s/%%LINK_FID%%/$link_fid/g;

        # Genera link para el artículo
        my $link_artic = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC.'/'.$dir_fecha.$prontus_varglb::DIR_PAG.'/'.$hash_data{'ASSET_ART_FILE'};
        # CVI - 29/03/2011 - Para habilitar las friendly urls en el admin de multimedia
        if ($prontus_varglb::FRIENDLY_URLS eq 'SI') {
          $link_artic = &lib_prontus::parse_filef('%%_FILEURL%%', $titular,
                $hash_data{'ASSET_ART_ID'}, $prontus_varglb::PRONTUS_ID, $link_artic,
                $TABLA_SECC{$hash_data{'ART_IDSECC1'}},$TABLA_TEMAS{$hash_data{'ART_IDTEMAS1'}},$TABLA_SUBTEMAS{$hash_data{'ART_IDSUBTEMAS1'}});
        }
        $fila =~ s/%%LINK_ARTIC%%/$link_artic/g;

        # contenido de asset
        my $asset = '';
        my $path_img = '';
        my $path_img_dam = '';
        my $path_asset = '';
        my $width_img = '';

        if ($FORM{'asset_search_type'} eq 'foto') {
            my @asset_list;
            if ($hash_data{'ASSET_LIST'}) {
                @asset_list = split(/\t/, $hash_data{'ASSET_LIST'});
            };

            my $asset_count = (scalar @asset_list);
            my $holder_class = 'tip' . $asset_count;
            my $foto_filas;

            $fila =~ /<!--foto_loop-->(.*?)<!--\/foto_loop-->/isg;
            my $loop_foto = $1;
            my $counter = 0;
            my $ultima_foto;

            foreach my $values_string (@asset_list) {
                my $loop_foto_tmp = $loop_foto;
                my ($asset_file, $asset_width, $asset_height, $asset_search_texto, $asset_search_foto) = split(/\|/, $values_string);
                $path_img = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . '/' . $dir_fecha . '/imag/' . $asset_file;
                my $path_img_dam = $path_img;
                $path_img_dam =~ s/(\.\w+)$/\.dam\1/;

                # # Si no existe la foto para el dam, se crea.
                # if(!-f $prontus_varglb::DIR_SERVER . $path_img_dam) {
                #     my $lafoto = $prontus_varglb::DIR_SERVER . '/' . $prontus_varglb::PRONTUS_ID . '/site/artic/' . $dir_fecha . '/imag/' . $asset_file;
                #     &lib_dam::genera_thumbnail_for_dam($lafoto);
                #     if (!-f $prontus_varglb::DIR_SERVER . $path_img_dam) {
                #         # Si no se crea, quiere decir que la foto es mas chica de lo esperado.
                #         # Se debe utilizarla misma.
                #         $path_img_dam = $path_img;
                #     };
                # };

                $ultima_foto = $path_img;
                $loop_foto_tmp =~ s/%%FOTO_SRC%%/$path_img/g;
                $loop_foto_tmp =~ s/%%HOLDER_CLASS%%/$holder_class/g;
                $foto_filas .= $loop_foto_tmp;
                $counter++;
            };

            $fila =~ s/<!--foto_loop-->.*?<!--\/foto_loop-->/$foto_filas/sg;
            $fila =~ s/%%_TS%%/$hash_data{'ASSET_ART_ID'}/g;

            # Si hay una solo foto, se debe quitar el icono de mostrar todas y mostrar el icono de copiar la url.
            if ($asset_count == 1) {
                $fila =~ s/%%PATH_ASSET%%/$ultima_foto/sg;
                $fila =~ s/<!--ver_todas-->.*?<!--\/ver_todas-->//sg;
            } else {
                # Si hay mas de una, el copiar se hará dentro del colorbox.
                $fila =~ s/<!--link_copiar-->.*?<!--\/link_copiar-->//sg;
            };

        } elsif (($FORM{'asset_search_type'} eq 'video') || ($FORM{'asset_search_type'} eq 'audio')) {
                $path_img = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . '/' . $dir_fecha . '/imag/' . $hash_data{'ASSET_FILE'};
                $path_asset = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . '/' . $dir_fecha
                              . '/mmedia/' . $hash_data{'ASSET_FILE'};

                $path_img_dam = $path_img;
                $path_img_dam =~ s/(\.\w+)$/-dam\1/;

                if(-f $prontus_varglb::DIR_SERVER . $path_img_dam) {
                    $path_img = $path_img_dam;
                };

                if($hash_data{'ASSET_SEARCH_FOTO'}) {
                    my $imgsize = 'width="'.$dam_varglb::FOTOS_WIDTH_MAX.'" ';
                    $fila =~ s/%%IMG_SIZE%%/$imgsize/g;
                    $path_img = $hash_data{'ASSET_SEARCH_FOTO'};

                } else {
                    my $path_foto = $path_asset;
                    $path_foto =~ s/(\.\w+)$/.jpg/;
                    if(-f ($prontus_varglb::DIR_SERVER . $path_foto)) {
                        my $imgsize = 'width="'.$dam_varglb::FOTOS_WIDTH_MAX.'" ';
                        $fila =~ s/%%IMG_SIZE%%/$imgsize/g;
                        $path_img = $path_foto;
                    } else {
                        $fila =~ s/<!--if_image-->.*?<!--\/if_image-->//sg;
                    };
                };
                $fila =~ s/<!--tam_foto-->.*?<!--\/tam_foto-->//sg;

                $path_img_dam = $path_img unless($path_img_dam);
                $fila =~ s/%%PATH_IMG%%/$path_img/g;
                $fila =~ s/%%PATH_IMG_THUMB%%/$path_img_dam/g;
                $fila =~ s/%%PATH_ASSET%%/$path_asset/g;
                $fila =~ s/%%WIDTH_IMG%%/$width_img/g;


        } else {
            $fila =~ s/<!--tam_foto-->.*?<!--\/tam_foto-->//sg;

        };

    } else {
        # Armar la fila sin datos.
        $fila =~ s/%%\w+?%%/&nbsp;/ig;
    };

    $LOOP_COUNTER++;
    $fila =~ s/%%LOOP_COUNTER%%/$LOOP_COUNTER/g;

    return $fila;

};

# ---------------------------------------------------------------
sub get_tot_artics {
  my ($filtros) = $_[0];
  my ($from) = $_[1];
  my ($sql, $salida, $tot, $count_art);

  $sql = 'select count(ASSET_ART_ID) from ' . $from . ' ' . $filtros;

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
    $limit = " LIMIT $desde_nroreg, $filasxpag";
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

    $links = "<strong>Resultados:</strong> $desde_nroreg a $hasta_nroreg de $totalRecords <br/><strong>P&aacute;ginas</strong>: $links";

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

# ---- END SCRIPT ---
