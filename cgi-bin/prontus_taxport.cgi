#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------


BEGIN {
    use FindBin '$Bin';
    $pathLibs = $Bin;
    unshift(@INC, $pathLibs);
    require 'dir_cgi.pm';
    $pathLibs =~ s/(\/)[^\/]+$/\1$DIR_CGI_CPAN/;
    unshift(@INC,$pathLibs);
};

our $DIR_CGI_PUBLIC;
our $DIR_CGI_CPAN;

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();

#use strict;
use lib_maxrunning;
use lib_prontus;
use glib_html_02;
use lib_ipcheck;
use glib_cgi_04;
use glib_fildir_02;
use lib_tax;
use POSIX qw(strftime ceil);

my (%FORM, %FIDS, %TABLA_SECC, %TABLA_TEM, %TABLA_STEM, %CFG_FIL_TAXPORT);
my ($SECCION_ID, $TEMA_ID, $SUBTEMA_ID, $NRO_PAGINA, $PLT, $EXT, $MV, $FID, $BD);
my ($SECCION_NOM, $TEMA_NOM, $SUBTEMA_NOM, $FIXEDURL, %MSGS);
my $PORT_TMP_DIR; # Directorio de plantillas
my $PORT_TMP_FILE; # Ruta completa de la plantilla.
my $CACHE_REL_DIR; # Ruta relativa al directorio de cache.
my $CACHE_DIR; # Ruta absoluta al directorio de cache.s

main: {
    &glib_cgi_04::new();

    $FORM{"taxport"} = &glib_cgi_04::param("taxport");

    &valida_parametros();

    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();

    if (!ref($BD)) {
        print STDERR "Error conectar BD: $msg_err_bd\n";
        &show_error("Error de conexión a la base de datos.");
        exit;
    }

    %TABLA_SECC = &lib_tax::carga_tabla_seccion($BD);
    %TABLA_TEM = &lib_tax::carga_tabla_temas($BD);
    %TABLA_STEM = &lib_tax::carga_tabla_subtemas($BD);

    &valida_taxonomia();
    &generar_portada();
};

sub valida_taxonomia {

    if ($SECCION_ID) {
        my ($nom, $port, $nom4vistas) = split (/\t\t/, $TABLA_SECC{$SECCION_ID});

        if (!$nom) {
            print STDERR "ERROR: La seccion no existe.\n";
            show_error("Parámetros incorrectos.");
        } else {
            $SECCION_NOM = $nom;
        }

        $FIXEDURL = $port if ($port);
    }

    if ($TEMA_ID) {
        my ($nom, $port, $idparent, $nom4vistas) = split (/\t\t/, $TABLA_TEM{$TEMA_ID});

        if (!$nom) {
            print STDERR "ERROR: El tema no existe.\n";
            show_error("Parámetros incorrectos.");
        } else {
            $TEMA_NOM = $nom;
        }

        $FIXEDURL = $port if ($port);
    }

    if ($SUBTEMA_ID) {
        my ($nom, $port, $idparent, $nom4vistas) = split (/\t\t/, $TABLA_STEM{$SUBTEMA_ID});

        if (!$nom) {
            print STDERR "ERROR: El subtema no existe.\n";
            show_error("Parámetros incorrectos.");
        } else {
            $SUBTEMA_NOM = $nom;
        }

        $FIXEDURL = $port if ($port);
    }

};

