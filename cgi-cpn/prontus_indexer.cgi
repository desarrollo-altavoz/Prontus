#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

#
# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Generar un indice para el buscador de Prontus (Prontus Search).
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Directorios Arbitrarios.
# Este indexador recorre todo el directorio de inicio, determinando
# si el indice debe ser reconstruido.
#
# El indice de los directorios arbitrarios es almacenado en:
# cpan/data/search/raw/
#
# Directorios Prontus.
# Este indexador recorre todo el directorio site/artic de un Prontus,
# identificando anos y determinando si los indices correspondientes
# deben ser reconstruidos.
#
# El indice de cada ano es almacenado en directorios de la forma:
# cpan/data/search/<nombre prontus>/aaaa/
#
# Los archivos de indice generados son:
#
# words.idx      - Indice de palabras.
#   Formato: Palabra=ID.
#               Las palabras se guardan ordenadas, pero los IDs se
#               generan on the fly, asi que no tienen un orden.
#
# cars.idx       - Indice alfabetico de primeros caracteres de palabras.
#   Formato: Letra=Offset.
#               Offset en el archivo de palabras donde parte ese caracter.
#               (Este archivo ya no se usa, pero se genera igual).
#
# files.idx      - Indice de articulos.
#   Formato:
#   IDarticulo=fechap|TS.extension|titular|meta1|meta2|meta3|resumen|seccion|tema|subtema|metadata1|..|metadata10
#   seccion, tema y subtema van en texto; no en IDs.
#   Si el archivo no es Prontus, fechap, seccion, tema y subtema van en
#   blanco, y TS.extension corresponde a la ubicacion del archivo.
#
# filesindex.idx - Indice de articulos y sus palabras.
#   Formato:
#   IDarticulo=|IDpalabra count|IDpalabra count|IDpalabra count|IDpalabra count|...
#   Este es un archivo temporal que es eliminado despues de la indexacion.
#
# filesindexf.idx - Indice de articulos y sus palabras, disenado para la busqueda por frases.
#   Formato:
#   IDarticulo=|IDpalabra ubicacion1 ubicacion2 ...|IDpalabra ubicacion1 ubicacion2 ...|...
#   Este es un archivo temporal que es eliminado despues de la indexacion.
#
# wordsindex.idx - Indice de palabras y los articulos que las contienen.
#   Formato:
#   IDpalabra=|IDarticulo count|IDarticulo count|IDarticulo count|IDarticulo count|...
#
# El archivo utilizado como semaforo es: semaforo.txt
#
# Dentro del archivo de configuracion Prontus Search, se tiene:
# # Directorios de otros Prontus a Indexar (i = 1, 2, 3,...) aparte del directorio de este Prontus.
# PRONTUS_DIR_i = <prontus dir>
# # Directorios Arbitrarios a Indexar (i = 1, 2, 3,...).
# RAW_DIR_i = <dir desde la raiz del sitio>
# # Tipos de Archivos Arbitrarios a Indexar.
# RAW_FILETYPES = <extensiones separadas por espacios>
# # Tipos de URLs a Indexar en modalidad spider.
# # Ademas de estos, se indexan los directorios (/) y urls que terminan en un string sin puntos.
# URL_FILETYPES = html htm shtml php asp jsp
# # Maximo de paginas a indexar.
# URL_MAXPAGS = 100
# # URLs a indexar en modalidad spider.
# URL_DIR_1 = http://www.nic.cl/
# # Límite asociado al punto de partida "n".
# # Esto permite acotar la búsqueda a subdirectorios dentro del URL inicial,
# # para indexar sólo una parte del sitio web.
# URL_SCOPE_1 = http://www.nic.cl/
# # Tipos de FID que seran consideradas validos para ser indexados.
# FIDS = fid_diario.html fid_general.html
# # Numero de caracteres a almacenar como resumen.
# RESUMEN = 100
# # Tamano maximo de la data a indexar.
# MAXCARS = 100000
# # Limite para palabras irrelevantes (%).
# RATIO = 50
# # Limite de caracteres para considerar que el texto es significativo.
# MINTEXT = 20
# # Variable Prontus que sera considerada el titular.
# TITLEVAR = TITULAR
# # Variables Prontus sobre las que se buscara.
# TEXTVARS = TEXTbajada TEXTarticulo
# # Resultados por pagina.
# RESPERPAG = 50
# # Maximo de paginas a mostrar.
# MAXPAGS = 20
# # Version de Prontus (9 o 10).
# PRONTUS_VER = 10;
# # Maximo de instancias permitidas (Unix).
# SEARCH_MAXEXEC = 5
# # Usa friendly urls (1) o no (0).
# USEFRIENDLYURLS = 1
# # Variables "META", usadas para perfilacion de contenidos u otra clasificacion.
# # Variables validas: META1 META2 y META3
# META1 = RDO_ROL
# META2 = RDO_AREA
# # Variables "META" adicionales, usadas para perfilacion de contenidos u otra clasificacion.
# # Variables validas: METADATA1 .. METADATA10
# METADATA1 = alerta
# METADATA2 = imagen
# # Filtro para archivos adjuntos.
# # FILEFILTER <extension> <ejecutable>
# # Si se especifica, indexara los archivos adjuntos de esa extension.
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cron, linea de comandos o post-proceso:
# prontus_indexer.cgi <prontus dir> [<forzar>]
#   donde <prontus dir> es el directorio del publicador Prontus (absoluto).
#           Ejemplo: /sites/mercuriovalpo.cl/web/prontus_noticias
#         <forzar> es el Prontus (o raw) para el que se desea forzar un reindexado.
#
# Desde la web, como cgi:
# prontus_indexer.cgi?dir=<prontus dir>&forzar=[<forzar>]
#   Ejemplo:
#     www.prontus.cl/cgi-cpn/prontus_indexer.cgi?dir=/sites/prontus.cl/web/prontus
#     o
#     www.prontus.cl/cgi-cpn/prontus_indexer.cgi?dir=/prontus
#     (En modalidad cgi, si no se incluye el document_root, Prontus lo inserta)
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# No registra.
# ---------------------------------------------------------------

# 1.0 - 25/06/2005 - Primera version.
# 1.1 - 13/07/2005 - Adaptacion para indexar directorios arbitrarios.
# 1.2 - 21/07/2005 - Cambios para adaptar mejor a Prontus.
# 1.3 - 26/07/2005 - Aplica algunas optimizaciones.
# 1.4 - 01/08/2005 - Permite ser invocado via web (solo para sitios pequenos, el timeout es problema del usuario).
# 1.5 - 16/08/2005 - Robustece la seguridad de getFormData.
# 1.6 - 15/09/2005 - YCH - Ahora los Directorios Prontus a Indexar y Directorios Arbitrarios a Indexar
#                          vienen con ruta relativa al document root, ej: /prontus_noticias. Ademas se
#                          validan los directorios antes de intentar indexarlos
# 1.7 - 18/04/2006 - ALD - Agrega variables de perfilacion genericas META1, META2 y META3
#                          (solo para Prontus 10 o superior).
# 1.8 - 07/03/2007 - ALD - Mejora separacion de elementos por espacios.
# 1.9 - 10/04/2007 - ALD - Agrega capacidad para indexar archivos adjuntos usando un filtro externo (Unix).
#                          Solo para Prontus > 10.
# 1.10- 24/08/2007 - ALD - Mejora capacidad para descubrir variables en contenido raw.
#                        - Solo indexa raw si es forzado a hacerlo.
# 1.11- 28/08/2007 - ALD - Corrige formato de indice RAW.
# 1.12- 03/09/2007 - ALD - Adapta para IIS.
# 1.13- 19/10/2007 - ALD - Adapta para que corra por shell windows o como tarea prog. de la forma:
#                          c:\sites\prontusRC5\cgi-cpn\prontus_indexer.cgi "c:/sites/prontusRC5/prontus_casapiedra"
# 1.14- 07/01/2008 - ALD - Agrega capacidad de indexar sitios en modalidad spider.
# 1.15  12/03/2008 - ALD - Usa rutina get_dir_server de lib_search para determinar el DOCUMENT_ROOT.
# 1.16  07/05/2008 - ALD - Agrega un espacio en blanco al detectar contenidos, para evitar que las palabras se peguen.
# 1.18  30/05/2008 - PRB - Se modifca tag <_TIPO_FICHA> por <_FID>.
# 1.19  01/07/2008 - ALD - Genera indice para buscar por frases.
#                        - Mejora recuperacion de datos META.
# 1.20  22/07/2008 - ALD - Soluciona bug en regexp, que hacia que se indexaran articulos sin alta.
# 1.21  22/07/2008 - YCC - Se modifica tag <_FID> por <_TIPO_FICHA> por compatibilidad con versiones 10.12.x.
# 1.22  06/11/2008 - ALD - Soluciona bug en rescate de datos META.
# 1.23  12/08/2009 - ALD - Agrega flag i a las regexp para compatibilidad con nuevos tags Prontus, que son todos lowercase.
# 1.23.1 04/09/2009  ALD - Corrige fid por defecto.
#                        - Elimina extensiones de los fids a indexar, si las traen.
#                        - Al indexar, compara la horap junto con la fechap.
#                        - Corrige comparacion con limite de repeticion de palabras.
#                        - Agrega chequeo de fechae y horae.
#                        - Elimina funcion fechas_ok por ser erronea.
# 1.23.2 20/01/2010  ALD - Permite indexado de variables reservadas Prontus declaradas en TEXTVARS dentro de la cfg.
# 1.23.3 25/03/2010  YCC - Fix de bug en procesamiento de metadata.
# 1.23.4 13/05/2010  ALD - Estripea retornos de carro de los campos meta y metadata.
#                        - Solo trunca el resumen si es necesario.
#                        - Busca titular sin CDATA.
# 1.24   16/12/2010  ALD - Cambia a UTF-8.
# 1.25   16/05/2010  YCC - Arregla ajuste de caracteres que fallaba por el utf8, ya que length y substr no soportan utf8
# 1.26   30/06/2011  ALD - Verifica variable _soloportadas para no considerar la fechae.
#                        - Completa cambios de mod 1.25.
#                        - Elimina compatibilidad con Prontus 9.
#                        - Si se detecta FORZAR, solo se indexa el ano indicado. No se buscan otros anos.

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

