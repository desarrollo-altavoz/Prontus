#!/usr/bin/perl


# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# SCRIPT.
# -----------
# sitemap_pags.cgi

# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-px/  o /cgi-cpn/

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Genera Sitemap del sitio con las páginas más recientes

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# via cron o consola
# $ARGV[0]: Dominio de las páginas. Ej:  www.cooperativa.cl
# $ARGV[1]: Document Root del Servidor. Ej:  /sites/cooperativa.cl/web
# $ARGV[2]: Nombre del prontus. Ej:  prontus_nots

# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# $DOCUMENT_ROOT . '/' . $PRONTUS_ID . $sitemap_varglb::PATH_TO_XML_PAGS

# ---------------------------------------------------------------
# Tablas.
# ------------------------
# BD: 'prontus_nots'. Tabla: 'ART'
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# Revisar historial en la release

# ---------------------------------------------------------------
# TODO.
# ---------------------------
# Revisar ToDo en la release

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
# HISTORIAL DE VERSIONES.
# -----------------------
# 1.1 12/12/2016 - SCT - Se corrige el modo para obtener URL de artículos. Ahora lo hace desde la lib_prontus

BEGIN {
    my $path = $ENV{'DOCUMENT_ROOT'};
    my @aux;
    $path = $0;
    @aux = split /\// , $path;
    pop (@aux);
    $path = join '/', @aux;
    unshift(@INC,$path);

    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/sitemaps$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
}

use strict;
use sitemap_varglb;
use sitemap_utils;
use sitemap_glib_dbi_02;
use sitemap_glib_fildir_02;
use DBI;
# use Data::Dumper;

use utf8;
use prontus_varglb; &prontus_varglb::init();
use lib_prontus;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my $SERVER_NAME;
my $DOCUMENT_ROOT;
my $PRONTUS_ID;
my $PROTOCOL;
my $ANIO_MES;

main:{

    $SERVER_NAME = $ARGV[0];
    $DOCUMENT_ROOT = $ARGV[1];
    $PRONTUS_ID = $ARGV[2];
    $ANIO_MES = $ARGV[3];
    $PROTOCOL= $sitemap_varglb::PROTOCOL;

    if ($DOCUMENT_ROOT eq '' || $PRONTUS_ID eq '') {
        print "----------\nError en los parametros de entrada: SERVER_NAME DOCUMENT_ROOT PRONTUS_ID ANIO_MES\n";
        print "Ej: /var/www/prontus_next.cl/web prontus_noticias 202010\n----------\n";
        exit;
    }

    die("El path de entrada no es valido") unless(-d $DOCUMENT_ROOT . "/" . $PRONTUS_ID);

    if ($ANIO_MES ne '' && $ANIO_MES !~ /^\d{6}$/) {
        print "El parametro ANIO_MES es opcional. Si lo ingresa, debe usar el formato aaaamm.\n";
        print "Ej: perl sitemap_pags.cgi prontus.cl /var/www/prontus.cl/web prontus_noticias 202010\n";
        exit;
    }

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($PRONTUS_ID);
    &lib_prontus::load_config( &lib_prontus::ajusta_pathconf($relpath_conf) );

    # los sitemaps se separan por meses y se recolectan en un index global.
    my @listaAniosMeses = ();
    if ($ANIO_MES) {
        push @listaAniosMeses, $ANIO_MES;
    } else {
        @listaAniosMeses = &getListaAniosMeses();
    }
    my $maxIndexes = 500; # google acepta un máximo de 500 archivos de sitemap por index global.
    if (scalar @listaAniosMeses > $maxIndexes) {
        $#listaAniosMeses = $maxIndexes; # truncamos el array a ese máximo.
    }

    #print Dumper(\@listaAniosMeses);

    my $xml_port = &procesarPortadas();
    my $agregarPorts = 0; # En la primera iteración adjuntamos las portadas.
    foreach my $anioMes (@listaAniosMeses) {
        my $xml_art = &procesarArticulos($anioMes);
        if ($agregarPorts == 0) {
            $xml_art = $xml_port . $xml_art;
            $agregarPorts = 1;
        }
        # print $xml_art, "\n\n";
        if($xml_art ne '') {
            &generarSiteMap($xml_art, $anioMes);
        }
    }

    my @archivos_sitemap = &getAniosMesesConSitemap;
    # ahora generamos el archivo global
    # print "archivos_sitemap: ".Dumper(\@archivos_sitemap);
    &generarIndex(\@archivos_sitemap);
}

