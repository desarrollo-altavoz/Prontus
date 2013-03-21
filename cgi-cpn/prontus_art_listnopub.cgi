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
# Deriva de ap_art_admin_01.pl (construido para www.mercuriovalpo.cl).

# Generar en base una plantilla (descrita mas abajo) y desplegar en el browser,
# la lista de Administración de Artículos existentes.
# Las principales marcas de campo que se reemplazan en la plantilla son:
# Listado de articulos (cuerpo, sin encabezado, de la tabla),
# Combobox de portadas (solo PRONTUS-04) y Combobox de tipos de articulos (PRONTUS-03 y PRONTUS-04).
#
# Este script se usa solo para PRONTUS-02, PRONTUS-03 y PRONTUS-04.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# No registra en forma directa, pero genera links para :
# - editar articulo --> prontus_art_ficha.pl
# con parametros:
# art=<nombre articulo con extension y s/path>
# Cmb_TIPO=<nombre del template de articulo usado en la creacion, con extension y sin path>
#
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde cualquier parte y con param :
# 1) path_conf = <path relativo a la raiz del sitio del arch. de configuracion de c/instancia del publicador> (p.ej. '/conf-prontus/conf1.cfg')
# 2) port = <nombre del archivo de seccion con extension y sin path, sirve para indicar caraga de los datos de una seccion especifica>
#    Este ultimo parametro es optativo, se usa cuando la pagina se recarga a si misma despues de un submit.
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# prontus_art_admin.html
# ---------------------------------------------------------------

# HISTORIAL DE VERSIONES.
# ---------------------------
# 01 - Viernes 02/06/2000 - Primera Version.
# 1.1 - Jueves 13/07/2000 - Ordenamiento de articulos se realiza ahora de menor a mayor Area/Orden.
# 1.2 - Viernes 18/08/2000 - Se agregan variantes PRONTUS-03NA y PRONTUS-04NA
# 1.3 - 20/09/2000 - soporte para que el script procese correctamente el path relativo al sitio del arch. de configuracion.
# 1.4 - 21/09/2000 - Ordenamiento de articulos ascend. por area/orden y desc. por articulo.
# 1.5 - 21/09/2000 - Re-estructuracion de codigo por encapsulamiento de la generacion de cada fila de la tabla.
# 1.6 - 23/09/2000 - se incluye un espacio junto con la coma al listar las secc. donde esta publicado un articulo.
# 1.7 - 13/10/2000 - Correccion de 1.3 y correccion para que funcione con varias portadas, lo cual quedo mal despues de 1.5
# 1.8 - 23/11/2000 - soporte para articulos shtml
# 1.9 - 06/12/2000 - Modificaciones en la llamada a la rutina que carga y valida el archivo de configuracion del prontus.
# Ademas se oficializa la validacion del referer.
# 1.10 - 24/01/2000 - Modificaciones pro correccion del ordenamiento area-orden al listar los articulos, este error se manifesto en indexlibros y noticias navales.
# 1.11 - 15/05/2001 - Extensiones para Prontus 5. Estas modificaciones se aplicaron antes de escribir este comentario.
# 1.12 - 16/05/2001 - Revision general de detalles de forma.

# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0

# 7.0 - 20/12/2001 - Extensiones p7 :
#   . "- Agrega marca a la portada para que inserte los menús de páginas con subtítulos.<br>"
#     . "- Perfilación de periodistas en lista de artículos para permitir artículos personales<br>"
#     . "- Capacidad para borrar fotos, asocfile y realmedia<br>"
#     . "- Linkeo de URLs https<br>"

# Prontus 8.0 - 23/05/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};


use prontus_varglb;
&prontus_varglb::init();

use glib_html_02;
use glib_fildir_02;
use lib_prontus;
use glib_hrfec_02;

use glib_cgi_04;

use glib_dbi_02;
use DBI;

my ($BD, $RESTAR_ARTICS_PUB, $CURRENT_SPARE, %TABLA_SECC, %TABLA_TEMAS, %TABLA_SUBTEMAS);
#my (%HASH_NOMPORTS);
my (%HASH_ARTIC_PUBS);
# ---------------------------------------------------------------
# MAIN.
# -------------
  # print STDERR "\n" . &get_time('Inicio');