sub generar_portada {
    my $sql = get_query();
    my $tot_artics = &get_total($sql);
    my $loopcounter = 1;
    my ($filtro_paginacion, $total_pags) = &get_filtro_paginacion($tot_artics);
    my $reldir_artic = "$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC/%%DIRFECHA%%$prontus_varglb::DIR_PAG";
    my $path_include = &lib_prontus::get_path_croncgi();
    my ($pagina, $loop) = &get_pagina_y_loop();
    my $output;
    my $art_id;
    my $dst_file = "/$FID/$PLT\_$SECCION_ID\_$TEMA_ID\_$SUBTEMA_ID\_$NRO_PAGINA\_cache.$EXT";

    $sql = "$sql $filtro_paginacion";

    print STDERR "sql[$sql]\n";

    my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($art_id));

    while ($salida->fetch) {
        my ($fila_content, $auxref, $auxref2) = &lib_tax::generar_fila($reldir_artic, $art_id, $EXT, $loop, $loopcounter, $tot_artics);
        $output .= $fila_content;
        $loopcounter++;
    }

    $salida->finish;

    $pagina =~ s/%%LOOP%%.*?%%\/LOOP%%/$output/sig; # Se reemplaza el loop.

    # Paginacion.
    if ($pagina !~  /%%_no_paginar%%/) {
        $pagina = &incluir_navbar($pagina, $SECCION_ID, $TEMA_ID, $SUBTEMA_ID, $MV, $EXT, $PLT);
        $pagina = &incluir_nrosdepag($tot_artics, $pagina, $NRO_PAGINA, $SECCION_ID, $TEMA_ID, $SUBTEMA_ID, $MV, $EXT, $PLT);
    }

    $pagina =~ s/%%_totartics%%/$tot_artics/ig;
    $pagina =~ s/%%_plt_nom%%/$PLT/isg;
    $pagina =~ s/%%_plt_ext%%/$EXT/isg;
    $pagina =~ s/%%_tax_fid%%/$FID/isg if ($FID);
    $pagina =~ s/%%NOMSECC%%/$SECCION_NOM/isg;
    $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
    $pagina =~ s/%%_SERVER_NAME%%/$prontus_varglb::PUBLIC_SERVER_NAME/isg;
    $pagina =~ s/%%_nropagina%%/$NRO_PAGINA/isg;
    $pagina =~ s/%%_vista%%/$MV/isg;

    $FIXEDURL = &lib_prontus::get_tax_link($FIXEDURL, $MV);
    $pagina =~ s/%%_FIXED_URL%%/$FIXEDURL/isg;

    # Para poder hacer IF de seccion, tema y subtema
    my %claves = ('_tax_seccion' => $SECCION_ID, '_tax_tema' => $TEMA_ID, '_tax_subtema' => $SUBTEMA_ID,
            '_tax_nom_seccion' => $SECCION_NOM, '_tax_nom_tema' => $TEMA_NOM, '_tax_nom_subtema' => $SUBTEMA_NOM);

    my %claves_compatibles = ('_seccion1' => $SECCION_ID, '_tema1' => $TEMA_ID, '_subtema1' => $SUBTEMA_ID,
            '_nom_seccion1' => $SECCION_NOM, '_nom_tema1' => $TEMA_NOM, '_nom_subtema1' => $SUBTEMA_NOM,
            '_vista' => $MV, '_nropagina' => $NRO_PAGINA, '_tax_fid' => $FID);

    $pagina = &lib_prontus::procesa_condicional($pagina, \%claves, \%claves_compatibles);

    $pagina =~ s/%%_SECCION[1-3]%%/$SECCION_ID/isg;
    $pagina =~ s/%%_TEMA[1-3]%%/$TEMA_ID/isg;
    $pagina =~ s/%%_SUBTEMA[1-3]%%/$SUBTEMA_ID/isg;
    $pagina =~ s/%%_NOM_SECCION[1-3]%%/$SECCION_NOM/isg;
    $pagina =~ s/%%_NOM_TEMA[1-3]%%/$TEMA_NOM/isg;
    $pagina =~ s/%%_NOM_SUBTEMA[1-3]%%/$SUBTEMA_NOM/isg;

    # Se parsean las nuevas marcas de taxport
    $pagina =~ s/%%_tax_seccion%%/$SECCION_ID/isg;
    $pagina =~ s/%%_tax_tema%%/$TEMA_ID/isg;
    $pagina =~ s/%%_tax_subtema%%/$SUBTEMA_ID/isg;
    $pagina =~ s/%%_tax_nom_seccion%%/$SECCION_NOM/isg;
    $pagina =~ s/%%_tax_nom_tema%%/$TEMA_NOM/isg;
    $pagina =~ s/%%_tax_nom_subtema%%/$SUBTEMA_NOM/isg;

    # Parsear el nombre de la s, t, st segun la vista.
    if ($MV) {
        my ($mv_nom_seccion1, $mv_nom_tema1, $mv_nom_subtema1) = &lib_prontus::get_nom4vistas($MV, $SECCION_ID, $TEMA_ID, $SUBTEMA_ID);
        $pagina =~ s/%%_tax_nom_seccion_$MV%%/$mv_nom_seccion1/isg;
        $pagina =~ s/%%_tax_nom_tema_$MV%%/$mv_nom_tema1/isg;
        $pagina =~ s/%%_tax_nom_subtema_$MV%%/$mv_nom_subtema1/isg;
        $pagina =~ s/%%_nom_seccion[1-3]_$MV%%/$mv_nom_seccion1/isg;
        $pagina =~ s/%%_nom_tema[1-3]_$MV%%/$mv_nom_tema1/isg;
        $pagina =~ s/%%_nom_subtema[1-3]_$MV%%/$mv_nom_subtema1/isg;
    }

    $pagina = &lib_prontus::parser_custom_function($pagina, $path_include);
    $pagina = &lib_prontus::parse_includes($prontus_varglb::DIR_SERVER, $pagina);

    $pagina =~ s/%%.*?%%//isg; # quita la marcas que no se parsearon.

    &glib_fildir_02::check_dir("$CACHE_DIR/$FID");
    &glib_fildir_02::write_file("$CACHE_DIR$dst_file", $pagina);

    print "Content-type: text/html\n\n";
    print '<!--# include virtual="' . $CACHE_REL_DIR . $dst_file . '?noloop" -->';
    # print "Location: $CACHE_REL_DIR$dst_file\n\n";
    exit;
};