# ---------------------------------------------------------------
# Procesa los artículos y genera un string con los nodos del
# xml asociado a las Portadas. Lee las portadas desde un arreglo
# validando su existencia.
#   Retorna: Un string con los nodos.
sub procesarPortadas {

    my $fecha = &sitemap_utils::getFecha();
    my $nomedic = &sitemap_utils::getEdicVigente($DOCUMENT_ROOT, $PRONTUS_ID);
    my $xml_port;
    foreach my $port (@sitemap_varglb::PORTADAS) {
        my $portada;
        # si la portada tiene ediciones usamos la edicion vigente obtenida anteriormente
        if ($$port[1] eq 'SI' ) {
            $portada = '/' . $PRONTUS_ID . '/site/edic/'.$nomedic.'/port/' . $$port[0];
        } else {
        # si la portada no tiene ediciones usamos base
            $portada = '/' . $PRONTUS_ID . '/site/edic/base/port/' . $$port[0];
        }
        $xml_port = $xml_port . &crearNodoUrl($portada, $fecha, 'hourly', '1.0', ''); # 1.0.1
    }
    return $xml_port;
}

# ---------------------------------------------------------------
# Procesa los artículos y genera un string con los nodos del
# xml asociado a los artículos. Lee los tipos de artículos válidos
# desde un arreglo y luego busca artículos que sean de dichos tipos
# en la Base de Datos. Tabla  ART.
#   Retorna: Un string con los nodos.
sub procesarArticulos {
    my $anioMes = shift;
    my $BD;
    my ($art_titu, $art_dirfecha, $art_id, $art_ext, $secc, $tema, $stema); # 1.0.1
    my %CONF_BD;
    my %CONF_VAR;
    my $xml_art;

    %CONF_BD = &sitemap_utils::datosConf($DOCUMENT_ROOT .'/'. $PRONTUS_ID . '/cpan/'.$PRONTUS_ID.'-bd.cfg');
    %CONF_VAR = &sitemap_utils::datosConf($DOCUMENT_ROOT .'/'. $PRONTUS_ID . '/cpan/'.$PRONTUS_ID.'-var.cfg');

    die("Error al cargar datos de BD") unless(%CONF_BD);
    die("Este Script solo funciona con BD Mysql") unless($CONF_BD{'MOTOR_BD'} eq 'MYSQL');

    # Generacion inicial de las paginas correspondientes a cada dia desde que hay noticias.
    $BD = DBI->connect("DBI:mysql:".$CONF_BD{'NOM_BD'}.":".$CONF_BD{'SERVER_BD'}, $CONF_BD{'USER_BD'}, $CONF_BD{'PWD_BD'})
            or die("Error al conectar a la BD");

    my @params;
    my $sql = "select ART_TITU, ART_DIRFECHA, ART_ID, ART_EXTENSION, SECC_NOM, TEMAS_NOM, SUBTEMAS_NOM from ART";
        $sql .= " left join SECC on (SECC_ID = ART_IDSECC1)";
        $sql .= " left join TEMAS on (TEMAS_ID = ART_IDTEMAS1)";
        $sql .= " left join SUBTEMAS on (SUBTEMAS_ID = ART_IDSUBTEMAS1)";

    my $sql2 = '';

    # Para la Fecha de publicacion
    my $fechahora = &sitemap_utils::getFechaHora();
    push(@params, $anioMes);
    push(@params, $fechahora);
    $sql2 = $sql2 . ' (substring(ART_ID, 1, 6) = ?) AND (ART_FECHAPHORAP <= ?)';

    my $filtro_fichas;
    foreach my $ficha (@sitemap_varglb::ARTICULOS) {
        push(@params, $ficha);
        $filtro_fichas = $filtro_fichas . " or ART_TIPOFICHA = ? ";
    }
    $filtro_fichas =~ s/^ or //;

    # Para el control de Alta
    $sql2 = $sql2 . ' and (ART_ALTA="1")' if($CONF_VAR{'CONTROLAR_ALTA_ARTICULOS'} eq 'SI') ;

    # Para los filtros de Articulo
    $sql2 = $sql2 . ' and (' . $filtro_fichas . ')' if ($filtro_fichas);

    # Para el control fecha
    if($CONF_VAR{'CONTROL_FECHA'} eq 'SI') {
        push(@params, $fechahora, $fechahora);
        $sql2 = $sql2 . ' and ( (ART_FECHAEHORAE >= ? ) ';
        $sql2 = $sql2 . '   or((ART_FECHAEHORAE < ? ) and (ART_SOLOPORTADAS = "1")) )';
    }

    # Si realmente vienen filtros, se concatenan
    if($sql2 ne '') {
        $sql = $sql . ' where ' . $sql2;
    }

    # Finalmente, el order by
    $sql = $sql . " order by ART_FECHAP DESC LIMIT ".$sitemap_varglb::NRO_MAX_PAGS;

    #~ print STDERR "SQL [$sql]\n";

    # 1.0.1
    my $salida = &sitemap_glib_dbi_02::ejecutar_sql_bind_param($BD, $sql, \@params, \($art_titu, $art_dirfecha, $art_id, $art_ext, $secc, $tema, $stema));
    while ($salida->fetch) {

        my $art = '/'.$PRONTUS_ID . '/site/artic/'.$art_dirfecha.'/pags/'.$art_id.'.'.$art_ext;
        my $art_friendly; # 1.0.1

        $art_friendly = &lib_prontus::parse_filef("%%_FILEURL%%", $art_titu, $art_id, $PRONTUS_ID, ".$art_ext", $secc, $tema, $stema) if ($sitemap_varglb::USE_FRIENDLY_URLS); # 1.0.1

        $xml_art = $xml_art . &crearNodoUrl($art, '', '', '0.5', $art_friendly); # 1.0.1
    }
    $salida->finish;

    return $xml_art;
}