main: {

    # Rescatar parametros recibidos
    &glib_cgi_04::new();


    $FORM{'_orden_lista'} = &glib_cgi_04::param('_orden_lista'); #  'F' (fecha public, default)  / 'T' (titular) / 'C' creacion
    $FORM{'_orden_lista'} = 'C' if ($FORM{'_orden_lista'} !~ /^(F|T|C)$/);


    $FORM{'_edic'} = &glib_cgi_04::param('_edic'); # base
    $FORM{'_port'} = &glib_cgi_04::param('_port'); # portada.html

    $FORM{'_search'} = &glib_cgi_04::param('_search'); # 0/1
    $FORM{'_search'} =~ s/[^01]//g;

    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # filas por pag
    $FORM{'_filas_x_pag'} = &glib_cgi_04::param('_filas_x_pag');
    if ($FORM{'_filas_x_pag'} =~ /^\d+$/) {
        $prontus_varglb::MAX_NRO_ARTIC = $FORM{'_filas_x_pag'};
    };

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL . "<script>window.location.href='/$prontus_varglb::PRONTUS_ID/cpan/core/prontus_index.html';</script>", 1, 'exit=1,ctype=1');
    };

    $FORM{'_rec_ini'} = &glib_cgi_04::param('_rec_ini'); # solo BD
    $FORM{'_rec_ini'} = 0 if $FORM{'_rec_ini'} eq '';    # solo BD

    print "Cache-Control: no-cache\n";
    print "Cache-Control: max-age=0\n";
    print "Cache-Control: no-store\n";

    print "Content-Type: text/html\n\n";

    my $dir_cache = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache";
    my $file_cache = "listnopub_" . $prontus_varglb::USERS_ID . "_$FORM{'_orden_lista'}-$FORM{'_edic'}-$FORM{'_filas_x_pag'}-$FORM{'_rec_ini'}-$FORM{'_port'}";
    $file_cache =~ s/[^\w\-]//g;
    my $path_cache = "$dir_cache/$file_cache.html";
    # print "_search[$FORM{'_search'}]";
    # warn($path_cache);
    if ((-s $path_cache) && (!$FORM{'_search'})) {
        my $buffer_cache = &glib_fildir_02::read_file($path_cache);
        # warn("usando cache");
        print $buffer_cache;
        exit;
    };


    # CVI - 06/02/2012 - Se carga el Hash de Articulos publicados en portadas
    %HASH_ARTIC_PUBS = &lib_prontus::load_artic_pubs();

    # Conectar a BD siempre
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_pag_result("Error",$msg_err_bd,0,'exit=1,,link=nolink');
    };


    my $buffer = &glib_fildir_02::read_file($prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/prontus_art_listnopub.html");
    $buffer = &lib_prontus::set_coreplt_ppal($buffer);

    $buffer =~ /<!--articulo_loop-->(.*)<!--\/articulo_loop-->/is;
    my $loop = $1;

    my ($artics_parsed, $ult_reg, $sql_contar, $ftexto) = &make_lista($loop);

    $buffer =~ s/<!--articulo_loop-->.*<!--\/articulo_loop-->/$artics_parsed/s;

    my $label_paginacion = '';
    # if ($artics_parsed) {
        $label_paginacion = &implementar_anterior_sgte($artics_parsed, $ult_reg, $sql_contar, $ftexto);
    # };
    $buffer =~ s/%%_label_paginacion%%/$label_paginacion/;

    $BD->disconnect;

    $buffer =~ s/%%_orden_lista%%/$FORM{'_orden_lista'}/g;
    $buffer =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/g;
    $buffer =~ s/%%_path_conf%%/$FORM{'_path_conf'}/g;


    if ($prontus_varglb::CONTROL_FECHA ne 'SI') {
        $buffer =~ s/<!--control_fecha-->.*?<!--\/control_fecha-->//sg;
    };

    if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS ne 'SI') {
        $buffer =~ s/<!--alta_col-->.*?<!--\/alta_col-->//sg;
    };

    #~ $buffer =~ s/<!--vobo-->.*?<!--\/vobo-->//sg; # quitar vobo de listado de no publicados, solo aplica a publicados.

    # $buffer = &agrega_valores_filtros($buffer);

    # print STDERR &get_time('Fin');

    $buffer =~ s/<!--\w.*?\w-->//sg;
    $buffer =~ s/<!--\/\w.*?\w-->//sg;
    my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
    $buffer =~ s/>($crlf| )+</>\x0a</sg;
    $buffer =~ s/ +/ /sg;
    $buffer =~ s/($crlf)+/\x0a/sg;

    # CVI - 16/06/2011
    my $open_fid_in_pop = 'open_normally';
    if($prontus_varglb::ABRIR_FIDS_EN_POP eq 'SI') {
        $open_fid_in_pop = 'open_in_pop';
    }
    $buffer =~ s/%%_class_open_fid%%/$open_fid_in_pop/ig;

    # Escribe cache, no cachea busquedas
    if (!$FORM{'_search'}) {
        &glib_fildir_02::check_dir($dir_cache);
        &glib_fildir_02::write_file($path_cache, $buffer);
    };

    print $buffer;

};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub print_date_or_time {
  # Escribe la fecha u hora, dependiendo si la fecha del art. es de hoy o no.
  my ($aaaammdd_art, $hhmmss_art) = @_;
  my $isofec = &glib_hrfec_02::get_date_pack4();

  if ($aaaammdd_art eq $isofec) { # es de hoy
    # Escribe hora (puede venir formateada o no.)
    if ($hhmmss_art =~ /:/) {
      return $hhmmss_art;
    }
    else {
      if ($hhmmss_art =~ /^(\d\d)(\d\d)(\d\d)$/) {
        return $1 . ':' . $2 . ':' . $3;
      }
      else {
        return '';
      };
    };
  }
  else {
    # Escribe fecha

    if ($aaaammdd_art =~ /^(\d\d\d\d)(\d\d)(\d\d)$/) {
      return $3 . '/' . $2 . '/' . $1;
    }
    else {
      return '';
    };

  };
};


# ---------------------------------------------------------------
sub salir {
  my $msg = $_[0];
  # print "Content-Type: text/html\n\n";
  print $msg;
  exit;
};
# ---------------------------------------------------------------
sub implementar_anterior_sgte {

    my ($artics_parsed) = $_[0];
    my ($ult_reg) = $_[1];
    my ($sql) = $_[2];
    my ($ftexto) = $_[3];

    my ($result, $href, $sgte, $anter, $prev_ini, $ant_sig, $salida, $tot_reg);
    my ($from_ultpag, $href_ultpag, $ultpag);
    my ($from_firstpag, $href_firstpag, $firstpag);

    if ($artics_parsed) {
        $sql =~ s/select .* from /select count(ART_ID) from /;
        $sql =~ s/limit .+$//i;
        # print "<br>sql_contar[$sql]"; # debug

        $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($tot_reg));
        $salida->fetch;
        $salida->finish;
    };

    $tot_reg = '0' if ($tot_reg <= 0);
    # print STDERR "tot_reg[$tot_reg]\n";

    if ($ult_reg == $prontus_varglb::MAX_NRO_ARTIC) {
        $ult_reg = $FORM{'_rec_ini'} + $prontus_varglb::MAX_NRO_ARTIC;
    }
    else {
        $ult_reg = $tot_reg;
    };

    $FORM{'_rec_ini'}++;



    if ($tot_reg > $ult_reg) { # habilitar link siguiente

        $sgte = "<a href=\"#\" onclick=\"Listartic.nextpag('$ult_reg'); return false;\">Siguiente &rsaquo;&nbsp;</a>";

        $from_ultpag = $tot_reg - ($tot_reg % $prontus_varglb::MAX_NRO_ARTIC);

        $from_ultpag -= $prontus_varglb::MAX_NRO_ARTIC if ($tot_reg % $prontus_varglb::MAX_NRO_ARTIC) == 0;

        $ultpag = "<a href=\"#\" onclick=\"Listartic.ultpag('$from_ultpag'); return false;\">&Uacute;ltima P&aacute;gina &raquo;</a>";
    }
    else { # deshabilitarlo
        $sgte =  "";
    };

    if ($FORM{'_rec_ini'} > $prontus_varglb::MAX_NRO_ARTIC) { # habilitar link anterior

        $prev_ini = ($FORM{'_rec_ini'} - 1) - $prontus_varglb::MAX_NRO_ARTIC;
        $anter = "<a href=\"#\" onclick=\"Listartic.prevpag('$prev_ini'); return false;\"> &nbsp;&lsaquo; Anterior</a>";
        $from_firstpag = 0;
        $firstpag = "<a href=\"#\" onclick=\"Listartic.firstpag('$from_firstpag'); return false;\">&laquo; Primera P&aacute;gina</a>";

    }
    else { # deshabilitarlo.
        $anter =  "";
    };

    if ($tot_reg == 0) {
        $result = '&nbsp;';
    }
    else {

        $result = "<b>$FORM{'_rec_ini'}</b> a <b>$ult_reg</b> de <b>$tot_reg</b>"; # No hay para que informar cuantos encontro.
    };

    if (($anter ne  "") or ($sgte ne  "")) {
        my $separador = '';
        $separador = '&nbsp; | &nbsp;' if ($anter && $sgte);
        $ant_sig = "$firstpag $anter $separador $sgte $ultpag";
    }
    else {
        $ant_sig ='';
    };

    $tot_reg = '0' if ($tot_reg eq '');

    my ($plural, $plural_n) = '';
    $plural = 's' if $tot_reg > 1;
    $plural_n = 'n' if $tot_reg > 1;


    my $label_tablanopub;
    if ($FORM{'_search'}) {
        $label_tablanopub = "\nSu b&uacute;squeda entreg&oacute; <b>$tot_reg</b> art&iacute;culo$plural "
                          . "que cumple$plural_n con los siguentes atributos:<br/> $ftexto";
    }
    else {
        $label_tablanopub = "\n&Uacute;ltimos Art&iacute;culos Ingresados. $ftexto";
    };
    $label_tablanopub .= '<br/>' . $result . '&nbsp;' x 20 . $ant_sig;


    return $label_tablanopub;

};