sub get_pagina_y_loop {
    my $pagina = &glib_fildir_02::read_file($PORT_TMP_FILE);
    my $dirmacros = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_PTEMA_MACROS";
    my $loop;

    $pagina = &lib_prontus::add_macros($pagina, $dirmacros) if(-d $dirmacros);

    if ($pagina =~ /%%LOOP%%(.*?)%%\/LOOP%%/isg) {
        $loop = $1;
    }

    $MSGS{'no_results'} = 'No se encontraron resultados.';

    while ($pagina =~ /<!--\s*MSG\s*(\w+)\s*=\s*(.+?)\s*-->/sg) {
        $MSGS{$1} = $2;
    }

    # Elimina mensajes de la plantilla.
    $pagina =~ s/<!--\s*MSG\s*(\w+)\s*=\s*(.+?)\s*-->//sg;

    return ($pagina, $loop);
};

sub get_query {
    my $sql;

    $sql = "SELECT ART_ID FROM ART WHERE 1=1 ";
    $sql .= " AND ART_IDSECC1 = $SECCION_ID" if ($SECCION_ID);
    $sql .= " AND ART_IDTEMAS1 = $TEMA_ID" if ($TEMA_ID);
    $sql .= " AND ART_IDSUBTEMAS1 = $SUBTEMA_ID" if ($SUBTEMA_ID);
    $sql .= " AND ART_TIPOFICHA = '$FID'" if ($FID && $FID !~ /^(all|fil_)/);

    if ($FID =~ /^fil_/) {
        my @elems = @{$CFG_FIL_TAXPORT{$FID}{'FIDS'}};
        my $str = sprintf "'%s'," x @elems, @elems;
        $str = substr($str, 0, (length $str) - 1);
        $sql .= " AND ART_TIPOFICHA IN ($str)";
    }

    $sql .= " ORDER BY $prontus_varglb::TAXPORT_ORDEN";

    return $sql;
};

sub get_total {
    my $sql = $_[0];

    $sql =~ s/SELECT .*? FROM/SELECT COUNT\(*\) FROM/sg;

    my $tot;
    my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($tot));
    $salida->fetch;
    $salida->finish;

    return $tot;
};

sub get_filtro_paginacion {
    my $total = $_[0];
    my $sql;
    my $num_pags = ceil($total / $prontus_varglb::TAXPORT_ARTXPAG);

    if ($NRO_PAGINA ne '') {
        $NRO_PAGINA = $num_pags if ($num_pags && $NRO_PAGINA > $num_pags);

        my $p = $NRO_PAGINA - 1;
        my $limit = $p * $prontus_varglb::TAXPORT_ARTXPAG;

        $sql = " LIMIT $limit, $prontus_varglb::TAXPORT_ARTXPAG";
    }

    return ($sql, $num_pags);
};