# ---------------------------------------------------------------
# Crea un Nodo de portada o Artículo
#   0) Ruta al archivo desde la raíz del sitio
#   1) Fecha de la última modificación
#   2) Frecuencia de actualización
#   3) Prioridad dentro del sitio
sub crearNodoUrl {
    my ($loc, $lastmod, $freq, $prior, $art_friendly) = (@_);
    my $xml_temp;
    if(-f $DOCUMENT_ROOT . $loc) {

        # En el caso que vengan vacios, se debe obtener desde el archivo
        $lastmod    = &sitemap_utils::getFechaArchivo($DOCUMENT_ROOT . $loc)    unless($lastmod);
        $freq       = &sitemap_utils::getFrecuencia($DOCUMENT_ROOT . $loc)      unless($freq);
        $loc = $art_friendly if (($art_friendly) && ($sitemap_varglb::USE_FRIENDLY_URLS)); # 1.0.1
        $loc = $PROTOCOL.'://'.$SERVER_NAME . $loc;
        $xml_temp = $sitemap_varglb::XML_PAGS_MOLDE2;
        $xml_temp =~ s/%%LOC%%/$loc/;
        $xml_temp =~ s/%%LASTMOD%%/$lastmod/;
        $xml_temp =~ s/%%FREQ%%/$freq/;
        $xml_temp =~ s/%%PRIOR%%/$prior/;
    }
    return $xml_temp;
}

# Escribe en disco el contenido del string entregado como
# parámetro. (Le agrega el inicio y el fin).
#   0) String con los nodos de portadas y artículos
sub generarSiteMap {
    my ($xml, $anioMes) = @_;
    my $xml_total = $sitemap_varglb::XML_PAGS_MOLDE1;
    $xml_total =~ s/%%CONTENT%%/$xml/;
    # my $path_xml = $DOCUMENT_ROOT.'/'.$PRONTUS_ID.$sitemap_varglb::PATH_TO_XML_PAGS;
    # $path_xml =~ /^(.+)\/[^\/]+$/;
    # $path_xml =~ s/%%ANIO_MES%%/$anioMes/;
    # &glib_fildir_03::check_dir($1);
    utf8::encode($xml_total) unless($sitemap_varglb::PRONTUS11_UTF8);
    my $gzip_filename = $DOCUMENT_ROOT.'/'.$PRONTUS_ID.$sitemap_varglb::PATH_TO_XML_PAGS.".gz";
    $gzip_filename =~ s/%%ANIO_MES%%/$anioMes/;

    &comprimirBuffer($gzip_filename, $xml_total);

    return 1;
}