# ---------------------------------------------------------------
#sub agrega_valores_filtros {
#  my ($buf) = $_[0];
#
#  $buf =~ s/%%nom_alta%%/$FORM{'nom_alta'}/sig;
#  $buf =~ s/%%alta%%/$FORM{'alta'}/sig;
#
#  $buf =~ s/%%tipart%%/$FORM{'tipart'}/si;
#
#  $buf =~ s/%%seccion%%/$FORM{'seccion'}/si;
#  $buf =~ s/%%tema%%/$FORM{'tema'}/si;
#  $buf =~ s/%%subtema%%/$FORM{'subtema'}/si;
#
#  $buf =~ s/%%nom_tipart%%/$FORM{'nom_tipart'}/sig;
#  $buf =~ s/%%nom_seccion%%/$FORM{'nom_seccion'}/sig;
#  $buf =~ s/%%nom_tema%%/$FORM{'nom_tema'}/sig;
#  $buf =~ s/%%nom_subtema%%/$FORM{'nom_subtema'}/sig;
#
#
#  $buf =~ s/%%autor%%/$FORM{'autor'}/sig;
#  $buf =~ s/%%titu%%/$FORM{'titu'}/sig;
#  $buf =~ s/%%baja%%/$FORM{'baja'}/sig;
#  my $fec_desnorm;
#  $fec_desnorm = &glib_hrfec_02::des_normaliza_fecha($FORM{'dia'}) if ($FORM{'dia'} ne '');
#  $buf =~ s/%%dia%%/$fec_desnorm/sig;
#
#  $fec_desnorm = '';
#  $fec_desnorm = &glib_hrfec_02::des_normaliza_fecha($FORM{'diapub'}) if ($FORM{'diapub'} ne '');
#  $buf =~ s/%%diapub%%/$fec_desnorm/sig;
#
#  $fec_desnorm = '';
#  $fec_desnorm = &glib_hrfec_02::des_normaliza_fecha($FORM{'diaexp'}) if ($FORM{'diaexp'} ne '');
#  $buf =~ s/%%diaexp%%/$fec_desnorm/sig;
#
#
#  $buf =~ s/%%autoinc%%/$FORM{'autoinc'}/sig;
#
#  return $buf;
#};

# ---------------------------------------------------------------
sub make_lista {
# Genera lista de artic. by megalupa, con BD
    my $artic_loop = shift;

    # Carga la tabla de secciones de una sola vez.
    &carga_tabla_secc();
    &carga_tabla_temas();
    &carga_tabla_subtemas();

    #  'F' (fecha public, default)  / 'T' (titular)
    my $orderby;
    $orderby = ' order by ART_FECHAPHORAP desc' if ($FORM{'_orden_lista'} eq 'F');
    $orderby = ' order by ART_TITU asc' if ($FORM{'_orden_lista'} eq 'T');
    $orderby = ' order by ART_AUTOINC desc' if ($FORM{'_orden_lista'} eq 'C');

    my $sql = "select ART_ID, ART_IDSECC1, ART_IDTEMAS1, ART_IDSUBTEMAS1, ART_DIRFECHA, ART_TITU, ART_EXTENSION, ART_AUTOINC, ART_TIPOFICHA, ART_ALTA, ART_IDUSR, ART_FECHAP, ART_HORAP, ART_FECHAE, ART_HORAE "
            . "from ART  "
            . "%%FILTRO%% $orderby LIMIT $FORM{'_rec_ini'}, $prontus_varglb::MAX_NRO_ARTIC";

    my ($filtros, $ftexto) = &genera_filtros();
    if ($filtros ne '') {
        $sql =~ s/%%FILTRO%%/ where $filtros /;
    }
    else {
        $sql =~ s/%%FILTRO%%//;
    };

    print STDERR "sql filtro[$sql]\n\n";
    my ($art_id, $art_dirfecha, $art_tit, $art_seccion, $art_tema, $art_subtema, $art_extension, $art_autoinc, $art_tipoficha, $art_idsecc1, $art_idtemas1, $art_idsubtemas1, $art_alta, $art_idusr, $art_fechap, $art_horap, $art_fechae, $art_horae);
    my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($art_id, $art_idsecc1, $art_idtemas1, $art_idsubtemas1, $art_dirfecha, $art_tit, $art_extension, $art_autoinc, $art_tipoficha, $art_alta, $art_idusr, $art_fechap, $art_horap, $art_fechae, $art_horae));
    my $nro_filas = 0;

    my $artics_parsed;
    while (($salida->fetch) && ($lineas < $prontus_varglb::MAX_NRO_ARTIC)) {
        $art_seccion = $TABLA_SECC{$art_idsecc1};
        $art_tema = $TABLA_TEMAS{$art_idtemas1};
        $art_subtema = $TABLA_SUBTEMAS{$art_idsubtemas1};
        $nro_filas++;

        my $ts_art_ext = $art_id . '.' . $art_extension;
        $path_artic = $prontus_varglb::DIR_SERVER .
        $prontus_varglb::DIR_CONTENIDO .
        $prontus_varglb::DIR_ARTIC . '/' .
        $art_dirfecha .
        $prontus_varglb::DIR_PAG . '/' .
        $ts_art_ext;

        $artics_parsed .= &get_artic_parsed($artic_loop, $path_artic, $art_id, $ts_art_ext, $art_tit, $art_tipoficha, $art_seccion, $art_tema, $art_subtema, $art_alta, $art_fechap, $art_horap, $art_fechae, $art_horae, $art_idusr, $art_autoinc);
        $lineas++;
    };
    $salida->finish;

    return ($artics_parsed, $nro_filas, $sql, $ftexto);

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

