#!/usr/bin/perl

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Librería usada por los post_procesos de cooperativa

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# Revisar historial en la release

# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

package sitemap_varglb;

# Version del Producto
$SITEMAP_VERSION = '1.2.2';

# Seteo de Variables
$NRO_MAX_PAGS = 1000;    # máximo segun google 50.000
$NRO_MAX_NEWS = 200;    # máximo segun google 1.000

# 1.0.1
$USE_FRIENDLY_URLS = 1; # 0/1

$FRIENDLY_URLS_VERSION = 2; # Deprecated: Ahora se obtendrá la friendly desde la configuración del prontus

# Protocolo
$PROTOCOL= 'http';

# Site Name para News Sitemaps
$SITENAME = 'desarrollo';

# Encodificar la info como UTF8 si es que no viene como tal
$PRONTUS11_UTF8 = 1;

# Path de archivos y directorios
$PATH_DIR = '/site/';
$PATH_TO_PAGS_INDEX = $PATH_DIR . 'sitemap_pags_index.xml';
$PATH_TO_XML_PAGS = $PATH_DIR . 'sitemap_pags_%%ANIO_MES%%.xml';
$XML_PAGS_MOLDE1 = "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n%%CONTENT%%</urlset>\n";
# $XML_PAGS_MOLDE2 = "<url>\n\t<loc>%%LOC%%</loc>\n\t<lastmod>%%LASTMOD%%</lastmod>\n\t<changefreq>%%FREQ%%</changefreq>\n\t<priority>%%PRIOR%%</priority>\n</url>\n";
$XML_PAGS_MOLDE2 = "<url>\n\t<loc>%%LOC%%</loc>\n</url>\n";

$XML_GLOBAL_MOLDE1 = "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<sitemapindex xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n%%CONTENT%%</sitemapindex>\n";
$XML_GLOBAL_MOLDE2 = "<sitemap>\n\t<loc>%%LOC%%</loc>\n</sitemap>\n";

$PATH_TO_XML_NEWS = '/sitemap_news.xml';
$XML_NEWS_MOLDE1 = '<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">%%CONTENT%%
</urlset>';

$NEWS_IMG_PORT = 'FOTOFIJA_PORT298';#Identificador Imagen Portada
$NEWS_CAPTION_PORT = ''; # Pie de la imagen
$NEWS_IMG_ART = 'FOTOFIJA_ART800';#Identificador Imagen Articulo
$NEWS_CAPTION_ART = 'pie_foto'; #Pie de imagen

$XML_NEWS_MOLDE2 = '
    <url>
        <loc>%%LOC%%</loc>
        <news:news>
            <news:publication>
                <news:name>%%SITENAME%%</news:name>
                <news:language>es</news:language>
            </news:publication>
            <news:geo_locations>Santiago, Chile</news:geo_locations>
            <news:publication_date>%%PUB_DATE%%</news:publication_date>
            <news:title>%%TITULAR%%</news:title>
            <news:keywords>%%KEYWORDS%%</news:keywords>
        </news:news>%%IF_IMG_ART%%
        <image:image>
            <image:loc>%%IMG_ART%%</image:loc>%%IF_CAPTION%%
            <image:caption>%%CAPTION_ART%%</image:caption>%%/IF_CAPTION%%
        </image:image>%%/IF_IMG_ART%% %%IF_IMG_PORT%%
        <image:image>
            <image:loc>%%IMG_PORT%%</image:loc>%%IF_CAPTION%%
            <image:caption>%%CAPTION%%</image:caption>%%/IF_CAPTION%%
        </image:image>%%/IF_IMG_PORT%%
    </url>';

# Configuración del sitio
@PORTADAS;
# formato : ['nombre_portada.html', 'Usar ediciones: SI|NO']
push(@PORTADAS, ['inicio.html', 'NO']);
push(@PORTADAS, ['newsletter.html', 'SI']);

@ARTICULOS; # campo ART_TIPOFICHA de la BD
push(@ARTICULOS, 'fid_noticia');
push(@ARTICULOS, 'fid_foto');

@ARTICULOS_NEWS;
push(@ARTICULOS_NEWS, 'fid_general');
push(@ARTICULOS_NEWS, 'fid_audio');
push(@ARTICULOS_NEWS, 'fid_evento');
push(@ARTICULOS_NEWS, 'fid_galeria');
push(@ARTICULOS_NEWS, 'fid_video');

# ---------------------------------------------------------------
return 1;