BEGIN {
  my ($SCRIPTROOT) = '.';
  unshift(@INC,$SCRIPTROOT); # Para dejar disponibles las librerias.
  $SCRIPTROOT = $0;
  $SCRIPTROOT =~ s/[^\/]+$//g;
  unshift(@INC,$SCRIPTROOT); # Para dejar disponibles las librerias.
  #~ my $pesoscero = $0;
  #~ $pesoscero =~ s/(\w+\.cgi)$/prontus_temp\/\1/;
  # open (STDERR, ">$pesoscero.error.log");

};

# Captura STDERR
#~ use lib_stdlog;
#~ &lib_stdlog::set_stdlog($0, 51200);

use strict;
use File::Copy;
use lib_search;
use glib_hrfec_02;

$|=1;

# open DEB,'>debug.txt';

# 1.12 Deteccion de la raiz del sitio web.
# 1.15 my $DOCUMENT_ROOT;
# 1.15 if ($ENV{'DOCUMENT_ROOT'} ne '') {
# 1.15   $DOCUMENT_ROOT = $ENV{'DOCUMENT_ROOT'};
# 1.15 }elsif ($ENV{'PATH_TRANSLATED'} ne '') {
# 1.15   $DOCUMENT_ROOT = $ENV{'PATH_TRANSLATED'};
# 1.15 };
my $DOCUMENT_ROOT = &lib_search::get_dir_server(); # 1.15