# ---------------------------------------------------------------
sub genera_filtros {
  my ($filtros, $filtros_texto, $sql, $salida, $nom, $tablas);

  $FORM{'tipart'} = &glib_cgi_04::param('tipart');
  $FORM{'seccion'} = &glib_cgi_04::param('seccion');
  $FORM{'tema'} = &glib_cgi_04::param('tema');
  $FORM{'subtema'} = &glib_cgi_04::param('subtema');
  $FORM{'autor'} = &glib_cgi_04::param('autor');
  $FORM{'titu'} = &glib_cgi_04::param('titu');

  $FORM{'baja'} = lc &glib_cgi_04::param('baja');
  $FORM{'dia'} = lc &glib_cgi_04::param('dia');
  $FORM{'dia'} = &glib_hrfec_02::normaliza_fecha($FORM{'dia'}) if ($FORM{'dia'} ne '');
  $FORM{'autoinc'} = &glib_cgi_04::param('autoinc');
  $FORM{'diapub'} = lc &glib_cgi_04::param('diapub');
  $FORM{'diapub'} = &glib_hrfec_02::normaliza_fecha($FORM{'diapub'}) if ($FORM{'diapub'} ne '');

  $FORM{'diaexp'} = lc &glib_cgi_04::param('diaexp');
  $FORM{'diaexp'} = &glib_hrfec_02::normaliza_fecha($FORM{'diaexp'}) if ($FORM{'diaexp'} ne '');


  $FORM{'nom_tipart'} = &glib_cgi_04::param('nom_tipart');
  $FORM{'nom_seccion'} = &glib_cgi_04::param('nom_seccion');
  $FORM{'nom_tema'} = &glib_cgi_04::param('nom_tema');
  $FORM{'nom_subtema'} = &glib_cgi_04::param('nom_subtema');

  $FORM{'nom_alta'} = &glib_cgi_04::param('nom_alta');
  $FORM{'alta'} = &glib_cgi_04::param('alta');

  $FORM{'ts'} = &glib_cgi_04::param('ts');

  $FORM{'autor'} =~ s/\"/\'/sig;
  #~ $FORM{'titu'} =~ s/\"/\'/sig ($FORM{'titu'} =~ /".*?"/);
  $FORM{'titu'} =~ s/'/\\'/sig;
  $FORM{'baja'} =~ s/\"/\'/sig;

  if ($FORM{'autoinc'} ne '') {
    $filtros .= " ART_AUTOINC = $FORM{'autoinc'}";
    $filtros_texto = "<b>C&oacute;digo:</b> $FORM{'autoinc'}";

  }
  else {

    if ($FORM{'tipart'}) { # Distinto de todos.
      $filtros .= " and ART_TIPOFICHA = \"$FORM{'tipart'}\"" if $filtros ne '';
      $filtros = "ART_TIPOFICHA = \"$FORM{'tipart'}\"" if $filtros eq '';
      $filtros_texto .= "<b>Tipo artic:</b> $FORM{'nom_tipart'}" if $filtros_texto eq '';
    };

    if ($FORM{'seccion'} eq 'SS') { # Los sin seccion
      my $esc_value = &lib_prontus::escape_html($FORM{'nom_seccion'});
      $filtros .= " and " if $filtros ne '';
      $filtros .= "(ART_IDSECC1 = \"0\" or ART_IDSECC2 = \"0\" or ART_IDSECC3 = \"0\")";
      $filtros_texto .= " | <b>Secci&oacute;n:</b> $esc_value" if $filtros_texto ne '';
      $filtros_texto .= "<b>Secci&oacute;n:</b> $esc_value" if $filtros_texto eq '';
    };

    if (($FORM{'seccion'} =~ /^\d+$/) && ($FORM{'seccion'} > 0)) { # Distinto de todos.
      my $esc_value = &lib_prontus::escape_html($FORM{'nom_seccion'});
      $filtros .= " and " if $filtros ne '';
      $filtros .= "(ART_IDSECC1 = \"$FORM{'seccion'}\" or ART_IDSECC2 = \"$FORM{'seccion'}\" or ART_IDSECC3 = \"$FORM{'seccion'}\")";
      $filtros_texto .= " | <b>Secci&oacute;n:</b> $esc_value" if $filtros_texto ne '';
      $filtros_texto .= "<b>Secci&oacute;n:</b> $esc_value" if $filtros_texto eq '';
    };

    if ($FORM{'tema'}) { # Distinto de todos.
      my $esc_value = &lib_prontus::escape_html($FORM{'nom_tema'});
      $filtros .= " and " if $filtros ne '';
      $filtros .= "(ART_IDTEMAS1 = \"$FORM{'tema'}\" or ART_IDTEMAS2 = \"$FORM{'tema'}\" or ART_IDTEMAS3 = \"$FORM{'tema'}\")";
      $filtros_texto .= " | <b>Tema:</b> $esc_value" if $filtros_texto ne '';
      $filtros_texto = "<b>Tema:</b> $esc_value" if $filtros_texto eq '';
    };

    if ($FORM{'subtema'}) { # Distinto de todos.
      my $esc_value = &lib_prontus::escape_html($FORM{'nom_subtema'});
      $filtros .= " and " if $filtros ne '';
      $filtros .= "(ART_IDSUBTEMAS1 = \"$FORM{'subtema'}\" or ART_IDSUBTEMAS2 = \"$FORM{'subtema'}\" or ART_IDSUBTEMAS3 = \"$FORM{'subtema'}\")";
      $filtros_texto .= " | <b>Subtema:</b> $esc_value" if $filtros_texto ne '';
      $filtros_texto = "<b>Subtema:</b> $esc_value" if $filtros_texto eq '';
    };


    $FORM{'autor'} =~ s/\+//g;
    $FORM{'autor'} =~ s/^ +//g;
    $FORM{'autor'} =~ s/ +$//g;
    $FORM{'autor'} =~ s/ {2,}/ /g;
    if ($FORM{'autor'} ne '') {
      my $autor4query = $FORM{'autor'};

      if ($prontus_varglb::MOTOR_BD eq 'MYSQL') {
        $autor4query =~ s/ / \+/g; # mysql
        $autor4query =~ s/^/+/;    # mysql
        $filtros .= " and MATCH (ART_AUTOR) AGAINST (\"$autor4query\")" if $filtros ne ''; # mysql
        $filtros = " MATCH (ART_AUTOR) AGAINST (\"$autor4query\")" if $filtros eq '';      # mysql
      };

      if ($prontus_varglb::MOTOR_BD eq 'PRONTUS') {
        $filtros .= " and ART_AUTOR like (\"%$autor4query%\")" if $filtros ne ''; # sqlite
        $filtros = " ART_AUTOR like (\"%$autor4query%\")" if $filtros eq '';      # sqlite
      };

      my $esc_value = &lib_prontus::escape_html($FORM{'autor'});
      $filtros_texto .= " | <b>Autor:</b> $esc_value" if $filtros_texto ne '';
      $filtros_texto = "<b>Autor:</b> $esc_value" if $filtros_texto eq '';
    };

    $FORM{'titu'} =~ s/\+//g;
    $FORM{'titu'} =~ s/^ +//g;
    $FORM{'titu'} =~ s/ +$//g;
    $FORM{'titu'} =~ s/ {2,}/ /g;
    if ($FORM{'titu'} ne '') {
      my $titu4query = $FORM{'titu'};

      if ($prontus_varglb::MOTOR_BD eq 'MYSQL') {
        if($titu4query =~ /".*?"/) {
            $filtros .= " and MATCH (ART_TITU) AGAINST ('$titu4query' IN BOOLEAN MODE)" if $filtros ne ''; # mysql
            $filtros = " MATCH (ART_TITU) AGAINST ('$titu4query' IN BOOLEAN MODE)" if $filtros eq '';      # mysql

        } else {
            $titu4query =~ s/ / \+/g;  # mysql
            $titu4query =~ s/^/+/;     # mysql
            $filtros .= " and MATCH (ART_TITU) AGAINST (\"$titu4query\" IN BOOLEAN MODE)" if $filtros ne ''; # mysql
            $filtros = " MATCH (ART_TITU) AGAINST (\"$titu4query\" IN BOOLEAN MODE)" if $filtros eq '';      # mysql
        };
      };


      if ($prontus_varglb::MOTOR_BD eq 'PRONTUS') {
        $filtros .= " and ART_TITU like (\"%$titu4query%\")" if $filtros ne ''; # sqlite
        $filtros = " ART_TITU like (\"%$titu4query%\")" if $filtros eq '';      # sqlite
      };
      my $esc_value = &lib_prontus::escape_html($FORM{'titu'});
      $esc_value =~ s/\\//sig;
      $filtros_texto .= " | <b>Titular:</b> $esc_value" if $filtros_texto ne '';
      $filtros_texto = "<b>Titular:</b> $esc_value" if $filtros_texto eq '';
    };


    $FORM{'baja'} =~ s/\+//g;
    $FORM{'baja'} =~ s/^ +//g;
    $FORM{'baja'} =~ s/ +$//g;
    $FORM{'baja'} =~ s/ {2,}/ /g;
    if ($FORM{'baja'} ne '') {
      my $baja4query = $FORM{'baja'};

      if ($prontus_varglb::MOTOR_BD eq 'MYSQL') {
        $baja4query =~ s/ / \+/g; # mysql
        $baja4query =~ s/^/+/;    # mysql
        $filtros .= " and MATCH (ART_BAJA) AGAINST (\"$baja4query\")" if $filtros ne ''; # mysql
        $filtros = " MATCH (ART_BAJA) AGAINST (\"$baja4query\")" if $filtros eq '';      # mysql
      };

      if ($prontus_varglb::MOTOR_BD eq 'PRONTUS') {
        $filtros .= " and ART_BAJA like (\"%$baja4query%\")" if $filtros ne ''; # sqlite
        $filtros = " ART_BAJA like (\"%$baja4query%\")" if $filtros eq '';      # sqlite
      };

      my $esc_value = &lib_prontus::escape_html($FORM{'baja'});
      $filtros_texto .= " | <b>Bajada:</b> $esc_value" if $filtros_texto ne '';
      $filtros_texto = "<b>Bajada:</b> $esc_value" if $filtros_texto eq '';
    };

    if ($FORM{'dia'} ne '') {
      $filtros .= " and ART_DIRFECHA = \"$FORM{'dia'}\"" if $filtros ne '';
      $filtros = "ART_DIRFECHA = \"$FORM{'dia'}\"" if $filtros eq '';
      my $dia_desnorm = &glib_hrfec_02::des_normaliza_fecha($FORM{'dia'});
      $filtros_texto .= " | <b>Fec. creaci&oacute;n:</b> $dia_desnorm" if $filtros_texto ne '';
      $filtros_texto = "<b>Fec. creaci&oacute;n:</b> $dia_desnorm" if $filtros_texto eq '';
    };

    if ($FORM{'diapub'} ne '') {
      $filtros .= " and ART_FECHAP = \"$FORM{'diapub'}\"" if $filtros ne '';
      $filtros = "ART_FECHAP = \"$FORM{'diapub'}\"" if $filtros eq '';
      my $dia_desnorm = &glib_hrfec_02::des_normaliza_fecha($FORM{'diapub'});
      $filtros_texto .= " | <b>Fec. publicaci&oacute;n:</b> $dia_desnorm" if $filtros_texto ne '';
      $filtros_texto = "<b>Fec. publicaci&oacute;n:</b> $dia_desnorm" if $filtros_texto eq '';
    };

    if ($FORM{'diaexp'} ne '') {
      $filtros .= " and ART_FECHAE = \"$FORM{'diaexp'}\"" if $filtros ne '';
      $filtros = "ART_FECHAE = \"$FORM{'diaexp'}\"" if $filtros eq '';
      my $dia_desnorm = &glib_hrfec_02::des_normaliza_fecha($FORM{'diaexp'});
      $filtros_texto .= " | <b>Fec. expiraci&oacute;n:</b> $dia_desnorm" if $filtros_texto ne '';
      $filtros_texto = "<b>Fec. expiraci&oacute;n:</b> $dia_desnorm" if $filtros_texto eq '';
    };

    if ($FORM{'alta'} ne '') { # Distinto de todos.
      my $alta_value = $FORM{'alta'};
      $alta_value = '' if ($alta_value eq '0'); # Cuando se niega el alta, queda con '' y no con '0'
      $filtros .= " and ART_ALTA = \"$alta_value\"" if $filtros ne '';
      $filtros = "ART_ALTA = \"$alta_value\"" if $filtros eq '';
      $filtros_texto .= " | <b>Alta:</b> $FORM{'nom_alta'}" if $filtros_texto ne '';
      $filtros_texto = "<b>Alta:</b> $FORM{'nom_alta'}" if $filtros_texto eq '';
    };

    # CVI - para busqueda rápida por TS
    if ($FORM{'ts'} ne '') {
      $filtros .= " and ART_ID = \"$FORM{'ts'}\"" if $filtros ne '';
      $filtros = "ART_ID = \"$FORM{'ts'}\"" if $filtros eq '';
      $filtros_texto .= " | <b>Timestamp:</b> $FORM{'ts'}" if $filtros_texto ne '';
      $filtros_texto = "<b>Timestamp:</b> $FORM{'ts'}" if $filtros_texto eq '';
    };

    # OCULTAR ARTICS AJENOS AUTOMATICAMENTE
    if ( (($prontus_varglb::PERIODISTA_VER_ARTICULOS_AJENOS ne 'SI') and ($prontus_varglb::USERS_PERFIL eq 'P'))
       or (($prontus_varglb::EDITOR_VER_ARTICULOS_AJENOS ne 'SI') and ($prontus_varglb::USERS_PERFIL eq 'E')) ) {

      $filtros .= " and ART_IDUSR = \"$prontus_varglb::USERS_ID\"" if $filtros ne '';
      $filtros = "ART_IDUSR = \"$prontus_varglb::USERS_ID\"" if $filtros eq '';
      $filtros_texto .= " | <b>S&oacute;lo art&iacute;culos propios.</b>" if $filtros_texto ne '';
      $filtros_texto = "<b>S&oacute;lo art&iacute;culos propios.</b>" if $filtros_texto eq '';
    };
  };


  # -----------------------

  if ($filtros_texto eq '') {
    $filtros_texto = '&nbsp;Sin filtros';
  } else {
    my $imgDel = '<img src="/'.$prontus_varglb::PRONTUS_ID.'/cpan/core/imag/boto/delete10x10px.png" width="10" height="10" alt="Eliminar Filtros" />';
    $filtros_texto .= '&nbsp;&nbsp;&nbsp;<a href="#" onclick="Buscador.limpiaFiltros(); return false;" class="elim-filtros">['.$imgDel.' Eliminar filtros]</a>';
  };




  return ($filtros, $filtros_texto);
}; # genera_filtros.