sub valida_parametros {
    if ($FORM{"taxport"} eq '') {
        &show_error("Parámetros insuficientes.");
    } else {
        # /prontus_develop/fid_noticia-movil/taxport_1_1_1_1
        $FORM{"taxport"} =~ s/^\///; # quitar el / del principio.

        my ($prontus_id, $filtro, $taxport) = split(/\//, $FORM{"taxport"});

        if ($filtro =~ /^(\w+)-?(\w+)?$/) {
            $FID = $1;
            $MV = $2;
        }

        if (!$FID) {
            &show_error("Parámetros incorrectos.");
        }

        if ($taxport =~ /^([a-zA-Z0-9]+)_(\d+)?_(\d+)?_(\d+)?_(\d+)\.(\w+)$/) {
            ($PLT, $SECCION_ID, $TEMA_ID, $SUBTEMA_ID, $NRO_PAGINA, $EXT) = ($1, $2, $3, $4, $5, $6);

            $NRO_PAGINA = 1 if (!$NRO_PAGINA);

            if (!$SECCION_ID && $TEMA_ID) { # no puede venir un tema sin seccion.
                &show_error("Parámetros incorrectos.");
            } elsif (!$TEMA_ID && $SUBTEMA_ID) { # no puede venir un subtema sin tema.
                &show_error("Parámetros incorrectos.");
            }

        } else {
            &show_error("Parámetros incorrectos.");
        }

        if(!&lib_prontus::valida_prontus($prontus_id)) {
            &show_error("Instancia de Prontus no valida.");
        } else {
            # Cargar configuracion de Prontus.
            my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($prontus_id);
            &lib_prontus::load_config(&lib_prontus::ajusta_pathconf($relpath_conf));

            &carga_fids();

            if ($FID ne 'all' && $FID !~ /^fil_/ && !defined $FIDS{$FID}) {
                &show_error("Parámetros incorrectos.");
            }

            # Validar plantilla.
            $PORT_TMP_DIR = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_PTEMA";
            $PORT_TMP_FILE = "$PORT_TMP_DIR/$filtro/$PLT.$EXT";

            if (!-f $PORT_TMP_FILE) {
                print STDERR "ERROR: La plantilla [$PORT_TMP_FILE] no existe.\n";
                &show_error("Parámetros incorrectos.");
            }

            $CACHE_REL_DIR = "/$prontus_varglb::PRONTUS_ID/site/tax/port";
            $CACHE_DIR = "$prontus_varglb::DIR_SERVER$CACHE_REL_DIR";

            # Si es fil_, cargar configuracion.
            if ($FID =~ /^fil_/) {
                &cargar_fil_cfg("$PORT_TMP_DIR/$filtro/filtros.cfg", $FID);

                # Solo para filtros. Si estan configuradas las plantillas, solo se consideran esas.
                if ($FID =~ /^fil_/ && defined $CFG_FIL_TAXPORT{$FID}{'PLANTILLAS'} && !defined $CFG_FIL_TAXPORT{$FID}{'PLANTILLAS'}{"$PLT.$EXT"}) {
                    print STDERR "ERROR: Portada fil, plantilla incorrecta.\n";
                    show_error("Parámetros incorrectos.");
                }
            }
        }
    }
};

sub carga_fids {
    foreach my $key (keys %prontus_varglb::FORM_PLTS) { # key = 'fid_general:General(general.php)'
        my $fid_name;
        next if ($key !~ /^(\w+) *:/);
        $fid_name = $1;
        $FIDS{$fid_name}  = 1;
    }
};

# sub taxport_garbage {
#     my @dirs = glob("$CACHE_DIR/*");

#     foreach my $dir (@dirs) {
#         my @files = glob("$dir/*");

#         if (!scalar @files) { # directorios vacios se borran.
#             unlink $dir;
#         } else {
#             foreach my $file (@files) {
#                 if (-f $file) { # Solo si es archivo, no se permiten subdirectorios.
#                     if ((stat($file))[9] < (time - 600)) {
#                         unlink $file;
#                     }
#                 }
#             }
#         }
#     }

# };

sub cargar_fil_cfg {
    my $file = $_[0];
    my $fil = $_[1];

    return if (!-f $file);

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
    }

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
        }

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

    }

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
    }

};