# Genera un indice de sitemaps según
# https://support.google.com/webmasters/answer/75712?visit_id=637273939996212081-1472635633&rd=1
# Parámetros:
#   ref a array de meses generados
# Retorna: booleano.
sub generarIndex {
    my $generados = shift;
    my $xml_total = $sitemap_varglb::XML_GLOBAL_MOLDE1;
    my $xml_nodo = $sitemap_varglb::XML_GLOBAL_MOLDE2;

    my $path_gz_sitemap = $PROTOCOL . '://' . $SERVER_NAME . '/' .$PRONTUS_ID . $sitemap_varglb::PATH_TO_XML_PAGS . ".gz";
    
    my $path_xml_index = $DOCUMENT_ROOT.'/'.$PRONTUS_ID.$sitemap_varglb::PATH_TO_PAGS_INDEX;
    $path_xml_index =~ /^(.+)\/[^\/]+$/;
    &sitemap_glib_fildir_02::check_dir($1);

    my $xml;
    my ($sitemap_parcial, $path_parcial);
    foreach my $anioMes (@$generados) {
        $path_parcial = $path_gz_sitemap;
        $sitemap_parcial = $xml_nodo;
        $path_parcial =~ s/%%ANIO_MES%%/$anioMes/;
        $sitemap_parcial =~ s/%%LOC%%/$path_parcial/;
        $xml .= $sitemap_parcial;
    }
    $xml_total =~ s/%%CONTENT%%/$xml/;
    utf8::encode($xml_total) unless($sitemap_varglb::PRONTUS11_UTF8);
    &sitemap_glib_fildir_02::write_file($path_xml_index, $xml_total);
}

# Devuelve un array con los años/meses de archivos sitemap existentes.
# Parámetros: ninguno
# Retorna:
#   array ('yyyymm', 'yyyymm', 'yyyymm', ...)
sub getAniosMesesConSitemap {
    my @files = &sitemap_glib_fildir_02::lee_dir($DOCUMENT_ROOT.'/'.$PRONTUS_ID.$sitemap_varglb::PATH_DIR);
    my @archivos_sitemap = ();
    my $path_tpl = "$sitemap_varglb::PATH_TO_XML_PAGS.gz";
    $path_tpl =~ s/%%ANIO_MES%%/\\d{6}/;
    foreach my $archivo (@files) {
        next if ("$sitemap_varglb::PATH_DIR$archivo" !~ m/$path_tpl/);
        $archivo =~ m/(\d{6})/;
        push @archivos_sitemap, $1;
    }
    return @archivos_sitemap;
}

# Obtiene una lista con todos los años y meses que contienen artículos
# Parámetros: 
#   referencia a conexión a db
# Retorna:
#   Array de strings: [aaaamm, aaaamm, aaaamm, aaaamm,...]
sub getListaAniosMeses {
    my %CONF_BD;

    %CONF_BD = &sitemap_utils::datosConf($DOCUMENT_ROOT .'/'. $PRONTUS_ID . '/cpan/'.$PRONTUS_ID.'-bd.cfg');

    die("Error al cargar datos de BD") unless(%CONF_BD);
    die("Este Script solo funciona con BD Mysql") unless($CONF_BD{'MOTOR_BD'} eq 'MYSQL');

    # Generacion inicial de las paginas correspondientes a cada dia desde que hay noticias.
    my $BD = DBI->connect("DBI:mysql:".$CONF_BD{'NOM_BD'}.":".$CONF_BD{'SERVER_BD'}, $CONF_BD{'USER_BD'}, $CONF_BD{'PWD_BD'})
            or die("Error al conectar a la BD");

    my @listaAniosMeses = ();
    my $anioMes;
    my $sql = "SELECT DISTINCT SUBSTRING(ART_ID, 1, 6) FROM ART ORDER BY ART_ID DESC";
    my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($anioMes));
    while ($salida->fetch) {
        push @listaAniosMeses, $anioMes;
    }
    $salida->finish;

    return @listaAniosMeses;
}

# Recibe una string y crea un archivo comprimido.
# Parámetros
#   nombre del archivo a generar
#   buffer a comprimir
sub comprimirBuffer {
    my $filename = shift;
    my $buffer = shift;
    open (my $gzip_fh, "| /bin/gzip -c > $filename") or die "Error iniciando gzip: $!";

    print $gzip_fh $buffer;
    close $gzip_fh;
}
# -------------------------END SCRIPT----------------------