#-------------------------------------------------------------------------#
sub get_time {
  my $label = $_[0];
  my $dt = &glib_hrfec_02::get_dtime_pack4();
  $dt =~ /(\d{2})(\d{2})(\d{2})$/;
  return "\nHora $label [$1:$2:$3]";

};

#--------------------------------------------------------------------#
sub normaliza_fecha_plus {
# Toma una fecha escrita como dia/mes/ano, la normaliza y la entrega
# compactada en formato ISO.

# Param : string con la fecha a normalizar.

# Retorna : "$ano$mes$dia"
  my ($input) = $_[0];
  my($dia,$mes,$ano);

  if ($input =~ /^\d{1,2}(\-|\/)\d{1,2}(\-|\/)\d{4}$/) {
    $input =~ s/\-/\//g;
    ($dia,$mes,$ano) = split (/\//,$input);

    $mes = &glib_str_02::format_n($mes,2);
    $dia = &glib_str_02::format_n($dia,2);
    return "$ano$mes$dia";
  }
  elsif ($input =~ /^\d{1,2}(\-|\/)\d{4}$/) {
    $input =~ s/\-/\//g;
    ($mes,$ano) = split (/\//,$input);

    $mes = &glib_str_02::format_n($mes,2);

    return "$ano$mes";
  }
  elsif ($input =~ /^\d{4}$/) {
    $ano = $input;


    return "$ano";
  }
  else {
    return '';
  };

};

#--------------------------------------------------------------------#
sub des_normaliza_fecha_plus {
# Toma una fecha en formato ISO y la escribe como dia/mes/ano.

# Param : string con la fecha a des-normalizar.

# Retorna : "$dia/$mes/$ano"

  my($fecha) = $_[0];
  my($dia,$mes,$ano);
  if ($fecha =~ /^(\d\d\d\d)(\d\d)(\d\d)$/) {
    ($dia,$mes,$ano) = ($3,$2,$1);
    return "Fecha: $dia/$mes/$ano";
  }
  elsif ($fecha =~ /^(\d\d\d\d)(\d\d)$/) {
    ($mes,$ano) = ($2,$1);
    return "Mes: $mes/$ano";
  }
  elsif ($fecha =~ /^(\d\d\d\d)$/) {
    return "Año: $1";
  }
  else {
    return '';
  };

};








# ---------------------------------------------------------------
sub generar_hash_articulos_pub {
# Cargar en un hash de registros la lista total de articulos de la portada

# Obs : Cada archivo de seccion almacena en su pagina html la lista de articulos (con sus areas y prioridades)
# que estan publicados en ella. Cada articulo esta representado por una linea de la forma
#      <rowartic>
#        <dir></dir>
#        <file></file>
#        <area></area>
#        <ord></ord>
#        <pub></pub>
#      </rowartic>

    my ($path_port) = $_[0];

    # Deduce del path completo de la portada, el del xml.
    my ($path_xml) = $path_port;
    $path_xml =~ s/\/port\/(\w+?)\.\w*$/\/xml\/\1\.xml/;

    if (-f $path_xml) {

        my $text_port = &read_file_ref($path_xml);
        # Rescatar la info de c/artic de la seccion
        while ($$text_port =~ /<rowartic>[ \n]*?<dir>(\d+?)<\/dir>[ \n]*?<file>(.*?)<\/file>[ \n]*?<area>(\d*?)<\/area>[ \n]*?<ord>(\d*?)<\/ord>[ \n]*?(<vb>(\w*?)<\/vb>)?[ \n]*?<?i?n?>?([\w\/\-]*?)<?\/?i?n?>?[ \n]*?<?o?u?t?>?([\w\/\-]*?)<?\/?o?u?t?>?[ \n]*?<?p?u?b?>?(\d?)<?\/?p?u?b?>?[ \n]*?<\/rowartic>/isg) {

            my ($dirfecha,$art,$area,$prio,$ext_art,$pub, $vb) = '';
            ($dirfecha,$art,$area,$prio,$vb,$pub) = ($1,$2,$3,$4,$6,$9);

            if ($art =~ /(\.\w+$)/) { # obt. extension con punto # 8.0
                $ext_art = $1;
            };
            $art =~ s/\.\w+$//; # saca ext. # 1.4 # 8.0


            if ($vb ne 'S') { $vb = '';}; # 1.11
            $HASH_VB{$art} = $vb; # 1.11 # Visto bueno. # S | N

            $HASH_ORDEN{$art} = $prio; # 1.4
            $HASH_AREA{$art} = $area; # 1.4
            $HASH_DIRFECHA{$art} = $dirfecha; # aaaammdd Dir. corresp. al dia donde se ubica el articulo.
            $HASH_EXT{$art} = $ext_art; # Extension con punto del archivo
            $HASH_PUB{$art} = $pub; # Indicador de si el art. esta o no publicado en el html

            # $HASH_ARTICULOS{$art . $ext_art . '__' . $HASH_NOMPORTS{$entry}} = $area . '_' . $prio; #1.4

        }# while
    }# if

};# sub




#-----------------------------------------------------------------------#
sub lee_dir {
# Lee un directorio y entrega la lista ordenada de entries en bruto.

# Param. de entrada :
# 0) Path real del directorio.

# Retorna : Arreglo ordenado de entradas en bruto del directorio.

  my($eldir) = $_[0];
  # Abre directorio.
  opendir(DIR, $eldir) || die "Can't opendir" . $eldir . $!;
  my @entries = readdir(DIR);
  closedir DIR;
  # Ordena entries alfabeticamente.
  # @entries = sort @entries;
  return @entries;
};



# ---------------------------------------------------------------
sub get_lisdir_artic {
# Mete lista de archivos sin extension a un arreglo y lo deja listo para ordenar.
  my ($lisdir, $full_dir_artic) = @_;
  my ($nom_archivo, $extension, @archivos_sorted);
    foreach $nom_archivo (@$lisdir) {
        # Si se trata de un articulo valido
        if (($nom_archivo =~ /^\d{14}\.\w+$/) and (-s "$full_dir_artic/$nom_archivo") and (! -d "$full_dir_artic/$nom_archivo")) {

            # obt. extension con punto
      $nom_archivo =~ /(\.\w+$)/;
      $extension = $1;

      # saca ext.
      $nom_archivo =~ s/\.\w+$//;
      push @archivos_sorted, $nom_archivo;

      # Extension con punto del archivo
      $HASH_EXT_NOPUBS{$nom_archivo} = $extension;

    };
  };
  return @archivos_sorted;
};




# ---------------------------------------------------------------
sub get_artic_parsed {
    # 1.5
    # Genera html correspondiente a un articulo de la lista.

    my ($loop_art_tpl, $path_artic, $ts, $ts_art_ext, $titulo, $fid, $nom_seccion, $nom_tema, $nom_subtema, $alta, $art_fechap, $art_horap, $art_fechae, $art_horae, $users_id, $art_autoinc) = @_;

    my $nom_seccion_orig = $nom_seccion;
    # $titulo = &lib_prontus::escape_html($titulo);
    $nom_seccion = &lib_prontus::escape_html($nom_seccion);

    # Art. inexistente
    if (! -f $path_artic) {
        $loop_art_tpl =~ s/%%_ts%%/$ts/g;
        $loop_art_tpl =~ s/%%_artic_sin_file%%/_artic_sin_file/g;
        $loop_art_tpl =~ s/%%_vobo_class_name%%/vobo_disabled/g;
        $loop_art_tpl =~ s/%%\w+?%%//g;
        return $loop_art_tpl;
    };
    $loop_art_tpl =~ s/%%_artic_sin_file%%//g;


    # Obtiene st de publicacion
    my $st_pub;
    if (exists $HASH_ORDEN{$ts}) {
        # warn "pub[$art_id]\n";
        $st_pub = $HASH_PUB{$ts};
    }
    else {
        $st_pub = &get_potencialpub($alta, $art_fechap, $art_horap, $art_fechae, $art_horae); # status de public. potencial del artic
    };

    if ($st_pub) {
        $st_pub = 'pub';
    } else {
        $st_pub = 'nopub';
    };

    $loop_art_tpl =~ s/%%_status_pub%%/$st_pub/g;

    # vobo.
    $loop_art_tpl =~ s/%%_status_vobo%%/No publicar en esta portada/g;
    $loop_art_tpl =~ s/%%_vobo_st_img%%/pub/g;
    $loop_art_tpl =~ s/%%_vobo_class_name%%/vobo_disabled/g;
    $loop_art_tpl =~ s/%%_voboboto_class_name%%/voboboto_disabled/g;

    # print STDERR "titulo[$titulo]\n";


    # Datos derivados
    my $dir_fecha = &lib_prontus::get_dirfecha_by_ts($ts);
    my $marca_file = &lib_prontus::remove_front_string($path_artic, $prontus_varglb::DIR_SERVER);
    my $glosa_tipo_ficha = &get_glosa_tipo_ficha($fid);

    $loop_art_tpl =~ s/%%_ts%%/$ts/g;
    $loop_art_tpl =~ s/%%_ts_ext%%/$ts_art_ext/g;
    $loop_art_tpl =~ s/%%_fid%%/$fid/g;

    # CVI - 06/02/2012 - Para indicar si el artículo posee fotos o no
    if(&lib_prontus::check_fotos_from_ts($ts)) {
        $loop_art_tpl =~ s/%%_con_foto%%/$prontus_varglb::FOTOS_ARTIC_SI_IMG/g;
        $loop_art_tpl =~ s/%%_con_foto_texto%%/El art&iacute;culo tiene fotos/g;
    } else {
        $loop_art_tpl =~ s/%%_con_foto%%/$prontus_varglb::FOTOS_ARTIC_NO_IMG/g;
        $loop_art_tpl =~ s/%%_con_foto_texto%%/El art&iacute;culo no posee fotos/g;
    }

    # CVI - 06/02/2012 - Para indicar en cuantas portadas se encuentra publicado el articulo
    my $portadas = &lib_prontus::check_artic_pub($ts, \%HASH_ARTIC_PUBS);
    if($portadas) {
        $loop_art_tpl =~ s/%%_artic_pub%%/$prontus_varglb::ARTIC_PUB_SI_IMG/g;
        $loop_art_tpl =~ s/%%_artic_pub_texto%%/El art&iacute;culo est&aacute; publicado/g;
        $loop_art_tpl =~ s/%%_artic_pub_resumen%%/$portadas/g;
    } else {
        $loop_art_tpl =~ s/%%_artic_pub%%/$prontus_varglb::ARTIC_PUB_NO_IMG/g;
        $loop_art_tpl =~ s/%%_artic_pub_texto%%/El art&iacute;culo no est&aacute; publicado/g;
        $loop_art_tpl =~ s/%%_artic_pub_resumen%%/El art&iacute;culo no est&aacute; publicado/g;
    }

    # CVI - 29/03/2011 - Para habilitar las friendly urls en el admin de comentarios
    if ($prontus_varglb::FRIENDLY_URLS eq 'SI') {
      $marca_file = &lib_prontus::parse_filef('%%_FILEURL%%', $titulo, $ts, $prontus_varglb::PRONTUS_ID, $marca_file, $nom_seccion_orig, $nom_tema, $nom_subtema);
    }
    $loop_art_tpl =~ s/%%_file%%/$marca_file/g;
    $loop_art_tpl =~ s/%%_autoinc%%/$art_autoinc/g;

    $titulo = &lib_prontus::get_minitext_value($titulo);
    $titulo = &lib_prontus::escape_xml($titulo);

    $loop_art_tpl =~ s/%%_titular%%/$titulo/g;
    if ($nom_seccion) {
        $nom_seccion = "<b>Secci&oacute;n: </b> $nom_seccion";
    } else {
        $nom_seccion = "Sin Secci&oacute;n";
    };
    $loop_art_tpl =~ s/%%_nom_seccion%%/$nom_seccion/g;
    $loop_art_tpl =~ s/%%_labelfid%%/$glosa_tipo_ficha/g;

    my $in_curr_port = 0;
    if (exists $HASH_ORDEN{$ts}) {
        $in_curr_port = 1;
    };
    $loop_art_tpl =~ s/%%_in_curr_port%%/$in_curr_port/g;

    # Ocultamiento de articulos ajenos.
    my $ocultar_ajeno = 0;
    if ( (($prontus_varglb::PERIODISTA_VER_ARTICULOS_AJENOS ne 'SI') and ($prontus_varglb::USERS_PERFIL eq 'P'))
        or (($prontus_varglb::EDITOR_VER_ARTICULOS_AJENOS ne 'SI') and ($prontus_varglb::USERS_PERFIL eq 'E')) ) {
        if ($users_id ne $prontus_varglb::USERS_ID) { # si el art. es ajeno
            $ocultar_ajeno = 1;
        };
    };
    $loop_art_tpl =~ s/%%_ocultar%%/$ocultar_ajeno/g;



    # Ver si el usuario conectado tiene asignado el FID de este articulo
    my $art_forbidden = 1; # prohibido
    if ( ($prontus_varglb::USERS_PERFIL eq 'P') or ($prontus_varglb::USERS_PERFIL eq 'E') ) { # Periodista o Editor
        foreach my $key2 (keys %prontus_varglb::ARTUSERS) {
            my ($tipart, $usr) = split /\|/, $key2;
            # print STDERR "tipart[$tipart] - tipo_ficha[$fid]\n";
            if ( ($usr eq $prontus_varglb::USERS_ID) && ($tipart eq $fid) ) {
                $art_forbidden = 0; # habilitado
            };
        };
    } else {
        $art_forbidden = 0;
    };

    # Ver si corresponde poner link para editar o no.
    my $editable = 1;
    if ($prontus_varglb::USERS_PERFIL eq 'P') { # Periodista
        # Si el art. es de otro usuario <> '' # 7.0
        if ( ($users_id ne '') && ($users_id ne $prontus_varglb::USERS_ID) && ($prontus_varglb::PERIODISTA_EDITAR_ARTICULOS_AJENOS ne 'SI') ) {
            $editable = 0;
        };
    };
    if ($prontus_varglb::USERS_PERFIL eq 'E') { # Editor
        # Si el art. es de otro usuario <> '' # 7.0
        if ( ($users_id ne '') && ($users_id ne $prontus_varglb::USERS_ID) && ($prontus_varglb::EDITOR_EDITAR_ARTICULOS_AJENOS ne 'SI') ) {
            $editable = 0;
        };
    };
    $editable = 0 if ($art_forbidden);
    $loop_art_tpl =~ s/%%_editable%%/$editable/g;



    # Fecha hora publicacion
    my $publicacion;
    my ($feciso, $hrminseg);
    if (($art_fechap) && ($art_fechap ne '9' x 8)) {
        if ($art_horap =~ /(\d\d):?(\d\d)/) {
            $art_horap = $1 . ':' . $2;
        }
        else {
            $art_horap = '00:00';
        };
        $publicacion = &glib_hrfec_02::des_normaliza_fecha($art_fechap) . ' ' . $art_horap . 'hrs.';
    };
    $loop_art_tpl =~ s/%%_fec_publicacion%%/$publicacion/g;

    # Fecha hora expiracion
    my $expiracion;
    if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
        if (($art_fechae) && ($art_fechae ne '9' x 8)) {
            if ($art_horae =~ /(\d\d):?(\d\d)/) {
                $art_horae = $1 . ':' . $2;
            }
            else {
                $art_horae = '00:00';
            };
            $expiracion = &glib_hrfec_02::des_normaliza_fecha($art_fechae) . ' ' . $art_horae . 'hrs.';
        };
        $loop_art_tpl =~ s/%%_fec_expiracion%%/$expiracion/g;
        $loop_art_tpl =~ s/<!--control_fecha-->(.*)<!--\/control_fecha-->//sg if (!$expiracion);
    } else {
        $loop_art_tpl =~ s/<!--control_fecha-->(.*)<!--\/control_fecha-->//sg;
    };


    return $loop_art_tpl;

}; # sub

# ---------------------------------------------------------------
sub get_potencialpub {
  # Obtiene status de publicacion potencial del artic.
  # El artic sera potencialmente publicable si tiene alta y si
  # sus fechas estan ok (si es q hay control fecha)
  my ($alta, $art_fechap, $art_horap, $art_fechae, $art_horae) = @_;

  # las fechas de entrada vienen \d{8} y las horas \d{4}

  if ( ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS eq 'SI') && (! $alta) ) {
    return 0; # no es potencialmente publicable ya q no tiene alta
  };
  if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
    $art_horap .= '00' if ($art_horap ne '');
    $art_horae .= '00' if ($art_horae ne '');
    if (! &lib_prontus::fechas_ok('', $art_fechap, $art_horap, $art_fechae, $art_horae)) {
      return 0; # no es potencialmente publicable ya q sus fechas is not in range
    };
  };

  return 1; # publicable

};
# ---------------------------------------------------------------
sub get_glosa_tipo_ficha {
  # Obtiene la glosa asociada al tipo de articulo
  my ($tipo_ficha) = $_[0];
  my ($glosa, $key);

  foreach $key (keys %prontus_varglb::FORM_PLTS) {
    # El valor a mostrar esta despues de los 2 puntos en la clave.
    if ($key =~ /^$tipo_ficha *: *(.+)/) {
      $glosa = $1;
    };
  };
  return $glosa;
};