# Variables de la invocacion.
my $INVOCACION;
my $PRONTUS_DIR;
my $FORZAR;
my %FORM;
&getFormData();
if ($FORM{'dir'} ne '') { # 1.4 Invocacion via cgi.
  print "Content-type: text/html\n\n";
  print "<p>*** Inicio ***</p>";
  $INVOCACION = 'web';
  $PRONTUS_DIR = $FORM{'dir'};
  $FORZAR = $FORM{'forzar'};
  if ($PRONTUS_DIR !~ /^\//) { $PRONTUS_DIR = '/' . $PRONTUS_DIR; };
  $PRONTUS_DIR =~ s/\/$//g; # Elimina posibles slashes puestos al final.
  if ($PRONTUS_DIR !~ /^$DOCUMENT_ROOT/) {
    $PRONTUS_DIR = $DOCUMENT_ROOT . $PRONTUS_DIR;
  };
}else{ # Invocacion via linea de comandos o cron.
  $INVOCACION = 'cron';
  $PRONTUS_DIR = $ARGV[0];
  # Si no es windows, entonces aplicar lo de ald. # 1.13
  if ($PRONTUS_DIR !~ /^\w:/) {
    if ($PRONTUS_DIR !~ /^\//) { $PRONTUS_DIR = '/' . $PRONTUS_DIR; };
  };
  $PRONTUS_DIR =~ s/\/$//g; # Elimina posibles slashes puestos al final.
  $FORZAR = $ARGV[1];
};
# Variables globales.
my $ROOTDIR; # Directorio raiz del sitio web.
my $SEARCH_DIR = "$PRONTUS_DIR/cpan/data/search"; # Directorio de trabajo.
my $CFG_FILENAME = 'buscador_prontus.cfg';     # Nombre del archivo de configuracion.
my $WORDS_FILENAME = 'words.idx';   # Nombre de los archivos de palabras.
my $CARS_FILENAME = 'cars.idx';     # Nombre de los archivos de caracteres.
my $FILES_FILENAME = 'files.idx';   # Nombre de los archivos indice de articulos.
my $FILESINDEX_FILENAME = 'filesindex.idx'; # Nombre de los archivos indice de archivos.
my $WORDSINDEX_FILENAME = 'wordsindex.idx'; # Nombre de los archivos de indice de palabras.
my $FILESINDEXF_FILENAME = 'filesindexf.idx'; # 1.19 Nombre de los archivos indice de archivos para busqueda por frases.
my $SEMAFORO_FILENAME = 'semaforo.txt';     # Nombre del archivo semaforo.
my $RAW_DIRNAME = 'raw';     # Nombre del directorio de indices de directorios brutos (raw).
my %CFG = ();   # Variables del archivo de configuracion.
my %WORDS = (); # Palabras.
my $WIDX;       # Indice de palabras.
my $FIDX;       # Indice de archivos.
my @PRONTUS_DIR; # Prontus que hay que indexar.
my @RAW_DIR;     # Directorios brutos que hay que indexar.
my @RAW_FILETYPES; # Extensiones validas para los archivos raw.
my $PRONTUS;    # Nombre del publicador Prontus.
my $DIR;        # Nombre del directorio bruto (raw).
my %FILEFILTER; # 1.9 Filtros por extension, para indexar archivos de datos.

my $URL_DIRNAME = 'url'; # 1.14 Nombre del directorio de indices de directorios URL (spider).
my @URL_DIR;             # 1.14 URLs que hay que indexar.
my %LINKS;               # 1.14 URL visitados por el spider.
my $URL_FILETYPES_REGEXP; # 1.14 Expresion regular para validar los URL a indexar.
my $PROFUNDIDAD = 0;     # 1.4 Profundidad de la navegacion del spider (para limitarla).

# Deduce el nombre del publicador Prontus.
$PRONTUS_DIR =~ s/\\/\//g; # 1.4 Convierte backslashes en slashes.
if ($PRONTUS_DIR =~ /^(.+)(\/[^\/]+)$/) {
  $ROOTDIR = $1;
  $PRONTUS_DIR[0] = $2; # (comentar para que no indexe de nuevo las noticias)
}else{
  print "Directorio Prontus no valido [$PRONTUS_DIR].\n";
  exit;
};
my $FECHAACTUAL = &lib_search::fecha_iso(); # Fecha de hoy en formato ISO.
my $FECHAHORAACTUAL = &lib_search::timestamp_iso(); # 1.23.1 Fecha y hora de hoy en formato ISO.
my %ANOS;  # Anos a indexar. $ANOS{ano} = time del archivo mas recientemente modificado.
my $ANO;   # Ano actualmente indexandose.
my $MTIME; # Tiempo de modificacion de un indice.

# ###################################################
# Main
# Verifica semaforo.
if (-f "$SEARCH_DIR/$SEMAFORO_FILENAME") {
  # Si el semaforo es menos antiguo que 12 horas, aborta la ejecucion.
  # (0: $dev, 1: $ino, 2: $mode, 3: $nlink, 4: $uid, 5: $gid, 6: $rdev, 7: $size, 8: $atime, 9: $mtime, 10: $ctime, 11: $blksize, 12: $blocks).
  if ((stat("$SEARCH_DIR/$SEMAFORO_FILENAME"))[9] > (time - 43200)) {
    if ($INVOCACION eq 'web') {
      print "<p>*** Semaforo activo. Hay otro proceso de indexaci&oacute;n corriendo. ***</p>\n";
    }else{
      print "Semaforo activo. Hay otro proceso de indexaci&oacute;n corriendo.\n";
    };
    exit;
  };
};
unlink "$SEARCH_DIR/$SEMAFORO_FILENAME";
open SEMAFORO, ">$SEARCH_DIR/$SEMAFORO_FILENAME";
print SEMAFORO time;
close SEMAFORO;

# Lee archivo de configuracion.
%CFG = &lib_search::get_config("$PRONTUS_DIR/cpan/$CFG_FILENAME");
# Valida las variables del archivo de configuracion.
&validacfg();
# Detecta los Prontus y directorios brutos que hay que indexar.
&detectadirs();

# Parte indexando los Prontus.
foreach my $prontus (@PRONTUS_DIR) {
  $PRONTUS = $prontus; # Esto es para visibilidad de esta variable dentro de las rutinas.
  %ANOS = ();
  # print "Indexando $PRONTUS "; # debug
  if ($INVOCACION eq 'web') { print "<p><B>&raquo; Indexando $PRONTUS</B></p> \n"; };
  if (! -d "$ROOTDIR$PRONTUS") {
    if ($INVOCACION eq 'web') { print "<p>Directorio $PRONTUS no existe en web server</p> \n"; };
    next;
  };
  # print "$PRONTUS\n"; # debug
  if ($FORZAR =~ /^\d{4}$/) {
    # 1.26 Si hay $FORZAR entonces se indexa solo el ano indicado.
    $ANOS{$FORZAR} = 1;
  }else{
    # Si no, determina los anos existentes y determina la fecha de modificacion mas reciente para cada uno.
    &busca_anos("$ROOTDIR$PRONTUS/site/artic");
  };
  # Recorre los anos reindexando en caso necesario.
  foreach my $ano (sort {$b cmp $a} keys %ANOS) { # 1.10

    $ANO = $ano; # Esto es para visibilidad de esta variable dentro de las rutinas.
    # print "$ANO "; # debug
    if ($INVOCACION eq 'web') { print "$ANO \n"; };
    # Si no es necesario reindexar, continua con el siguiente ano.
    if (-f "$SEARCH_DIR$PRONTUS/$ANO/$WORDSINDEX_FILENAME") {
      $MTIME = (stat("$SEARCH_DIR$PRONTUS/$ANO/$WORDSINDEX_FILENAME"))[9];
      # print "MTIME=$MTIME\n"; # debug
      # print $MTIME . '<=>' . $ANOS{$ANO} . "\n" ; # debug
      if ($FORZAR ne $ANO) { next if ($MTIME > $ANOS{$ANO}); };
    };
    %WORDS = ();
    $WIDX = 0;   # Indice de palabras.
    $FIDX = 0;   # Indice de archivos.
    # Crea el directorio para este indice.
    &lib_search::crea_dir("$SEARCH_DIR$PRONTUS/$ANO");
    # Inicia el proceso de indexado global.
    if ($INVOCACION eq 'web') { print "<p>Buscando art&iacute;culos...</p> \n"; };
    &busca_articulos("$ROOTDIR$PRONTUS/site/artic");
    # Escribe indices de palabras.
    if ($INVOCACION eq 'web') { print "<p>Escribiendo &iacute;ndices de palabras...</p> \n"; };
    &escribe_palabras("$SEARCH_DIR$PRONTUS/$ANO");
    # Genera cross-index de palabras.
    if ($INVOCACION eq 'web') { print "<p>Escribiendo &iacute;ndices cruzados...</p> \n"; };
    &genera_wordsindex("$SEARCH_DIR$PRONTUS/$ANO");
    # Escribe los archivos definitivos.
    if ($INVOCACION eq 'web') { print "<p>Sustituyendo archivos &iacute;ndice...</p> \n"; };
    move("$SEARCH_DIR$PRONTUS/$ANO/$WORDS_FILENAME.tmp","$SEARCH_DIR$PRONTUS/$ANO/$WORDS_FILENAME");
    move("$SEARCH_DIR$PRONTUS/$ANO/$CARS_FILENAME.tmp","$SEARCH_DIR$PRONTUS/$ANO/$CARS_FILENAME");
    move("$SEARCH_DIR$PRONTUS/$ANO/$FILES_FILENAME.tmp","$SEARCH_DIR$PRONTUS/$ANO/$FILES_FILENAME");
    move("$SEARCH_DIR$PRONTUS/$ANO/$FILESINDEXF_FILENAME.tmp","$SEARCH_DIR$PRONTUS/$ANO/$FILESINDEXF_FILENAME"); # 1.19
    move("$SEARCH_DIR$PRONTUS/$ANO/$WORDSINDEX_FILENAME.tmp","$SEARCH_DIR$PRONTUS/$ANO/$WORDSINDEX_FILENAME");
    unlink "$SEARCH_DIR$PRONTUS/$ANO/$FILESINDEX_FILENAME.tmp";
    unlink "$SEARCH_DIR$PRONTUS/$ANO/$FILESINDEXF_FILENAME.tmp"; # 1.19
    if ($INVOCACION eq 'web') { print "<p>&raquo; FIN de indexaci&oacute;n de $PRONTUS</p> \n"; };
  };
  # print "\n"; # debug
};

# Indexa los directorios brutos.
# print "RAWS DIR:@RAW_DIR\n"; # debug
if ($#RAW_DIR >= 0) {
  # Determina si es necesario reindexar o no.
  # print "$FORZAR ne $RAW_DIRNAME\n"; # debug
  if ($FORZAR ne $RAW_DIRNAME) {
    foreach my $dir (@RAW_DIR) {
      $DIR = $dir; # Esto es para visibilidad de esta variable dentro de las rutinas.
      if (-f "$SEARCH_DIR/$RAW_DIRNAME/0000/$WORDSINDEX_FILENAME") {
        # 1.10 No reindexa directorios raw a menos que sea forzado.
        # $MTIME = (stat("$SEARCH_DIR/$RAW_DIRNAME/0000/$WORDSINDEX_FILENAME"))[9];
        # # print "MTIME = $MTIME " . &maxtime("$ROOTDIR/$DIR") . "\n"; # debug
        # if ($MTIME < &maxtime("$ROOTDIR$DIR")) {
        #   $FORZAR = $RAW_DIRNAME; # Fuerza reindexado.
        #   last;
        # };
      }else{
        $FORZAR = $RAW_DIRNAME; # Fuerza reindexado si es que no existe el directorio.
        last;
      };
    };
  };
  # print "$FORZAR ne $RAW_DIRNAME\n"; # debug
  if ($FORZAR eq $RAW_DIRNAME) {
    %WORDS = ();
    $WIDX = 0;   # Indice de palabras.
    $FIDX = 0;   # Indice de archivos.
    # Crea el directorio para este indice.
    &lib_search::crea_dir("$SEARCH_DIR/$RAW_DIRNAME/0000");
    my $raws_indexados;
    unlink "$SEARCH_DIR/$RAW_DIRNAME/0000/$FILES_FILENAME.tmp"; # 1.10
    unlink "$SEARCH_DIR/$RAW_DIRNAME/0000/$FILESINDEX_FILENAME.tmp"; # 1.10
    foreach my $dir (@RAW_DIR) {
      $DIR = $dir; # Esto es para visibilidad de esta variable dentro de las rutinas.
      $MTIME = (stat("$SEARCH_DIR/$RAW_DIRNAME/0000/$WORDSINDEX_FILENAME"))[9];
      # 1.10 Verifica si es necesario indexar.
      if ($MTIME < &maxtime("$ROOTDIR$DIR")) {
        # print "Indexando $DIR\n"; # debug
        if ($INVOCACION eq 'web') { print "<p><b>&raquo; Indexando $DIR</b></p> \n"; };
        if (! -d "$ROOTDIR$DIR") {
          if ($INVOCACION eq 'web') { print "<p>Directorio $DIR no existe en web server</p> \n"; };
          next;
        };
        open FILES, ">>$SEARCH_DIR/$RAW_DIRNAME/0000/$FILES_FILENAME.tmp";   # Archivo de articulos.
        open FILESINDEX, ">>$SEARCH_DIR/$RAW_DIRNAME/0000/$FILESINDEX_FILENAME.tmp"; # Archivo indice de articulos.
        open FILESINDEXF, ">>$SEARCH_DIR/$RAW_DIRNAME/0000/$FILESINDEXF_FILENAME.tmp"; # 1.19 Archivo indice de articulos para busqueda por frases.
        if ($INVOCACION eq 'web') { print "<p>Buscando art&iacute;culos...</p> \n"; };
        &busca_articulos_raw("$ROOTDIR$DIR");
        close FILES;
        close FILESINDEX;
        close FILESINDEXF; # 1.19
        $raws_indexados++;
      };
    };
    if ($raws_indexados) {
      # Escribe indices de palabras.
      if ($INVOCACION eq 'web') { print "<p>Escribiendo &iacute;ndices de palabras...</p> \n"; };
      &escribe_palabras("$SEARCH_DIR/$RAW_DIRNAME/0000");
      # Genera cross-index de palabras.
      if ($INVOCACION eq 'web') { print "<p>Escribiendo &iacute;ndices cruzados...</p> \n"; };
      &genera_wordsindex("$SEARCH_DIR/$RAW_DIRNAME/0000");
      # Escribe los archivos definitivos.
      if ($INVOCACION eq 'web') { print "<p>Sustituyendo archivos &iacute;ndice...</p> \n"; };
      move("$SEARCH_DIR/$RAW_DIRNAME/0000/$WORDS_FILENAME.tmp","$SEARCH_DIR/$RAW_DIRNAME/0000/$WORDS_FILENAME");
      move("$SEARCH_DIR/$RAW_DIRNAME/0000/$CARS_FILENAME.tmp","$SEARCH_DIR/$RAW_DIRNAME/0000/$CARS_FILENAME");
      move("$SEARCH_DIR/$RAW_DIRNAME/0000/$FILES_FILENAME.tmp","$SEARCH_DIR/$RAW_DIRNAME/0000/$FILES_FILENAME");
      move("$SEARCH_DIR/$RAW_DIRNAME/0000/$WORDSINDEX_FILENAME.tmp","$SEARCH_DIR/$RAW_DIRNAME/0000/$WORDSINDEX_FILENAME");
      unlink "$SEARCH_DIR/$RAW_DIRNAME/0000/$FILESINDEX_FILENAME.tmp";
      if ($INVOCACION eq 'web') { print "<p>&raquo; FIN de indexaci&oacute;n de raw dirs</p> \n"; };
    };
  };
  # print "\n"; # debug
};

# 1.14 Indexa los URLs en modalidad spider.
# print "URLs:@URL_DIR\n"; # debug
if ($#URL_DIR >= 0) {
  # Los URLs son siempre reindexados, ya que no hay forma de saber a priori si cambiaron o no.
  %WORDS = ();
  $WIDX = 0;   # Indice de palabras.
  $FIDX = 0;   # Indice de archivos.
  # Crea el directorio para este indice.
  &lib_search::crea_dir("$SEARCH_DIR/$URL_DIRNAME/0000");
  unlink "$SEARCH_DIR/$URL_DIRNAME/0000/$FILES_FILENAME.tmp";
  unlink "$SEARCH_DIR/$URL_DIRNAME/0000/$FILESINDEX_FILENAME.tmp";
  foreach my $i (@URL_DIR) {
    if ($INVOCACION eq 'web') { print "<p><b>&raquo; Indexando $i: " .$CFG{"URL_DIR_$i"}. "</b></p> \n"; };
    open FILES, ">>$SEARCH_DIR/$URL_DIRNAME/0000/$FILES_FILENAME.tmp";   # Archivo de articulos.
    open FILESINDEX, ">>$SEARCH_DIR/$URL_DIRNAME/0000/$FILESINDEX_FILENAME.tmp"; # Archivo indice de articulos.
    open FILESINDEXF, ">>$SEARCH_DIR/$URL_DIRNAME/0000/$FILESINDEXF_FILENAME.tmp"; # 1.19 Archivo indice de articulos para busqueda por frases.
    if ($INVOCACION eq 'web') { print "<p>Leyendo p&aacute;ginas...</p> \n<pre>"; };
    $PROFUNDIDAD = 0; # 1.14
    &recursiveSpider($CFG{"URL_DIR_$i"},$CFG{"URL_SCOPE_$i"});
    if ($INVOCACION eq 'web') { print "<\/pre>\n"; };
    close FILES;
    close FILESINDEX;
    close FILESINDEXF; # 1.19
  };
  # Escribe indices de palabras.
  if ($INVOCACION eq 'web') { print "<p>Escribiendo &iacute;ndices de palabras...</p> \n"; };
  &escribe_palabras("$SEARCH_DIR/$URL_DIRNAME/0000");
  # Genera cross-index de palabras.
  if ($INVOCACION eq 'web') { print "<p>Escribiendo &iacute;ndices cruzados...</p> \n"; };
  &genera_wordsindex("$SEARCH_DIR/$URL_DIRNAME/0000");
  # Escribe los archivos definitivos.
  if ($INVOCACION eq 'web') { print "<p>Sustituyendo archivos &iacute;ndice...</p> \n"; };
  move("$SEARCH_DIR/$URL_DIRNAME/0000/$WORDS_FILENAME.tmp","$SEARCH_DIR/$URL_DIRNAME/0000/$WORDS_FILENAME");
  move("$SEARCH_DIR/$URL_DIRNAME/0000/$CARS_FILENAME.tmp","$SEARCH_DIR/$URL_DIRNAME/0000/$CARS_FILENAME");
  move("$SEARCH_DIR/$URL_DIRNAME/0000/$FILES_FILENAME.tmp","$SEARCH_DIR/$URL_DIRNAME/0000/$FILES_FILENAME");
  # 1.19 ??? Investigar por que no se estaba conservando el archivo $FILESINDEX_FILENAME
  move("$SEARCH_DIR/$URL_DIRNAME/0000/$FILESINDEX_FILENAME.tmp","$SEARCH_DIR/$URL_DIRNAME/0000/$FILESINDEX_FILENAME"); # 1.19 ???
  move("$SEARCH_DIR/$URL_DIRNAME/0000/$FILESINDEXF_FILENAME.tmp","$SEARCH_DIR/$URL_DIRNAME/0000/$FILESINDEXF_FILENAME"); # 1.19 ???
  move("$SEARCH_DIR/$URL_DIRNAME/0000/$WORDSINDEX_FILENAME.tmp","$SEARCH_DIR/$URL_DIRNAME/0000/$WORDSINDEX_FILENAME");
  unlink "$SEARCH_DIR/$URL_DIRNAME/0000/$FILESINDEX_FILENAME.tmp";
  unlink "$SEARCH_DIR/$URL_DIRNAME/0000/$FILESINDEXF_FILENAME.tmp"; # 1.19
  if ($INVOCACION eq 'web') { print "<p>&raquo; FIN de indexaci&oacute;n de urls</p> \n"; };
  # print "\n"; # debug
};

if ($INVOCACION eq 'web') {
  print "<p>*** Fin ***</p>\n";
  #print "<a href='#' onclick='parent.Opciones.cerrarColorbox();' style='color:#0099ff;; font-weight:bold; text-decoration:none;'>[Cerrar]</a>\n";
};
# if ($INVOCACION eq 'web') { print "<p>*** Fin ***</p>\n"; };

# Elimina el semaforo.
unlink "$SEARCH_DIR/$SEMAFORO_FILENAME";

# close DEB; # debug

# ###################################################
# Funciones

# ------------------------------------------------------------------------#
# Recorre el directorio de archivos en bruto buscando archivos que indexar.
sub busca_articulos_rawejemplo {
  my($eldir) = $_[0];
  my(@days,$day,$fullpath,@files,$file,$filepath,@webpages,$webpage);

  @files = &lib_search::lee_dir($eldir); # Lee el directorio.

  foreach $file (sort {$b cmp $a} @files) { # 1.10
    next if ( $file =~ /^\./); # Descarta archivos invisibles.
    # print "file = $eldir/$file\n"; # debug
    $fullpath = "$eldir/$file";
    if (-d $fullpath) {
      # Si es un directorio, sige la busqueda de archivos en forma recursiva.
      &busca_articulos_raw($fullpath);
    }elsif (-f $fullpath) {
      # Si es un archivo y la extension coincide con las buscadas, lo indexa.
      next if (! (grep {$file =~ /\.$_$/} @RAW_FILETYPES) );
      # print "fullpath = $fullpath\n"; # debug
      if ($fullpath =~ /^$ROOTDIR(\/.+)$/) { # 1.11 Extrae la parte bajo el rootdir.
        $filepath = $1;
        # Indexa el archivo.
        # print "indexando $filepath...\n"; # debug
        &indexa_raw($fullpath,$filepath);
      };
    };
  };
}; # busca_articulos_rawejemplo

# ------------------------------------------------------------------------#
# 1.14 Rutina que recorre recursivamente un URL de partida, hasta
# detectar todos los URLs dentro del mismo 'scope'.
# El 'scope' es el limite superior de los links para ser recorridos.
# No seran recorridos links que apunten mas arriba, en el sentido de
# organizacion de directorios, que el scope pasado como parametro.
sub recursiveSpider {
  my ($url,$scope) = @_;
  my ($lnk);
  my (@lnk) = &simpleSpider($url,$scope);
  my (@lnk2);
  # Primero recorre todos los links encontrados en esta pagina.
  foreach $lnk (@lnk) {
    # print "lnk=$lnk\n"; # debug
    push @lnk2,&simpleSpider($lnk,$scope);
  };
  # Luego recorre los links encontrados en las paginas recorridas.
  foreach $lnk (@lnk2) {
    # print "lnk2=$lnk\n"; # debug
    $PROFUNDIDAD++;
    if ($PROFUNDIDAD <= 20) { # Limite de recursividad.
      &recursiveSpider($lnk,$scope);
    };
    $PROFUNDIDAD--;
  };
}; # recursiveSpider

# ------------------------------------------------------------------------#
# 1.14 Rutina que indexa un URL y reporta todos los links que encuentra en el.
# El 'scope' es el limite superior de los links para ser recorridos.
# No seran recorridos links que apunten mas arriba, en el sentido de
# organizacion de directorios, que el scope pasado como parametro.
# Nota: no resulta llamar recursivamente a esta rutina, pq el spider se va solo
# por una rama del sitio, cuando lo que conviene es que vaya por capas.
sub simpleSpider {
  my ($url,$scope) = @_;
  my ($host,$path,$file,$params,$lnk,$i,$l,$p);
  my (@lnk) = ();
  # print "Spider: $url\n"; # debug
  return if ($LINKS{$url} ne '');
  $LINKS{$url} = 1;
  # Aborta si se ha llegado el limite de archivos.
  return if ($FIDX > $CFG{'URL_MAXPAGS'});
  my ($titular,$descripcion,$fechap,$texto,$robots,$buffer) = &getHTML($url);
  if ($titular eq '') {  # Si fracaso, no hace nada mas.
    # print "*** FAIL *** $url\n"; # debug
    return;
  };
  # print "$FIDX $url\n"; # debug
  if ($url =~ /http:\/\/([a-z0-9\.\-]+)\/*(\?|$)/i) {
    ($host,$path,$file) = ($1,'','');
  }elsif ($url =~ /http:\/\/([a-z0-9\.\-]+)(\/[a-z0-9\.\-\_\%\@\~\,]+)$/i) {
    ($host,$path,$file) = ($1,'',$2);
  }elsif ($url =~ /http:\/\/([a-z0-9\.\-]+)(\/[a-z0-9\.\-\_\%\@\~\,\/]+)(\/[a-z0-9\.\-\_\%\@\~\,]*)($|\?)/i) {
    ($host,$path,$file) = ($1,$2,$3);
  };
  # print "$FIDX url=[$url] host=[$host] path=[$path] file=[$file]\n"; # debug
  if ($INVOCACION eq 'web') { print "$FIDX prof=[$PROFUNDIDAD] url=[$url]\n"; };

  # Indexa el archivo si no hay instrucciones en contrario.
  &indexa_url($titular,$descripcion,$fechap,$texto,$robots,$url);
  # if ($texto =~ /llaima/is) { print "tiene Llaima: $url\n"; }; # debug

  # Extrae y sigue links si es que no hay instrucciones en contrario.
  return if ($robots =~ /nofollow/i);
  # Extrae y recorre los links.
  # Se define como link cualquier cosa que esta entre comillas
  # y coincide con $URL_FILETYPES_REGEXP
  while ($buffer =~ /([\"\'])([^\"\'\s]+)\1/ig) {
    $lnk = $2;
    if ( ($lnk =~ /($URL_FILETYPES_REGEXP)($|\?)/i)
       && ($lnk =~ /[a-z0-9\/]$/i) && ($lnk =~ /[a-z0-9]/i) ) {
      # print "found link: $lnk"; # debug
      # Arregla links derivados de un refresh.
      $lnk =~ s/\d+;url=(.+)/$1/i;
      # Elimina referencias al directorio actual.
      $lnk =~ s/^\.\/(.+)/$1/i;
      # Si el link "califica", entonces lo recorre tambien.
      if ($lnk =~ /^\//i) {  # Link absoluto.
        $lnk = "http://$host$lnk";
        # print "absoluto: $lnk\n"; # debug
      }elsif ($lnk =~ s/^((\.\.\/)+)//) { # Link relativo.
        $l = length($1) / 3;
        $p = $path;
        for ($i=0;$i<$l;$i++) {
          $p =~ s/\/[^\/]+$//i; # Elimina tantos directorios como ../ hay en el link.
        };
        $lnk = "http:\/\/$host$p/$lnk";
        # print "relativo: $lnk\n"; # debug
      }elsif ($lnk !~ /^http/) { # Link relativo a partir del mismo directorio.
        $lnk = "http://$host$path/$lnk";
        # print "simple: $lnk\n"; # debug
      }; # Si no se cumplio nada de lo anterior, se asume que el link viene con host.
      # Califica si el link esta en un nivel inferior al original.
      if ($lnk =~ /^$scope/) {
        if ($LINKS{$lnk} eq '') {
          $lnk =~ s/(\w)\/\//$1/g; # Elimina doble / para evitar doble indexacion.
          # &simpleSpider($lnk,$scope);
          if ($LINKS{$lnk} eq '') {
            # Solo recuerda links no indexados.
            push @lnk,$lnk;
          };
          # print "<<<";  # debug
        };
      };
      # print "\n";  # debug
    };
  };
  # $buffer = ''; # Libera memoria.
  # foreach $lnk (@lnk) {
  #   $PROFUNDIDAD++;
  #   if ($PROFUNDIDAD <= 20) { # Limite de recursividad.
  #     &simpleSpider($lnk,$scope);
  #   };
  #   $PROFUNDIDAD--;
  # };
  return @lnk;
}; # simpleSpider

# ------------------------------------------------------------------------#
# Genera el indice cruzado de palabras.
sub genera_wordsindex {
  my($dir) = $_[0];
  my($archivo,$palabras,$locations,$numlocations,$widx);
  my(%wordsidx) = ();
  my($numarchivos) = 0;

  # Lee el indice de archivos -> palabras y llena el hash de palabras -> archivos.
  open(FILESINDEX, "<$dir/$FILESINDEX_FILENAME.tmp") || die "No pude abrir el archivo $dir/$FILESINDEX_FILENAME.tmp $!";
  while (<FILESINDEX>) {
    # 12=969 1|3175 1|2595 1|9 1|5708 1|607 1|
    chomp;
    ($archivo,$palabras) = split (/=/,$_);
    while ($palabras =~ /\|(\d+) (\d+)/g) {
      # La palabra esta en este archivo, con frecuencia $2.
      $wordsidx{$1} .= "$archivo $2|";
    };
    $numarchivos++;
    # if ( ($numarchivos % 100) == 0 ) { print $numarchivos . ' '; }; # debug
  };
  close FILESINDEX;
  # Crea limite de palabras no significativas, las cuales seran descartadas.
  $numarchivos = $numarchivos * $CFG{'RATIO'} / 100;

  # Este sera el archivo de ubicacion de palabras (palabras=|archivo veces|...).
  open(WORDSINDEX, ">$dir/$WORDSINDEX_FILENAME.tmp") || die "No pude abrir el archivo $dir/$WORDSINDEX_FILENAME.tmp $!";
  foreach $widx (sort {$a <=> $b} keys %wordsidx) {
    # Descarta palabras muy repetidas.
    $locations = $wordsidx{$widx};
    $numlocations = ($locations =~ s/\|//g);
    if ($numlocations > $numarchivos) { # 1.23.1
      $wordsidx{$widx} = '';
      # print "Descartada la palabra $widx\n"; # debug
    };
    # Escribe el crossindex palabras -> archivos.
    print WORDSINDEX $widx . '=|' . $wordsidx{$widx} . "\n";
  };
  close WORDSINDEX;
  %wordsidx = (); # Libera RAM.

}; # genera_wordsindex

# ------------------------------------------------------------------------#
# Escribe los indices de palabras.
sub escribe_palabras {
  my($dir) = $_[0];
  my($widx,$i,$letra,$letraold,$palabra);
  my(%letras) = ();

  $i = 0;
  $letra = '';
  $letraold = '';
  # Escribe indice de palabras (ordenado alfabeticamente).
  open WORDS, ">$dir/$WORDS_FILENAME.tmp";
  foreach $palabra (sort keys %WORDS) {
    $i++;
    print WORDS $palabra . '=' . $WORDS{$palabra} . "\n";
    $letra = substr($palabra,0,1);
    if ($letra ne $letraold) {
      $letras{$letra} = $i;
      $letraold = $letra;
    };
  };
  close WORDS;
  # Escribe indice de letras.
  open CARS, ">$dir/$CARS_FILENAME.tmp";
  foreach $letra (sort keys %letras) {
    print CARS $letra . '=' . $letras{$letra} . "\n";
  };
  close CARS;
}; # escribe_palabras

# ------------------------------------------------------------------------#
# Recorre el directorio de articulos buscando archivos que indexar.
sub busca_articulos {
  my($eldir) = $_[0];
  my(@days,$day,$fullpath,@files,$file,$ts,$extension,@webpages,$webpage);

  open FILES, ">$SEARCH_DIR$PRONTUS/$ANO/$FILES_FILENAME.tmp";   # Archivo de articulos.
  open FILESINDEX, ">$SEARCH_DIR$PRONTUS/$ANO/$FILESINDEX_FILENAME.tmp"; # Archivo indice de articulos.
  open FILESINDEXF, ">$SEARCH_DIR$PRONTUS/$ANO/$FILESINDEXF_FILENAME.tmp"; # 1.19 Archivo indice de articulos para busqueda por frases.

  # Ordena al reves para busqueda cronologica (los mas antiguos quedan al final del archivo de articulos).
  @days = sort {$b cmp $a} (&lib_search::lee_dir($eldir));
  my $prontusid = $PRONTUS;
  $prontusid=~ s/^\///;
  foreach $day (@days) {
    next if ( $day !~ /^\d{8}$/); # 20050612
    next if ( $day !~ /^$ANO/);   # Solo considera dias del ano en curso.
    # print "day = $day ano = $ANO\n"; # debug
    if ($CFG{'PRONTUS_VER'} > 9) {
      $fullpath = "$eldir/$day/xml";
    }else{
      $fullpath = "$eldir/$day/pags";
    };
    if (-d "$fullpath") {
      # print "fullpath = $fullpath\n"; # debug
      @files = &lib_search::lee_dir($fullpath);
      foreach $file (@files) {
        if ((-f "$fullpath/$file") && ($file =~ /^(\d{14})\.(\w+)$/)) { # Archivos con TS.
          $ts = $1;
          $extension = $2;
          if ($CFG{'PRONTUS_VER'} > 9) {
            # Jamas se indexaran xml por error
            $extension = '';
            # Determina extension del archivo visible por web.
            @webpages = &lib_search::lee_dir("$eldir/$day/pags");
            foreach $webpage (@webpages) {
              if ($webpage =~ /^$ts\.(\w+)$/) {
                $extension = $1;
                last;
              };
            };
          };
          # Indexa el archivo. Solo indexa si el archivo existe
          if($extension) {
            &indexa("$fullpath/$file",$ts,$extension,"$eldir/$day", $prontusid); # 1.9
          };
        };
      };
    };
  };
  close FILES;
  close FILESINDEX;
  close FILESINDEXF; # 1.19
}; # busca_articulos

# ------------------------------------------------------------------------#
# Recorre el directorio de archivos en bruto buscando archivos que indexar.
sub busca_articulos_raw {
  my($eldir) = $_[0];
  my(@days,$day,$fullpath,@files,$file,$filepath,@webpages,$webpage);

  @files = &lib_search::lee_dir($eldir); # Lee el directorio.

  foreach $file (sort {$b cmp $a} @files) { # 1.10
    next if ( $file =~ /^\./); # Descarta archivos invisibles.
    # print "file = $eldir/$file\n"; # debug
    $fullpath = "$eldir/$file";
    if (-d $fullpath) {
      # Si es un directorio, sige la busqueda de archivos en forma recursiva.
      &busca_articulos_raw($fullpath);
    }elsif (-f $fullpath) {
      # Si es un archivo y la extension coincide con las buscadas, lo indexa.
      next if (! (grep {$file =~ /\.$_$/} @RAW_FILETYPES) );
      # print "fullpath = $fullpath\n"; # debug
      if ($fullpath =~ /^$ROOTDIR(\/.+)$/) { # 1.11 Extrae la parte bajo el rootdir.
        $filepath = $1;
        # Indexa el archivo.
        # print "indexando $filepath...\n"; # debug
        &indexa_raw($fullpath,$filepath);
      };
    };
  };
}; # busca_articulos_raw

# ------------------------------------------------------------------------#
# 1.14 Busca palabras de data proveniente de un URL y las mete en los indices correspondientes.
sub indexa_url {
  my($titular,$descripcion,$fechap,$texto,$robots,$url) = @_;
  my(@palabras,%ocurrencias,$palabra,$indice);
  # print "$titular,$descripcion,$texto\n"; # debug
  # No hace nada si el texto no es significativo.
  return if (length($texto) < $CFG{'MINTEXT'});
  # No hace nada si no debe hacer nada.
  return if ($robots =~ /noindex/i);
  # Registra archivo.
  $FIDX++;
  # IDarticulo=fechap|path al archivo|titular|primeras palabras|seccion|tema|subtema
  print FILES "$FIDX=$fechap|$url|$titular||||$descripcion|||\n";
  # Elimina todo lo que no sean caracteres validos.
  $texto =~ s/[^0-9a-z]/ /isg;
  # Separa en palabras.
  @palabras = split(/\s+/,$texto);
  # Registra palabras.
  foreach $palabra (@palabras) {
    # $palabra =~ s/s$//; # Elimina 's' final a palabras para asimilar plurales.
    next if (length($palabra) < 2); # Elimina letras sueltas.
    if ( ! exists $WORDS{$palabra}) {
      $WIDX++; $WORDS{$palabra} = $WIDX;
    };
    $ocurrencias{$palabra}++;
  };
  # Construye indice de palabras dentro de archivos.
  $indice = '';
  foreach $palabra (keys %ocurrencias) {
    # Registra el indice de la palabra y el numero de ocurrencias dentro del archivo.
    $indice .= $WORDS{$palabra} . ' ' . $ocurrencias{$palabra} . '|';
  };
  print FILESINDEX "$FIDX=|$indice\n";
}; # indexa_url

# ------------------------------------------------------------------------#
# Busca palabras dentro del archivo y las mete en los indices correspondientes.
sub indexa_raw {
  my($fullpath,$filepath) = @_;
  my(@palabras,%ocurrencias,%ubicaciones,$palabra,$indice,$indicef,$ipalabra);
  my($titular,$descripcion,$fechap,$texto) = &get_contents_raw(&lib_search::lee_archivo($fullpath),$filepath);
  # print "$titular,$descripcion,$texto\n"; # debug
  # No hace nada si el texto no es significativo.
  return if (length($texto) < $CFG{'MINTEXT'});
  # Registra archivo.
  $FIDX++;
  # IDarticulo=fechap|path al archivo|titular|primeras palabras|seccion|tema|subtema
  print FILES "$FIDX=$fechap|$filepath|$titular||||$descripcion|||\n"; # 1.11
  # Elimina todo lo que no sean caracteres validos.
  $texto =~ s/[^0-9a-z]/ /isg;
  # Separa en palabras.
  @palabras = split(/\s+/,$texto); # 1.8
  # Registra palabras.
  $ipalabra = 0; # 1.19 Indice de la palabra. Usado para la busqueda por frases.
  foreach $palabra (@palabras) {
    # $palabra =~ s/s$//; # Elimina 's' final a palabras para asimilar plurales.
    next if (length($palabra) < 2); # Elimina letras sueltas.
    if ( ! exists $WORDS{$palabra}) {
      $WIDX++; $WORDS{$palabra} = $WIDX;
    };
    $ocurrencias{$palabra}++;
    $ubicaciones{$palabra} += " $ipalabra"; # 1.19
    $ipalabra++; # 1.19
  };
  # Construye indice de palabras dentro de archivos.
  $indice = '';
  $indicef = ''; # 1.19
  foreach $palabra (keys %ocurrencias) {
    # Registra el indice de la palabra y el numero de ocurrencias dentro del archivo.
    $indice .= $WORDS{$palabra} . ' ' . $ocurrencias{$palabra} . '|';
    $indicef .= $WORDS{$palabra} . $ubicaciones{$palabra} . '|'; # 1.19
  };
  print FILESINDEX "$FIDX=|$indice\n";
  print FILESINDEXF "$FIDX=|$indicef\n";
}; # indexa_raw

# ------------------------------------------------------------------------#
# Busca palabras dentro del archivo y las mete en los indices correspondientes.
sub indexa {
  my ($archivo,$ts,$extension,$daypath, $prontus) = @_; # 1.9 $daypath = "$eldir/$day" (site/artic/20070402)
  my (@palabras,%ocurrencias,%ubicaciones,$palabra,$indice,$indicef,$filepath,$dir,$buffer);
  my (@files,$file,$ext,@data2index,$ipalabra); # 1.19
  my($titular,$meta1,$meta2,$meta3,$descripcion,$fechap,$texto,$seccion,$tema,$subtema);
  my @data;

  # 1.9 Busca archivos de data de este articulo que haya que indexar.
  # site/artic/20070402/asocfile/20070402165132
  # $archivo,$ts,$extension,$daypath
  @files = &lib_search::lee_dir("$daypath/asocfile/$ts");
  foreach $file (@files) {
    foreach $ext (keys %FILEFILTER) {
      if ($file =~ /\.$ext$/i) {
        push @data2index,"$daypath/asocfile/$ts/$file";
      };
    };
  };

  $buffer = &lib_search::lee_archivo($archivo); # 1.9
  ($titular,$meta1,$meta2,$meta3,$descripcion,$fechap,$texto,$seccion,$tema,$subtema,@data) = &get_contents($buffer, $prontus);
  # print "$archivo = $titular,$descripcion,$fechap,$texto,$seccion,$tema,$subtema\n"; # debug
  while ($titular ne '') { # 1.9
    # No hace nada si el texto no es significativo.
    if (length($texto) >= $CFG{'MINTEXT'}) {
      # Registra archivo.
      $FIDX++;
      # print DEB "archivo=[$archivo][$FIDX]["; # debug
      # Determina el path relativo al articulo.
      if ( ($CFG{'PRONTUS_VER'} > 9) && ($archivo =~ /\.xml$/) ) { # 1.9
        $dir = substr($ts,0,8);
        $filepath = "$PRONTUS/site/artic/$dir/pags/$ts\.$extension";
      }else{
        # if ($archivo =~ /^$ROOTDIR\/(.+)$/) { # Extrae la parte bajo el rootdir.
        if ($archivo =~ /^$ROOTDIR(.+)$/) { # Extrae la parte bajo el rootdir.
          $filepath = $1;
        };
      };

      # 1.20
      my $strtofile = "$FIDX=$fechap|$filepath|$titular|$meta1|$meta2|$meta3|$descripcion|$seccion|$tema|$subtema";
      for (my $k=0; $k<10;$k++) {
        $strtofile = $strtofile."|$data[$k]";
      };
      $strtofile = $strtofile."\n";
      print FILES $strtofile;

      # Elimina todo lo que no sean caracteres validos.
      $texto =~ s/[^0-9a-z]/ /isg;
      # Separa en palabras.
      @palabras = split(/\s+/,$texto); # 1.8
      # Registra palabras.
      $ipalabra = 0; # 1.19 Indice de la palabra. Usado para la busqueda por frases.
      foreach $palabra (@palabras) {
        # $palabra =~ s/s$//; # Elimina 's' final a palabras para asimilar plurales.
        next if (length($palabra) < 2); # Elimina letras sueltas.
        if ( ! exists $WORDS{$palabra}) {
          $WIDX++; $WORDS{$palabra} = $WIDX;
        };
        $ocurrencias{$palabra}++;
        $ubicaciones{$palabra} .= " $ipalabra"; # 1.19
        $ipalabra++; # 1.19
        # if ($ipalabra < 5) {
        #   print DEB "$WIDX=$palabra "; # debug
        # };
      };
      # print DEB "]\n"; # debug
      # Construye indice de palabras dentro de archivos.
      $indice = '';
      $indicef = ''; # 1.19
      foreach $palabra (keys %ocurrencias) {
        # Registra el indice de la palabra y el numero de ocurrencias dentro del archivo.
        $indice .= $WORDS{$palabra} . ' ' . $ocurrencias{$palabra} . '|';
        $indicef .= $WORDS{$palabra} . $ubicaciones{$palabra} . '|'; # 1.19
      };
      print FILESINDEX "$FIDX=|$indice\n";
      print FILESINDEXF "$FIDX=|$indicef\n";
    };
    # 1.9
    $titular = '';
    $archivo = pop @data2index;
    if ($archivo =~ /\.([^\.]+)$/) {
      $ext = $1;
      if ($archivo ne '') {
        $buffer = qx/$FILEFILTER{$ext} $archivo/;
        ($titular,$descripcion,$texto) = &get_contents_data($buffer);
        # Sobreescribe el titular como el nombre del archivo.
        if ($archivo =~ /\/([^\/]+)$/) {
          $titular = $1;
          $titular =~ s/_/ /g;
          $titular = ucfirst $titular;
        };
      }else{
        last;
      };
    };
  };
}; # indexa

# ---------------------------------------------------------------
# 1.9 Obtiene el contenido de interes de un archivo de datos.
sub get_contents_data {
  my($buffer) = $_[0];
  my($titular,$descripcion,$texto); # Variables de respuesta.
  utf8::decode($buffer); # 1.25
  # Considera como titular las palabras dentro de los primeros 40 caracteres del texto.
  $titular = substr($buffer,0,40);
  $titular =~ s/[^\s]+$//s;
  $titular .= '...';
  # Elimina tags, \n y | dentro del titular.
  $titular =~ s/[\|\n\r\<\>]/ /sg;
  # Obtiene texto significativo.
  $texto = $buffer;
  # Elimina tags que no contienen links ni informacion relevante.
  $texto =~ s/<style.+?<\/style>//sig;   # 1.14 (la 's')
  $texto =~ s/<script.+?<\/script>//sig; # 1.14 (la 's')
  $texto =~ s/<select.+?<\/select>//sig; # 1.14 (la 's')
  # Elimina los links, ya que apuntan a otra parte.
  $texto =~ s/<a .+?<\/a>//ig;
  # Elimina tags del texto;
  # $texto =~ s/<[^>]+>/ /isg;
  # Elimina los espacios excesivos.
  $texto =~ s/\s+/ /g;
  # Toma primeras letras del texto para formar la descripcion.
  $descripcion = substr($texto,0,$CFG{'RESUMEN'});
  # Trunca a una palabra entera antes.
  $descripcion =~ s/[^\s]+$//s;
  $descripcion =~ s/[\|\n\r\<\>]/ /sg; # Elimina | y \n.
  # Reemplaza tildes por letras normales.
  $texto = &lib_search::notildes($texto); # 1.25
  # 1.25 $texto = &lib_search::notildesUtf8($texto); # 1.24
  # Pasa todo el texto a minusculas. # 1.26 Esto antes estaba antes de notildesUtf8.
  $texto = lc $texto;
  # Reemplaza cualquier cosa no caracter por un espacio.
  $texto =~ s/[^0-9a-z]/ /sg;
  # Limita el texto a los primeros n caracteres.
  $texto = substr($texto,0,$CFG{'MAXCARS'});
  utf8::encode($descripcion); # 1.25
  utf8::encode($titular); # 1.25
  return ($titular,$descripcion,$texto);
}; # get_contents_data

# ---------------------------------------------------------------
# Obtiene el contenido de interes de un archivo bruto (raw).
sub get_contents_raw {
  my($buffer,$filepath) = @_; # 1.10
  my($titular,$descripcion,$fechap,$texto,$ano,$mes,$dia); # Variables de respuesta.
  utf8::decode($buffer); # 1.25
  # Si no hay que indexar, no hace nada y retorna todo vacio.
  if ($buffer =~ /<META\s+NAME=\"ROBOTS\"\s+CONTENT=\"NOINDEX\">/is) { return ('','',''); };
  # Obtiene el titular.
  if ($buffer =~ /<!--TITULAR-->(.+?)<!--\/TITULAR-->/is) { # 1.10
    $titular = $1;
  }elsif ($buffer =~ /<h1>(.+?)<\/h1>/is) {
    $titular = $1;
  }elsif ($buffer =~ /<h2>(.+?)<\/h2>/is) {
    $titular = $1;
  }elsif ($buffer =~ /<h3>(.+?)<\/h3>/is) {
    $titular = $1;
  }elsif ($buffer =~ /<title>(.+?)<\/title>/is) {
    $titular = $1;
  }else{
    $titular = 'Sin T&iacute;tulo';
  };
  if ($titular =~ /^\s*$/) { $titular = 'Sin T&iacute;tulo'; }; # 1.14
  # Intenta descubrir una fechap.
  # Formato PX <_FECHAP>20050109</_FECHAP>
  if ($buffer =~ /<_FECHAP>(\d+)<\/_FECHAP>/s) {
    $fechap = $1;
  }elsif ($buffer =~ /<!--FECHAP=(\d+)-->/s) { # <!--FECHAP=20050622-->
    $fechap = $1;
  }elsif ($filepath =~ /(\d{8})/s) { # 1.10
    $fechap = $1;
  }elsif ($filepath =~ /(\d{8})\d{6}/s) { # 1.10
    $fechap = $1;
  };
  # 1.10 Validacion de fechap
  $ano = substr($fechap,0,4);
  $mes = substr($fechap,4,2);
  $dia = substr($fechap,6,2);
  if ( ($ano < 1900) || ($ano > 2010) || ($mes < 1) || ($mes > 12) || ($dia <1) || ($dia > 31) ) {
    $fechap = '';
  };
  # print "fechap=$fechap\n"; # debug
  # Elimina tags, \n y | dentro del titular.
  $titular =~ s/<[^>]+>/ /isg;
  $titular =~ s/[\|\n]/ /sg;
  # Obtiene texto significativo. <!--TEXTarticulo-->
  if ($buffer =~ /<!--TEXTarticulo-->(.+?)<!--\/TEXTarticulo-->/is) { # 1.10
    $texto = $1;
  }elsif ($buffer =~ /<body.+?<\/body>/is) { # Bodys cortos.
    $texto = $&;
  }elsif ($buffer =~ /<body.+/is) { # Bodys largos o mal formados.
    $texto = $&;
  };
  # Elimina tags que no contienen links ni informacion relevante.
  $texto =~ s/<style.+?<\/style>//sig;   # 1.14 (la 's')
  $texto =~ s/<script.+?<\/script>//sig; # 1.14 (la 's')
  $texto =~ s/<select.+?<\/select>//sig; # 1.14 (la 's')
  # Elimina los links, ya que apuntan a otra parte.
  $texto =~ s/<a .+?<\/a>//ig;
  # Elimina tags del texto;
  $texto =~ s/<[^>]+>/ /isg;
  # Elimina los espacios excesivos.
  $texto =~ s/&nbsp;/ /g;
  $texto =~ s/\s+/ /g;
  # Toma primeras letras del texto para formar la descripcion.
  $descripcion = substr($texto,0,$CFG{'RESUMEN'});
  # Trunca a una palabra entera antes.
  $descripcion =~ s/[\&\w;#\x{c3a1}\x{c3a9}\x{c3ad}\x{c3b3}\x{c3ba}\x{c381}\x{c389}\x{c38d}\x{c393}\x{c39a}\x{c3b1}\x{c391}\x{c3bc}\x{c39c}]+$//s;
  $descripcion =~ s/[\|\n]/ /sg; # Elimina | y \n.
  # Concatena el titular al texto para construir el indice.
  $texto = "$titular $texto";
  # Elimina los retornos de carro y los tabuladores.
  $texto =~ s/[\r\n\t]/ /g;
  # Elimina los espacios excesivos (otra vez).
  $texto =~ s/&nbsp;/ /g;
  $texto =~ s/\s+/ /g;
  # Reemplaza tildes por letras normales.
  # 1.24 $texto = &lib_search::notildes($texto);
  $texto = &lib_search::notildes($texto); # 1.24 # 1.25
  # Pasa todo el texto a minusculas. # 1.25 Esto antes estaba antes de notildesUtf8.
  $texto = lc $texto;
  # Reemplaza cualquier cosa no caracter por un espacio.
  $texto =~ s/[^0-9a-z]/ /sg;
  # Limita el texto a los primeros n caracteres.
  $texto = substr($texto,0,$CFG{'MAXCARS'});
  utf8::encode($titular); # 1.25
  utf8::encode($descripcion); # 1.25
  return ($titular,$descripcion,$fechap,$texto);
}; # get_contents_raw

# ---------------------------------------------------------------
# Obtiene el contenido de interes de la pagina recien leida.
sub get_contents {
  my($buffer) = shift;
  my($prontus) = shift;
  my($titular,$meta1,$meta2,$meta3,$descripcion,$fechap,$texto,$seccion,$tema,$subtema); # 1.7 Variables de respuesta.
  my(@metadata, @metadata_var);
  my($var,$tipoficha,$k);
  my($horap) = '0000';
  my($fechae) = '99999999';
  my($horae) = '0000';
  my($alta) = 1; # por defecto asume que el articulo esta de alta.
  my($title_var) = $CFG{'TITLEVAR'};
  my($meta1_var) = $CFG{'META1'}; # 1.7
  my($meta2_var) = $CFG{'META2'}; # 1.7
  my($meta3_var) = $CFG{'META3'}; # 1.7
  for($k=0;$k<10;$k++) {
    # $metadata_var[$k]=$CFG{'METADATA'.$k};
    $metadata_var[$k]=$CFG{'METADATA'.($k+1)}; # 1.23.3
  }
  my(@textvars) = split(/\s+/,$CFG{'TEXTVARS'}); # 1.8
  my(@tiposficha) = split(/\s+/,$CFG{'FIDS'}); # 1.8
  # Obtiene el titular, fechap y texto significativo.
  # print "\nEn get_contents " . $CFG{'PRONTUS_VER'}; # debug

  # <_ALTA>1</_ALTA>
  if ($buffer =~ /<_ALTA>(.*?)<\/_ALTA>/is) { # 1.20
    $alta = $1;
  };
  # print "alta=$alta "; # debug
  return if ($alta != 1); # Si no esta en alta, retorna todo vacio.
  # <_TIPO_FICHA>fid_rotulo.html</_TIPO_FICHA>
  if ($buffer =~ /<_FID>(.+?)<\/_FID>/is) { # 1.18
    $tipoficha = $1;
  };
  # print "tipoficha=$tipoficha "; # debug
  return if ( ! (grep {$_ eq $tipoficha} @tiposficha)); # Si el tipo de ficha no corresponde, retorna.
  # <_FECHAP>20050109</_FECHAP>
  if ($buffer =~ /<_FECHAP>(\d+)<\/_FECHAP>/is) {
    $fechap = $1;
  };
  # print "fechap=$fechap $FECHAACTUAL "; # debug
  # 1.23.1 Obtiene la horap, fechae y horae y compara.
  if ($buffer =~ /<_horap>(.*?)<\/_horap>/is) {
    $horap = $1;
    $horap =~ s/[^0-9]//g; # Elimina separador de elementos.
  };
  # 1.26 Solo considera fechae y horae si NO esta <_soloportadas>1</_soloportadas>.
  if ($buffer !~ /<_soloportadas>1<\/_soloportadas>/is) {
    if ($buffer =~ /<_fechae>(\d+)<\/_fechae>/is) {
      $fechae = $1;
    };
    if ($buffer =~ /<_horae>(.*?)<\/_horae>/is) {
      $horae = $1;
      $horae =~ s/[^0-9]//g; # Elimina separador de elementos.
    };
  };
  # Retorna vacio si la fecha del articulo es posterior a hoy.
  # No es necesario recortar $FECHAHORAACTUAL a los minutos, pq la comparacion gt es caracter por caracter.
  return if ( ($fechap.$horap) gt $FECHAHORAACTUAL );
  return if ( ($fechae.$horae) lt $FECHAHORAACTUAL );
  # <_TXT_TITULAR>
  # <![CDATA[xxx]]>
  # </_TXT_TITULAR>
  if ($buffer =~ /<$title_var>\s*<!\[CDATA\[(.+?)\]\]>\s*<\/$title_var>/is) { # 1.3
    $titular = $1;
  }elsif ($buffer =~ /<$title_var>\s*(.+?)\s*<\/$title_var>/is) { # 1.23.4 Busca titular sin CDATA.
    $titular = $1;
  }else{
    $titular = 'Sin T&iacute;tulo';
  };
  # META1
  if ($buffer =~ /<$meta1_var>\s*<!\[CDATA\[(.+?)\]\]>\s*<\/$meta1_var>/is) { # 1.7
    $meta1 = $1;
  }elsif ($buffer =~ /<$meta1_var>(.+?)<\/$meta1_var>/is) { # 1.7
    $meta1 = $1;
  };
  # META2
  if ($buffer =~ /<$meta2_var>\s*<!\[CDATA\[(.+?)\]\]>\s*<\/$meta2_var>/is) { # 1.7
    $meta2 = $1;
  }elsif ($buffer =~ /<$meta2_var>(.+?)<\/$meta2_var>/is) { # 1.7
    $meta2 = $1;
  };
  # META3
  if ($buffer =~ /<$meta3_var>\s*<!\[CDATA\[(.+?)\]\]>\s*<\/$meta3_var>/is) { # 1.7
    $meta3 = $1;
  }elsif ($buffer =~ /<$meta3_var>(.+?)<\/$meta3_var>/is) { # 1.7
    $meta3 = $1;
  };
  # 1.23.4 Estripea retornos de carro.
  $meta1 =~ s/[\n\r]/ /sg;
  $meta2 =~ s/[\n\r]/ /sg;
  $meta3 =~ s/[\n\r]/ /sg;
  # METADATAk
  for($k=0;$k<10;$k++) {
    my $mdata = $metadata_var[$k];
    next unless($mdata);
    if($mdata eq '_prontus_id') {
      $metadata[$k] = $prontus;
      next;
    }
    if ($buffer =~ /<$mdata>\s*<!\[CDATA\[(.*?)\]\]>\s*<\/$mdata>/is) {
      $metadata[$k] = $1;
    }elsif ($buffer =~ /<$mdata>.*?<!\[CDATA\[(.*?)\]\]>(.*?)<\/$mdata>/is) {
      $metadata[$k] = $1;
    }elsif ($buffer =~ /<$mdata>(.+?)<\/$mdata>/is) {
      $metadata[$k] = $1;
    }else{
      $metadata[$k] = '';
    };
     # 1.23.4 Estripea retornos de carro.
    $metadata[$k] =~ s/[\n\r]/ /sg;
  };

  foreach $var (@textvars) {
    if ($buffer =~ /<$var>\s*<!\[CDATA\[(.+?)\]\]>\s*<\/$var>/is) { # 1.3
      $texto .= " $1"; # 1.16
    }elsif ($buffer =~ /<$var>\s*(.+?)\s*<\/$var>/is) { # 1.23.2
      $texto .= " $1";
    };
  };
  # <_NOM_SECCION1>...</_NOM_SECCION1>
  if ($buffer =~ /<_NOM_SECCION1>([^<]+)<\/_NOM_SECCION1>/is) {
    $seccion = $1;
  };
  # <_NOM_TEMA1>...</_NOM_TEMA1>
  if ($buffer =~ /<_NOM_TEMA1>([^<]+)<\/_NOM_TEMA1>/is) {
    $tema = $1;
  };
  # <_NOM_SUBTEMA1>...</_NOM_SUBTEMA1>
  if ($buffer =~ /<_NOM_SUBTEMA1>([^<]+)<\/_NOM_SUBTEMA1>/is) {
    $subtema = $1;
  };

  utf8::decode($titular); # 1.25
  utf8::decode($texto); # 1.25
  # Elimina tags, \n y | del titular.
  $titular =~ s/<[^>]+>/ /isg;
  $titular =~ s/[\|\n]/ /sg;
  # Elimina tags del texto;
  $texto =~ s/<[^>]+>/ /isg;
  # Elimina los espacios excesivos.
  $texto =~ s/&nbsp;/ /g;
  $texto =~ s/\s+/ /g;
  # Toma primeras letras del texto para formar la descripcion.
  $descripcion = substr($texto,0,$CFG{'RESUMEN'});
  if (length($texto) > $CFG{'RESUMEN'}) { # 1.23.4 Solo trunca el resumen si es necesario.
    # Trunca a una palabra entera antes.
    $descripcion =~ s/[\&\w;#\xe1\xe9\xed\xf3\xfa\xc1\xc9\xcd\xd3\xda\xf1\xd1\xfc\xdc]+$//s; # 1.25
    # $descripcion =~ s/[\&\w;#\x{c3a1}\x{c3a9}\x{c3ad}\x{c3b3}\x{c3ba}\x{c381}\x{c389}\x{c38d}\x{c393}\x{c39a}\x{c3b1}\x{c391}\x{c3bc}\x{c39c}]+$//s;
    $descripcion =~ s/[\|\n]/ /sg; # Elimina | y \n.
  };
  # Concatena el titular al texto para construir el indice.
  $texto = "$titular $texto";
  # Elimina los retornos de carro y los tabuladores.
  $texto =~ s/[\r\n\t]/ /g;
  # Elimina los espacios excesivos (otra vez).
  $texto =~ s/&nbsp;/ /g;
  $texto =~ s/\s+/ /g;
  # Reemplaza tildes por letras normales.
  # 1.24 $texto = &lib_search::notildes($texto);
  $texto = &lib_search::notildes($texto); # 1.24 # 1.25
  # Pasa todo el texto a minusculas. # 1.25 Esto antes estaba antes de notildesUtf8.
  $texto = lc $texto;
  # Reemplaza cualquier cosa no caracter por un espacio.
  $texto =~ s/[^0-9a-z]/ /sg;
  # Limita el texto a los primeros n caracteres.
  $texto = substr($texto,0,$CFG{'MAXCARS'});
  utf8::encode($titular); # 1.25
  utf8::encode($texto); # 1.25
  utf8::encode($descripcion); # 1.25
  return ($titular,$meta1,$meta2,$meta3,$descripcion,$fechap,$texto,$seccion,$tema,$subtema,@metadata); # 1.7
}; # get_contents

# ------------------------------------------------------------------------#
# Recorre el directorio de articulos determinando los anos que existen.
# Tambien determina la fecha de modificacion mas reciente de los archivos
# contenidos en el.
# Si se esta forzando un reindexado, no hace nada mas que simular que el
# indice de ese ano expiro.
sub busca_anos {
  my($dir) = $_[0];
  my(@days);
  my($ano,$day,$maxtime);
  @days = &lib_search::lee_dir($dir);
  foreach $day (@days) {
    next if ($day !~ /^\d{8}$/); # 20050612
    if ( $day =~ /^(\d{4})/) {
      $ano = $1;
      if ($FORZAR ne $PRONTUS) { # Variables globales, sorry.
        $maxtime = &maxtime("$dir/$day/pags");
      }else{
        # 1.26 $maxtime = 0; # Con esto fuerza el reindexado de estos anos.
        $maxtime = 1; # Con esto fuerza el reindexado de estos anos.
      };
      if ($ANOS{$ano} < $maxtime) {
        # my $mtime = (stat("$SEARCH_DIR$PRONTUS/$ano/$WORDSINDEX_FILENAME"))[9]; # debug
        # print "day=$day mtime=$mtime maxtime=$maxtime\n"; # debug
        $ANOS{$ano} = $maxtime;
      };
    };
  };
}; # busca_anos

# ------------------------------------------------------------------------#
# Detecta el archivo mas reciente de la coleccion de directorios dado
# y retorna su antiguedad en segundos.
sub maxtime {
  my($dir) = $_[0];
  my(@files) = &lib_search::lee_dir($dir);
  my($file,$maxtime,$mtime) = ('',0,0);
  foreach $file (@files) {
    next if ($file =~ /^\./);
    if (-f "$dir/$file") {
      #  (0: $dev, 1: $ino, 2: $mode, 3: $nlink, 4: $uid, 5: $gid, 6: $rdev, 7: $size, 8: $atime, 9: $mtime, 10: $ctime, 11: $blksize, 12: $blocks)
      $mtime = (stat "$dir/$file")[9];
      if ( $maxtime < $mtime  ) { $maxtime = $mtime; };
    }elsif (-d "$dir/$file") {
      $mtime = &maxtime("$dir/$file");
      if ( $maxtime < $mtime  ) { $maxtime = $mtime; };
    };
  };
  return $maxtime;
}; # maxtime

# ------------------------------------------------------------------------#
# Valida las variables del archivo de configuracion.
sub validacfg {
  my($ext,@ext,$key,$filtro);
  if ($CFG{'URL_MAXPAGS'} eq '') { $CFG{'URL_MAXPAGS'} = 2000; }; # 1.14
  if ($CFG{'FIDS'} eq '') { $CFG{'FIDS'} = 'fid_general'; }; # 1.23.1
  $CFG{'FIDS'} =~ s/\.\w+( |$)/ /g; # 1.23.1 Elimina extensiones si las trae.
  # 1.8 $CFG{'FIDS'} =~ s/  //g;
  if ($CFG{'RESUMEN'} < 0) { $CFG{'RESUMEN'} = 100; };
  if ($CFG{'RESUMEN'} > 400) { $CFG{'RESUMEN'} = 400; };
  if ($CFG{'MAXCARS'} < 10000) { $CFG{'MAXCARS'} = 10000; };
  if ($CFG{'RATIO'} < 10) { $CFG{'RATIO'} = 10; };
  if ($CFG{'RATIO'} > 100) { $CFG{'RATIO'} = 100; };
  if ($CFG{'MINTEXT'} < 0) { $CFG{'MINTEXT'} = 20; };
  if ($CFG{'TITLEVAR'} eq '') { $CFG{'TITLEVAR'} = '_TXT_TITULAR'; };
  if ($CFG{'TEXTVARS'} eq '') { $CFG{'TEXTVARS'} = 'TXT_bajada'; };
  if ($CFG{'PRONTUS_VER'} eq '') { $CFG{'PRONTUS_VER'} = 10; };
  @ext = split(/\s+/,$CFG{'RAW_FILETYPES'}); # 1.8
  foreach $ext (@ext) {
    $ext =~ s/[^a-zA-Z0-9]//g;
    if ($ext ne '') { push @RAW_FILETYPES, $ext; };
  };
  @ext = split(/\s+/,$CFG{'URL_FILETYPES'}); # 1.14
  foreach $ext (@ext) {
    $ext =~ s/[^a-zA-Z0-9]//g;
    $URL_FILETYPES_REGEXP .= "\.$ext|";
  };
  # 1.14 $URL_FILETYPES_REGEXP .= '\/';
  $URL_FILETYPES_REGEXP .= '\/|\/[\w\-]+';
  # 1.9 Obtiene definicion de filtros para archivos de datos.
  foreach $key (keys %CFG) {
    if ($key =~ /^FILEFILTER/) {
      # FILEFILTER1 pdf /cgi-cpn/pdftotext.sh
      ($ext,$filtro) = split(/\s+/,$CFG{$key});
      if ( ($ext =~ /^\w+$/) && (-f "$ROOTDIR$filtro") ) {
        # Inscribe el filtro en el hash de filtros.
        $FILEFILTER{$ext} = "$ROOTDIR$filtro";
      };
    };
  };
}; # validacfg

# ------------------------------------------------------------------------#
# Detecta los Prontus que hay que indexar.
sub detectadirs {
  foreach my $key (keys %CFG) {
    if ($key =~ /PRONTUS_DIR_\d+/) {
      push @PRONTUS_DIR,$CFG{$key};
      # print 'Hay que indexar:' . $CFG{$key} . "\n"; # debug
    };
    if ($key =~ /RAW_DIR_\d+/) {
      push @RAW_DIR,$CFG{$key};
      # print 'Hay que indexar:' . $CFG{$key} . "\n"; # debug
    };
    if ($key =~ /URL_DIR_(\d+)/) {
      push @URL_DIR,$1;
      # print 'Hay que indexar:' . $CFG{$key} . " $1\n"; # debug
    };
    # print "KEY[$key] - DATA[$CFG{$key}]" .  "<BR>"; # debug
  };
}; # detectadirs

# -------------------------------------------------------------------#
# 1.4 Rescata y valida las variables del chorro.
sub getFormData {
  my($pair,$buffer);
  if ($ENV{'REQUEST_METHOD'} eq 'GET') {
    $buffer = $ENV{'QUERY_STRING'};
  }else{
    read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
  };
  my(@pairs) = split(/&/, $buffer);
  foreach $pair (@pairs) {
    my($name, $value) = split(/=/,$pair);
    # Un-Webify plus signs and %-encoding
    $value =~ tr/+/ /;
    $value =~ s/%([0-9A-Ha-h]{2})/pack("c",hex($1))/ge;
    $value =~ s/~!/ ~!/g;
    $value =~ s/\.\.\///g; # 1.5 Elimina toda referencia de directorios hacia atras.
    $value =~ s/\|//g;     # 1.5 Elimina toda posibilidad de activar pipes.
    $value =~ s/\x00//g;   # 1.5 Elimina nulls.
    $value =~ s/\x1B//g;   # 1.5 Elimina escapes.
    $FORM{$name} = $value;
    # print "<p>$name $value"; # debug
  };
}; # getFormData

# ---------------------------------------------------------------
# Lee y retorna la pagina web pasada como parametro.
sub getHTML {
  my ($url) = $_[0];
  my ($buffer) = '';
  my ($titular,$descripcion,$fechap,$texto,$robots) = ('','','','','');
  my ($ua) = new LWP::UserAgent;
  $ua->agent('Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.0.04506; InfoPath.2)'); # El browser de los ineptos.
  $ua->max_size(100000); # Pone este limite para no eternizar la cosa.
  my ($request) = new HTTP::Request('GET', $url);
  my ($response) = $ua->request($request);
  if ($response->is_success) {
    $buffer = $response->content;
    # print "$buffer\n"; # debug
    # Detecta metas "robots".
    # <meta name="robots" content="nofollow">
    while ($buffer =~ /<meta\s+name=\"robots\"\s+content=\"([^\"]+)\">/isg) {
      $robots .= " $1";
    };
    ($titular,$descripcion,$fechap,$texto) = &get_contents_raw($buffer,$url);
  };
  return ($titular,$descripcion,$fechap,$texto,$robots,$buffer);
}; # getHTML.