sub incluir_navbar {
    my ($pagina, $secc_id, $temas_id, $subtemas_id, $mv, $extension, $nombase) = @_;
    my $secc_tema_stema_nom;
    my ($secc_nom, $secc_port, $secc_nom4vistas) = split (/\t\t/, $TABLA_SECC{$secc_id});

    $secc_nom = &lib_prontus::get_nomtax_envista($mv, $secc_nom4vistas) if ($mv);
    $secc_nom = &lib_prontus::escape_html($secc_nom);

    # Se lee el separador
    my $separador = '/';

    if ($pagina =~ /%%_secc_tema_stema_nom\((.*?)\)%%/i) {
      $separador = $1;
    }

    # Seccion.
    if ($secc_nom) {
        my $lnk_secc;

        if ($secc_port) {
            $lnk_secc = &lib_prontus::get_tax_link($secc_port);
        } else {
            $lnk_secc = "/$prontus_varglb::PRONTUS_ID/site/tax/port";
            $lnk_secc .= "/$FID" if (!$mv);
            $lnk_secc .= "/$FID-$mv" if ($mv);
            $lnk_secc .= "/$nombase\_$secc_id\___$NRO_PAGINA.$extension";
        }

        $secc_tema_stema_nom = "<a href='$lnk_secc'>$secc_nom</a>";
    }

    my ($tem_nom, $tem_port, $filler1, $tem_nom4vistas) = split (/\t\t/, $TABLA_TEM{$temas_id});
    $tem_nom = &lib_prontus::get_nomtax_envista($mv, $tem_nom4vistas) if ($mv);
    $tem_nom = &lib_prontus::escape_html($tem_nom);

    # Tema.
    if ($tem_nom) {
        my $lnk_tem;

        if ($tem_port) {
            $lnk_tem = &lib_prontus::get_tax_link($tem_port);
        } else {
            $lnk_tem = "/$prontus_varglb::PRONTUS_ID/site/tax/port";
            $lnk_tem .= "/$FID" if (!$mv);
            $lnk_tem .= "/$FID-$mv" if ($mv);
            $lnk_tem .= "/$nombase\_$secc_id\_$temas_id\__$NRO_PAGINA.$extension";
        }

        $secc_tema_stema_nom .= " $separador <a href='$lnk_tem'>$tem_nom</a>";
    }

    my ($stem_nom, $stem_port, $filler2, $stem_nom4vistas) = split (/\t\t/, $TABLA_STEM{$subtemas_id});
    $stem_nom = &lib_prontus::get_nomtax_envista($mv, $stem_nom4vistas) if ($mv);
    $stem_nom = &lib_prontus::escape_html($stem_nom);

    # Subtema.
    if ($stem_nom) {
        my $lnk_stem;

        if ($stem_port) {
            $lnk_stem = &lib_prontus::get_tax_link($stem_port);
        } else {
            $lnk_stem = "/$prontus_varglb::PRONTUS_ID/site/tax/port";
            $lnk_stem .= "/$FID" if (!$mv);
            $lnk_stem .= "/$FID-$mv" if ($mv);
            $lnk_stem .= "/$nombase\_$secc_id\_$temas_id\_$subtemas_id\_$NRO_PAGINA.$extension";
        }

        $secc_tema_stema_nom .=  " $separador <a href='$lnk_stem'>$stem_nom</a>";
    }

    $pagina =~ s/%%_SECC_TEMA_STEMA_NOM.*?%%/$secc_tema_stema_nom/isg;

    return $pagina;
};