# ---------------------------------------------------------------
sub get_path_link {
# Obtiene el path realivo del articulo
  my ($path_artic) = $_[0];

  $path_link = $path_artic;
  $path_link =~ s/^$prontus_varglb::DIR_SERVER//is; # Path normal al archivo

  return $path_link;
};

# ---------------------------------------------------------------
sub get_secc_basepub {
# Retorna lista con las secciones de la edicion base en las que aparece publicado el articulo.
my ($art_file) = $_[0]; # art. por el que  se consulta, sin path y con ext.
my ($pathdir_seccs) =  $prontus_varglb::DIR_SERVER .
                       $prontus_varglb::DIR_CONTENIDO .
                       $prontus_varglb::DIR_EDIC .
                       $prontus_varglb::DIR_UNICAEDIC .
                       $prontus_varglb::DIR_SECC;

# Deduce del path completo de la portada, el del xml.
my ($pathdir_seccs_xml) = $pathdir_seccs;
$pathdir_seccs_xml =~ s/\/port$/\/xml/;


my (@entries, $entry, $arch_seccion, $text_seccion, $lista_secc);

  # Examina portadas de la edicion base.
  @entries = &lee_dir($pathdir_seccs_xml);
  @entries = sort @entries;
  foreach $entry (@entries) {

    if (($entry !~ /^\./g) and ($entry !~ /^preview/g)) {
      $arch_seccion = "$pathdir_seccs_xml/$entry";
      # print STDERR "\n\narch_seccion[$arch_seccion]";
      if ((-s $arch_seccion) and (! -d $arch_seccion)) {
        $text_seccion = &read_file_ref($arch_seccion);
        # print "seccion:[$entry] "; # debug
        # Rescatar la info de c/artic de la seccion
        # print STDERR "\ntext_seccion[$text_seccion]";
        # while ($$text_seccion =~ /<!--ROWARTIC,([^,]+),([^,]+),([^,]+),([^,]+)(,?.*?)-->/sg) {
        while ($$text_seccion =~ /<rowartic>[ \n]*?<dir>(\d+?)<\/dir>[ \n]*?<file>(.*?)<\/file>[ \n]*?<area>(\d*?)<\/area>[ \n]*?<ord>(\d*?)<\/ord>[ \n]*?<?v?b?>?(\w*?)<?\/?v?b?>?[ \n]*?<?i?n?>?(.*?)<?\/?i?n?>?[ \n]*?<?o?u?t?>?(.*?)<?\/?o?u?t?>?[ \n]*?<?p?u?b?>?(\d?)<?\/?p?u?b?>?[ \n]*?<\/rowartic>/isg) {

          my ($dirfecha,$art,$area,$prio,$ext_art,$pub,$vb) = '';
          ($dirfecha,$art,$area,$prio,$vb,$pub) = ($1,$2,$3,$4,$5,$8);

          my ($nom_secc) = $entry;
          $nom_secc =~ s/\.\w*$//; # remueve extension del nombre del archivo.
          if ($art_file eq $art) {
            $lista_secc .= ', %' . $nom_secc . '/%';             # Estas marcas se sustituiran despues por los tags de font.
          };
        };# while
      };# if
    };# if

  };# foreach
  return $lista_secc;

};
# ---------------------------------------------------------------
sub tiene_seccion {
# Revisa si el archivo pasado como parametro se encuentra publicado en alguna seccion de la edicion
# seleccionada.
# Si no esta en el hash %HASH_ARTICULOS quiere decir que no tiene seccion asignada.

# Parametros :
# 0) Nombre del archivo a consultar, con extension y sin path.

# Retorna la lista de secciones donde figura el articulo, separada por comas.

my ($artic) = $_[0];
my ($key, $secciones, $tiene, $key_aux);
my (@sorted_secc);

  foreach $key (keys %HASH_ARTICULOS) {
    $keyaux = $key;
    $key =~ s/\_\_.*//; # dejar solo la parte de la clave correspondiente al nombre del archivo.
    if ($key eq $artic) {
      $keyaux =~ s/.*?\_\_(.*?)\..*?//s; # dejar solo la parte de la clave correspondiente al nombre de la portada.
      $keyaux = $1;
      # $secciones .= $keyaux . ', ';      #1.6
      push @sorted_secc, $keyaux;
    }
  }


  @sorted_secc = sort {$a cmp $b} (@sorted_secc);

  foreach $key (@sorted_secc) {
    $secciones .= $key . ', ';
  };
  $secciones =~ s/\, $//; # sacar coma y espacio sobrante  #1.6

  return $secciones;


};


# -------------------------------END SCRIPT----------------------