sub incluir_nrosdepag {
    my ($tot_artics, $pagina, $nro_pag, $secc_id, $temas_id, $subtemas_id, $mv, $extension, $nombase) = @_;
    my $tpl_nropag = '<a href="%%lnk%%">%%cnro_pag%%</a>';
    my $tpl_nropag2 = '<span class="actual">%%cnro_pag%%</span>';
    my $tpl_separador = '...';
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
    }

    # Quitar comentarios de configuración.
    $pagina =~ s/<!--\s*CONFIG\s*(\w+)\s*=\s*(.+?)\s*-->//sg;

    my $nro_paginas_totales = ceil($tot_artics / $prontus_varglb::TAXPORT_ARTXPAG);
    my ($ini, $fin, $nextlink, $prevlink);

    if ($prontus_varglb::TAXPORT_TIPO_PAGINACION eq '1') {
        # Se procesan las paginas hacia abajo
        $ini = ($nro_pag - $prontus_varglb::TAXPORT_PAGCORTA_MAXPAGS);

        if ($ini le 1) {
            $ini = 1;
        } else {
            $ini = $ini + 1;
            my $lnk;

            $lnk = "/$prontus_varglb::PRONTUS_ID/site/tax/port";
            $lnk .= "$FID" if (!$mv);
            $lnk .= "$FID-$mv" if ($mv);
            $lnk .= "/$PLT\_$secc_id\_$temas_id\_$subtemas_id\_1.$extension";

            my $pag = '1';
            my $tpl_nropag_aux = $tpl_nropag;
            $tpl_nropag_aux =~ s/%%lnk%%/$lnk/;
            $tpl_nropag_aux =~ s/%%cnro_pag%%/$pag/;
            $prevlink =  $tpl_nropag_aux . ' ' . $tpl_separador . ' ';
        }

        # Se procesan las páginas hacia arriba
        $fin = ($nro_pag + $prontus_varglb::TAXPORT_PAGCORTA_MAXPAGS);

        if ($fin >= $nro_paginas_totales) {
            $fin = $nro_paginas_totales;
        } else {
            $fin = $fin - 1;
            my $lnk;

            $lnk = "/$prontus_varglb::PRONTUS_ID/site/tax/port";
            $lnk .= "/$FID" if (!$mv);
            $lnk .= "/$FID-$mv" if ($mv);
            $lnk .= "/$PLT\_$secc_id\_$temas_id\_$subtemas_id\_$nro_paginas_totales.$extension";

            my $pag = $nro_paginas_totales;
            my $tpl_nropag_aux = $tpl_nropag;
            $tpl_nropag_aux =~ s/%%lnk%%/$lnk/;
            $tpl_nropag_aux =~ s/%%cnro_pag%%/$pag/;
            $nextlink =  ' ' . $tpl_separador . ' ' . $tpl_nropag_aux;
        }

    } else {
        $ini = 1;
        $fin = $nro_paginas_totales;
    }

    for (my $pag = $ini; $pag <= $fin; $pag++) {
        my $tpl_nropag_aux;

        if ($pag eq $nro_pag) {
            $tpl_nropag_aux = $tpl_nropag2;
        } else {
            $tpl_nropag_aux = $tpl_nropag;
        }

        my $lnk;

        $lnk = "/$prontus_varglb::PRONTUS_ID/site/tax/port";
        $lnk .= "/$FID" if (!$mv);
        $lnk .= "/$FID-$mv" if ($mv);
        $lnk .= "/$PLT\_$secc_id\_$temas_id\_$subtemas_id\_$pag.$extension";

        $tpl_nropag_aux =~ s/%%lnk%%/$lnk/;
        $tpl_nropag_aux =~ s/%%cnro_pag%%/$pag/;
        $html_nros_pag .= "$tpl_nropag_aux\n";
    }

    $html_nros_pag = $prevlink . $html_nros_pag . $nextlink;

    if ($html_nros_pag ne '') {
        $pagina =~ s/%%_HTML_NROS_PAG%%/ $html_nros_pag /ig;
    } else {
        $pagina =~ s/%%_HTML_NROS_PAG%%//ig;
        $pagina =~ s/%%_msg%%.*?%%\/_msg%%/$MSGS{'no_results'}/is; # 1.8
    }

    return $pagina;
};

sub show_error {
    my $msg = $_[0];

    print "Content-type: text/html\n";
    print "\n<html><head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/></head><body><p><strong>ERROR</strong>: $msg</p></body></html>\n";
    exit;
};
