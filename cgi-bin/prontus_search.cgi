#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Buscar palabras dentro de los indices generados por prontus_index.
# Puede buscar por una o mas palabras, descartar resultados que contengan
# palabra determinadas y buscar con comodines.
# Los resultados aparecen en orden cronologico o por relevancia.
# Para orden cronologico se requiere que los indices sean Prontus.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# El buscador lee los archivos indice de los directorios cpan/data/search/<dir>/aaaa/
# Donde <dir> es un directorio Prontus o el indice de directorios brutos (raw).
#
# Los archivos de indice son:
#
# words.idx      - Indice de palabras.
#   Formato: Palabra=ID. Ordenado por palabras.
#
# cars.idx       - Indice alfabetico de primeros caracteres de palabras.
#   Formato: Letra=Offset.
#
# files.idx      - Indice de articulos.
#   Formato:
#   IDarticulo=fechap|TS.extension|titular|meta1|meta2|meta3|resumen|seccion|tema|subtema
#   seccion, tema y subtema van en texto; no en IDs.
#   fechap, seccion, tema y subtema son nulos si el indice no es Prontus (directorio raw).
#
# wordsindex.idx - Indice de palabras y los articulos que las contienen.
#   Formato:
#   IDpalabra=|IDarticulo count|IDarticulo count|IDarticulo count|IDarticulo count|...
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cgi, usando metodo GET o POST. Los parametros son:
# search_prontus  - Nombre del directorio Prontus donde residen los indices.
# search_comodines - Si es 'yes', permite la busqueda usando las wildcards * y ?.
# search_idx      - Indice donde buscar. Puede ser 'ALL', en cuyo caso se busca en todos.
# search_tmp      - Nombre de la plantilla de busqueda.
#                   Las plantillas se toman de /<search_prontus>/plantillas/extra/search/pags
#                   Si no viene este parametro se asume search.html.
# search_resxpag  - Resultados por pagina. Si no viene este parametro se asume 20.
# search_maxpags  - Maximo de paginas de resultados a mostrar. Si no viene este parametro se asume 20.
# search_texto    - Texto a buscar. Este texto es validado y convertido en un conjunto de palabras.
# search_pag      - Pagina a mostrar. Si no viene, se muestra la primera pagina.
# search_orden    - Orden de los resultados (CRO o REL). Si no viene, se ordena cronologico.
# search_form     - Mostrar formulario (0 o 1). Si no viene, el formulario se muestra.
# search_modo     - Hacer AND u OR con las palabras ingresadas (por defecto hace OR).
# search_meta1    - Variable META1, definida en el archivo de configuracion.
# search_meta2    - Variable META2, definida en el archivo de configuracion.
# search_meta3    - Variable META3, definida en el archivo de configuracion.
# search_seccion  - Seccion a mostrar. Si no viene, se muestran todas.
# search_tema     - Tema a mostrar. Si no viene, se muestran todos.
# search_subtema  - Subtema a mostrar. Si no viene, se muestran todos.
# search_fechaini - Fecha de inicio. Si no viene, no se filtra por fecha.
# search_fechafin - Fecha de termino. Si no viene, no se filtra por fecha.
#
# Si el buscador se invoca con solo el parametro search_prontus, se muestra
# la plantilla de busqueda con el formulario visible.
#
# En plataforma Unix se valida que no existan mas de 5 procesos
# de busqueda corriendo en forma simultanea.
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# Se utiliza la plantilla indicada en la invocacion:
# search_tmp = search.html
#
# En base a esta plantilla se construye la pagina de respuesta, que es escrita
# en el directorio:
# /<directorio prontus>/site/cache/search/pags
# El browser se dirige para que lea esa pagina a traves de un header Location.
#
# Las marcas reconocidas son las siguientes:
#
#   <!--formulario--> Delimitador del formulario de búsqueda.
#                     Esta parte de la plantilla es omitida si
#                     el buscador se invoca con el parametro
#                     search_form=0. Es conveniente que siempre exista,
#                     ya que asi se pueden hacer pruebas desde el
#                     administrador.
#     %%scriptname%%  URL de la cgi que se esta invocando. Usado en la pagina de prueba.
#     %%search_form%% Variable que regula si se muestra o no el formulario.
#   <!--/formulario-->
#   <!--separador-->  Separador de la parte fija de la respuesta, usado para
#                     comenzar a entregar la pagina de resultados con rapidez,
#                     evitando asi el doble click.
#     %%msg%%         Mensaje de contexto. P. ej. "50 resultados en orden de importancia." o "No hay resultados.".
#     %%msgsn%%       Mismo mensaje, pero sin referencia a numeros (1.7).
#   <!--resloop--> Trozo de URL que se repite para cada respuesta.
#     %%num%%         Numero ordinal del articulo encontrado.
#     %%rel%%%        % de relevancia relativa.
#     %%lnk%%         URL del articulo.
#     %%tit%%         Titular del articulo.
#     %%fec%%         Fecha de publicacion del articulo.
#     %%res%%         Resumen (primeras palabras) del articulo.
#     %%meta1%%       Variable META1 definida en el cfg.
#     %%meta2%%       Variable META2 definida en el cfg.
#     %%meta3%%       Variable META3 definida en el cfg.
#     %%sec%%         Seccion del articulo.
#     %%tem%%         Tema del articulo.
#     %%sub%%         Subtema del articulo.
#     %%metadatai%%   Variable METADATAi definida en el cfg (i = 1..10).
#     %%if(<var>)%%   Contenido condicionado a la existencia de la variable <var>.
#     %%/if%%
#   <!--/resloop-->
#   <!--pags-->       Delimitador de los links a las distintas
#                     páginas de resultados.
#                     Si la cantidad de resultados es menor que search_resxpag,
#                     esta parte de la plantilla es omitida.
#     %%pags%%        Links hacia otras páginas para buscar.
#   <!--/pags-->
#
# Ademas en esta plantilla se definen los mensajes que entregara el buscador mediante
# comentarios html, de la forma:
#   <!-- STOPWORDS = to,the,an,in,of -->
#   <!-- MSG server_busy = The server is currently busy. Please try again later ... -->
#   <!-- MSG no_results = No pages containing your search terms were found. -->
#   <!-- MSG order_cron = by date. -->
#   <!-- MSG order_rel = by relevance. -->
#   <!-- MSG results = Results  -->
#   <!-- MSG to = to  -->
#   <!-- MSG of = of -->
#
#
# ---------------------------------------------------------------

# 1.0 - 02/07/2005 - Primera version.
# 1.1 - 14/07/2005 - Agrega soporte para busqueda en multiples indices, incluyendo el indice raw.
# 1.2 - 21/07/2005 - Corrige nomenclatura para asimilar mejor a Prontus.
# 1.3 - 27/07/2005 - Corrige algunos bugs.
# 1.4 - 11/08/2005 - Parche de seguridad para impedir lectura de archivos del sistema.
# 1.5 - 15/09/2005 - YCH - Modifica bloque BEGIN.
#                        - Ahora search_prontus viene con ruta relativa al document root, ej: /prontus_noticias
# 1.7 - 18/04/2006 - ALD - Agrega variables de perfilacion genericas META1, META2 y META3
#                          (solo para Prontus 10 o superior).
# 1.8 - 05/12/2006 - ALD - Agrega rutina para busqueda binaria.
#                        - Elimina ruta relativa, ya que producia errores.
#                        - Robustece parseo de variables.
# 1.9 - 17/01/2007 - ALD - Estripea caracteres peligrosos del parametro search_texto
# 1.10  03/04/2007 - ALD - Modifica la forma de leer las platillas:
#                          Ahora se leen directamente del filesystem y los resultados
#                          se entregan en una pagina temporal, especial para cada visitante.
#                          Estos archivos quedan donde mismo queda actualmente el cache de la plantilla:
#                          /<prontus>/site/cache/search/pags/
# 1.12  10/04/2007 - ALD - Parsea la extension del archivo en los resultados, para permitir su identificacion.
#       03/09/2007 - ALD - Adapta para IIS.
# 1.13  18/07/2007 - ALD - Aplica a las paginas 'ver mas' el mismo script que se invoco.
#                        - Valida que haya solo una o mas letras al chequear selects o checks.
# 1.14  09/10/2007 - ALD - Elimina articulos y conjunciones de las busquedas.
# 1.15  18/10/2007 - YCH - Parametriza cgi-bin
# 1.16  18/10/2007 - YCH - Determina DIR_SERVER usando funcion Prontus
# 1.17  06/10/2007 - YCH - Proteccion contra %00
# 1.18  23/11/2007 - ALD - Aplica validacion extrema de parametros.
#                    ALD - Ahiere a estandar multivista.
#                    ALD - Permite la inclusion de mensajes dentro de la plantilla.
#                    ALD - Organiza stop-words dentro de la plantilla.
# 1.19  07/12/2007 - ALD - Detalles varios.
# 1.20  04/01/2008 - ALD - Valida mejor el nombre del Prontus (search_prontus).
# 1.21  07/01/2008 - ALD - Valida que exista el directorio Prontus validando que exista el archivo de CFG,
#                          ya que si no comienzan a crearse indiscriminadamente.
#                        - Parametriza el nombre de la CGI de invocacion.
# 1.22  12/03/2008 - ALD - Agrega rutina get_dir_server a lib_search para bajar acoplamiento con Prontus.
#                        - Elimina prontus_varglb como requisito.
#                        - Incorpora variable $DEBUG para activar el modo debug.
#                        - Cambia PRONTUS_MAXEXEC por SEARCH_MAXEXEC (bug).
#                        - Activa uso de RESPERPAG y MAXPAGS (bug).
# 1.23  07/05/2008 - ALD - Arregla bug en filtraresultado.
# 1.24  01/07/2008 - ALD - Busca por frases, reconocidas porque se ingresan entre comillas.
# 1.25  05/08/2008 - ALD - Corrige bug en el rotulo de los resultados.
#                        - Genera tags compatibles con xhtml checked="checked" y selected="selected"
# 1.26  02/01/2009 - ALD - Corrige bug en numeros de pagina cuando hay multivista.
# 1.27  12/02/2009 - ALD - Aplica friendly URLs.
# 1.27.1  13/07/2009 CVI - Se corrige comportamiento con RESPERPAG y MAXPAGS.
# 1.27.2  04/09/2009 ALD - Ordena alfabeticamente los indices si son varios.
#                        - Define maximos absolutos para RESPERPAG y MAXPAGS.
#                        - Separa palabras compuestas por guiones para no buscarlas como una sola palabra,
#                          ya que el indexador no las considera como una sola palabra.
#                        - Usa friendly URLs solo si la variable de CFG USEFRIENDLYURLS es 1.
#                        - Verifica que archivos existen antes de abrirlo.
#                        - Implementa parseo de metadata en pagina de resultados.
# 1.28  16/12/2010   ALD - Pasa a UTF-8
# 1.29  21/01/2010   YCC - Ahora utiliza lib_maxrunning::myselfRunning() en lugar de lib_search::myself_running()
# 1.30 28/09/2012    JOR - Lectura de cfg de prontus y uso de parse_filef para friendly url en vez de funcion propia en lib_search.
# 1.31 11/10/2012    ALD - Detecta si se encuentra bajo NGINX para entregar el header X-Accel-Redirect en lugar de Location.

# -------------------------------BEGIN SCRIPT--------------------
BEGIN {
  # dir_cgi.pm trae algo como:
  # $DIR_CGI_CPAN = 'cgi-cpn';
  # $DIR_CGI_PUBLIC = 'cgi-bin'; # 1.15
  use vars qw($DIR_CGI_CPAN $DIR_CGI_PUBLIC); # para que queden disponibles como vars. globales
  require 'dir_cgi.pm';
  
  my ($ROOTDIR) = '';  # 1.12 desde el web
  if ($ENV{'DOCUMENT_ROOT'} ne '') {
    $ROOTDIR = $ENV{'DOCUMENT_ROOT'};
  }elsif ($ENV{'PATH_TRANSLATED'} ne '') {
    $ROOTDIR = $ENV{'PATH_TRANSLATED'};
  };
  $ROOTDIR .= '/' . $DIR_CGI_CPAN;
  unshift(@INC,$ROOTDIR); # Para dejar disponibles las librerias
};

# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

use strict;
# 1.22 use prontus_varglb; &prontus_varglb::init(); # 1.16
use lib_search;
use lib_maxrunning;
use lib_prontus;
use prontus_varglb; &prontus_varglb::init();

# Para mostrar de inmediato la pagina de resultados.
$|=1;
# 1.10 Una sola \n porque despues normalmente viene un header location.
print "Content-type: text/html\n";

# 1.12 Deteccion de la raiz del sitio web.
my $DOCUMENT_ROOT = &lib_search::get_dir_server(); # 1.22 $prontus_varglb::DIR_SERVER; # 1.16

my %FORM;        # Contenido del formulario de invocacion.
my %CFG;         # Variables del archivo de configuracion.
my %RESULTADOS;  # Hash de resultados de la busqueda (archivos y cuenta dentro de ellos).
my @RESULTADOS;  # Arreglo de resultados (ano e indice de archivo).
my %NUMRESULT;   # Hash del numero de palabras encontradas en cada resultado.
my %FECHAP;      # Fechas de publicacion de los resultados encontrados.
my %FILEDATA;    # Datos de cada archivo encontrado (fechap|TS.extension|titular|meta1|meta2|meta3|resumen|seccion|tema|subtema).
my $RESULTADOSTOTALES; # Total de resultados encontrados.
my %LETRAS;      # Posicion de las letras dentro del archivo words.idx.
my %TOSHOW;      # Resultados para desplegar.
my $TURBOMODE;   # Busqueda sin comodines.
my @YESWORDS;    # Palabras a buscar.
my @NOTWORDS;    # Palabras a omitir.
my @FRASES;      # 1.24 Frases a buscar.
my @FOUNDWORDSIDX; # Indices de las palabras a encontradas en cada indice.
my $MAXWORDS;    # Maximo de palabras distintas encontradas en un mismo archivo cuando se busca con wildcards.
my $MAXPALABRAS; # Maximo de palabras repetidas encontradas dentro de un archivo.
my @NOTWORDSIDX; # Indices de las palabras a omitir.
my %WORDSINDEXES; # 1.24 Indices de las palabras buscadas. Usado en la busqueda por frases.
my @IDX;         # Indices donde buscar.
my @ANOS;        # Anos presentes en los indices.
my $ANO;         # Ano sobre el cual se esta buscando.
my $FILTROACTIVO; # Flag que indica si se deben aplicar filtros o no.
my $FORMfechaini; # Fecha de inicio en formato ISO, para filtrar resultados.
my $FORMfechafin; # Fecha de termino en formato ISO, para filtrar resultados.
my $PLANTILLA;   # Plantilla de la pagina de resultados.
my $EXT;         # 1.10
my $RESULTADO;   # 1.10
my $MSG = '';    # Fuerza mensaje en la pagina de resultados.
my $CFG_FILENAME = 'buscador_prontus.cfg'; # Nombre del archivo de configuracion.
my $WORDS_FILENAME = 'words.idx';   # Nombre del archivo de palabras.
my $CARS_FILENAME = 'cars.idx';     # Nombre del archivo de caracteres.
my $FILES_FILENAME = 'files.idx';   # Nombre del archivo indice de articulos.
my $FILESINDEXF_FILENAME = 'filesindexf.idx'; # 1.24 Nombre del archivo de indice de archivos para la busqueda por frases.
my $WORDSINDEX_FILENAME = 'wordsindex.idx'; # Nombre del archivo de indice de palabras.
my @NOBUSCAR = ('de','el','la','los','las','del','en'); # 1.14 Palabras comunes por las que no hay que buscar.
my %MSGS;        # 1.18 Arreglo de mensajes.
my $VISTA;       # 1.18 Vista a mostrar.
my $RESXPAG = 50; # Maximo de resultados por pagina por defecto (overrideable por la CFG).
my $MAXPAGS = 20;  # Maximo de paginas por defecto (overrideable por la CFG).
my $DEBUG = 0;   # 1.22
if ($DEBUG) { print "\n<pre>inicio \n"; };

&getFormData(); # Lee formulario de invocacion y valida las variables.

my $PRONTUS = $FORM{'search_prontus'}; # Nombre del publicador Prontus donde se aloja el buscador.
if ($PRONTUS eq '') { # Muestra pagina en blanco.
  print "\nProntus dir not found. \nDirectorio Prontus no especificado.";
  exit;
};
if ($DEBUG) { print "\n<pre>PRONTUS = $PRONTUS \n"; };


my $PRONTUS_DIR = "$DOCUMENT_ROOT/$PRONTUS";
my $SEARCH_DIR = "$PRONTUS_DIR/cpan/data/search"; # Directorio de trabajo.
my $CACHE_REL_DIR = "/$PRONTUS/site/cache/search/pags"; # 1.10 Directorio de cache para el direccionamiento web.
my $CACHE_DIR = "$DOCUMENT_ROOT$CACHE_REL_DIR"; # 1.10 Directorio de cache.
my $TMP_DIR = "$PRONTUS_DIR/plantillas/extra/search/pags$VISTA"; # 1.10 Directorio de las plantillas.
# Lee archivo de configuracion y determina la cantidad de instancias que se aceptan.
if (! -f "$PRONTUS_DIR/cpan/$CFG_FILENAME") { # 1.21
  # Si no hay archivo de cfg, aborta.
  print "\nProntus Search cfg file not found. \nArchivo de configuraci&oacute;n Prontus no encontrado.";
  exit;
};
if ($DEBUG) { print "\n<pre>PRONTUS_DIR = $PRONTUS_DIR \n"; };

%CFG = &lib_search::get_config("$PRONTUS_DIR/cpan/$CFG_FILENAME");
if ( ($CFG{'SEARCH_MAXEXEC'} < 0) || ($CFG{'SEARCH_MAXEXEC'} !~ /^\d+$/) ) {
  $CFG{'SEARCH_MAXEXEC'} = 5;
};

# 1.27.2 if ($CFG{'RESPERPAG'} =~ /^\d+/) { $FORM{'search_resxpag'} = $CFG{'RESPERPAG'}; }; # 1.22
# 1.27.2 if ($CFG{'MAXPAGS'} =~ /^\d+/) { $FORM{'search_maxpags'} = $CFG{'MAXPAGS'}; }; # 1.22

# 1.27.2 Si no se especifican el la CFG, usa valores por defecto.
if ($CFG{'RESPERPAG'} !~ /^\d+$/) { $CFG{'RESPERPAG'} = $RESXPAG; };
if ($CFG{'MAXPAGS'} !~ /^\d+$/) { $CFG{'MAXPAGS'} = $MAXPAGS; };
# 1.27.2 Si los valores del form no se especifican o exceden el maximo, aplica el maximo.
if(($FORM{'search_resxpag'} eq '') || ($FORM{'search_resxpag'} > $CFG{'RESPERPAG'})) {
  $FORM{'search_resxpag'} = $CFG{'RESPERPAG'};
};
if(($FORM{'search_maxpags'} eq '') || ($FORM{'search_maxpags'} > $CFG{'MAXPAGS'})) {
  $FORM{'search_maxpags'} = $CFG{'MAXPAGS'};
};

# Cargar variables de configuración necesarias para friendly url desde archivo -var
my($buffervarcfg) = &lib_search::lee_archivo("$PRONTUS_DIR/cpan/$PRONTUS-var.cfg");
if ($buffervarcfg =~ m/\s*FRIENDLY_URLS\s*=\s*("|')(.*?)("|')/) {
    $prontus_varglb::FRIENDLY_URLS = $2;
};

if ($buffervarcfg =~ m/\s*FRIENDLY_URLS_VERSION\s*=\s*("|')(.*?)("|')/) {
    $prontus_varglb::FRIENDLY_URLS_VERSION = $2;
};

# Parsea y muestra primera parte de la pagina de resultados.
# 1.10 $PLANTILLA = &leeplantilla($PRONTUS_DIR,$FORM{'search_tmp'}); # Directorio de trabajo.
$PLANTILLA = &lib_search::lee_archivo($TMP_DIR .'/'. $FORM{'search_tmp'});
# if ($DEBUG) { print "\n<pre>PLANTILLA = $PLANTILLA \n"; };

&inicializaMensajes(); # 1.8 Carga arreglo de stop words (@NOBUSCAR) y hash de mensajes (%MSGS).
$RESULTADO = &parsea_plantilla1(); # 1.10
# 1.10 Deduce la extension de la plantilla.
if ($FORM{'search_tmp'} =~ /\.([\w]+)$/) {
  $EXT = $1;
};

my $IDX = $FORM{'search_idx'}; # Nombre del indice a utilizar.
if ( (uc $IDX) eq 'ALL' ) {
  @IDX = &get_idx($SEARCH_DIR);
}else{
  push @IDX, $IDX;
};
if ($DEBUG) { print "\n<pre>IDX = @IDX \n"; };

# Determina si hay menos invocaciones que el maximo permitido (UNIX).
# if (&lib_search::myself_running() > $CFG{'SEARCH_MAXEXEC'}) {
if (&lib_maxrunning::myselfRunning() > $CFG{'SEARCH_MAXEXEC'}) { # 1.29
  $MSG = $MSGS{'server_busy'}; # 1.18 'Servidor ocupado. Intenta m&aacute;s tarde ...';
  $RESULTADO .= &parsea_plantilla2(); # 1.10
  &muestraResultado();
  # 1.10 exit; # Muestra pagina en blanco.
};

# Si no hay variables de invocacion, muestra el formulario solo.
# if ($FORM{'search_texto'} eq '') {
if ($FORM{'search_texto'} !~ /[0-9a-zA-Z]{2}/) { # 1.8
  # print "debug: texto invalido<br>\n";
  $MSG = $MSGS{'no_results'}; # 1.18 'No se encontraron resultados.' ;
  $RESULTADO .= &parsea_plantilla2();
  &muestraResultado();
};

# Depura el texto ingresado para determinar las palabras a buscar (@SEARCHWORDS).
my($yeswords,$notwords,$turbomode,$frases) = &depura_palabras(); # 1.24
@YESWORDS = @$yeswords;
@NOTWORDS = @$notwords;
$TURBOMODE = $turbomode;
@FRASES = @$frases; # 1.24

$RESULTADOSTOTALES = 0;
foreach my $idx (@IDX) {
  $IDX = $idx;
  # Encuentra anos indexados dentro de cada indice. El indice raw corresponde al ano 0000.
  @ANOS = &get_anos("$SEARCH_DIR/$IDX");
  foreach $ANO (sort {$b <=> $a} @ANOS) {
    # Busca los indices de las palabras a encontrar y las stop words.
    my($foundwordsidx,$notwordsidx,$wordsindexes) = &busca_palabras("$SEARCH_DIR/$IDX/$ANO");
    @FOUNDWORDSIDX = sort {$a <=> $b} @$foundwordsidx;
    @NOTWORDSIDX = @$notwordsidx;
    %WORDSINDEXES = %$wordsindexes;
    # Busca las palabras en el indice de palabras, encontrando los indices de archivo.
    &busca_archivos("$SEARCH_DIR/$IDX/$ANO");
  };
};

$RESULTADO .= &muestra_resultados(); # 1.10
&muestraResultado(); # 1.10

# ###################################################
# Funciones


# -------------------------------------------------------------------------#
# 1.18 Busca, inicializa y elimina mensajes y stopwords dentro de la plantilla.
# Carga arreglo de stop words (@NOBUSCAR) y hash de mensajes (%MSGS).
#     <!-- STOPWORDS = al,de,nos,fu -->
#     <!-- MSG xxx = xxx -->
sub inicializaMensajes {
  my($stopwords);
  # Mensajes por defecto.
  $MSGS{'server_busy'} = 'Servidor ocupado. Intenta m&aacute;s tarde ...';
  $MSGS{'no_results'} = 'No se encontraron resultados.';
  $MSGS{'order_cron'} = 'en orden cronol&oacute;gico.';
  $MSGS{'order_rel'} = 'en orden de importancia.';
  $MSGS{'results'} = 'Resultados';
  $MSGS{'to'} = 'al';
  $MSGS{'of'} = 'de';
  while ($PLANTILLA =~ /<!--\s*MSG\s*(\w+)\s*=\s*(.+?)\s*-->/sg) {
    $MSGS{$1} = $2;
  };
  # Elimina mensajes de la plantilla.
  $PLANTILLA =~ s/<!--\s*MSG\s*(\w+)\s*=\s*(.+?)\s*-->//sg;
  # Stop words. Busca y elimina al mismo tiempo.
  if ($PLANTILLA =~ s/<!--\s*STOPWORDS\s*=\s*([\w\,\ ]+)\s*-->//s) {
    $stopwords = $1;
    $stopwords =~ s/\s+//g;
    @NOBUSCAR = split(/,/,$stopwords);
  };
}; # inicializaMensajes

# -------------------------------------------------------------------------#
# 1.10 Parsea y retorna la primera parte de la pagina de resultados.
# Si en la plantilla no hay separador no hace nada.
sub parsea_plantilla1 {
  my $plantilla = $PLANTILLA;
  my($scriptname) = $ENV{'SCRIPT_NAME'}; # 1.21
  my($aux,$key);
  if ($plantilla =~ /<!--separador-->/si) {
    $plantilla = $`;
  }else{
    return; # Si no hay separador no hace nada.
  };
  # Elimina el formulario si es que el mode era 0.
  if ($FORM{'search_form'} eq 'no') {
    $plantilla =~ s/<!--formulario-->(.+?)<!--\/formulario-->//sig;
  };
  # En forma automatica, crea y parsea variables checked y las variables del formulario.
  foreach $key (keys %FORM) {
    $aux = $FORM{$key};
    # if ($aux =~ /^[\w]+$/) { # 1.8
    if ($aux =~ /\w+/) { # 1.13
      $plantilla =~ s/%%chk_$key\_$aux%%/checked=\"checked\"/isg; # 1.25
      $plantilla =~ s/%%sel_$key\_$aux%%/selected=\"selected\"/isg; # 1.25
    };
    $plantilla =~ s/%%$key%%/$aux/isg;
  };
  # 1.21 Parsea nombre de la CGI.
  $plantilla =~ s/%%scriptname%%/$scriptname/sg; # 1.21
  # Elimina tags sin parsear.
  $plantilla =~ s/%%[^%]+%%//sg;
  return $plantilla;
}; # parsea_plantilla1

# -------------------------------------------------------------------------#
# 1.10 Parsea y retorna la segunda parte de la pagina de resultados.
# Si en la plantilla no hay separador parsea y muestra la pagina completa.
sub parsea_plantilla2 {
  my(@resultados) = @_;
  my($scriptname) = $ENV{'SCRIPT_NAME'}; # 1.13
  my($searchloop,$searchloop_tmp,$aux,$resultad);
  # $fechap|$ts.$extension|$titular|meta1|meta2|meta3|$descripcion|$seccion|$tema|$subtema
  my($numresult,$numrepet,$fechap,$file,$tit,$meta1,$meta2,$meta3,$res,$sec,$tem,$sub,$ts,$ext,$rel,$dir,$lnk,$fec,$msg,$msgsn,$pags,$num,$i,$key,$resultado); # 1.7
  my @metadata = (); # 1.27.2
  my ($prontus_id); # 1.27
  my $search_resxpag = $FORM{'search_resxpag'};
  my $search_pag = $FORM{'search_pag'};
  my $min = ($search_pag - 1) * $search_resxpag + 1; # Numero del primer resultado mostrado.
  my $max = $search_pag * $search_resxpag;
  my $paginastotales = int( 1 + ($RESULTADOSTOTALES - 1) / $search_resxpag);
  my $yeswords;

  if ($TURBOMODE == 1) {
    $yeswords = $#YESWORDS + 1;
  }else{
    $yeswords = $MAXWORDS;
  };

  if ( $paginastotales > $FORM{'search_maxpags'}) { $paginastotales = $FORM{'search_maxpags'}; };
  if ($max > $RESULTADOSTOTALES) { $max = $RESULTADOSTOTALES; };
  for($i=1;$i<=$paginastotales;$i++) {
    if ($i != $search_pag) {
      # 1.13 $pags .= '| <a href="/cgi-bin/prontus_search.cgi?search_prontus=' . $FORM{'search_prontus'}
      $pags .= '<a href="' . $scriptname . '?search_prontus=' . $FORM{'search_prontus'}
            . '&amp;search_idx=' . $FORM{'search_idx'}
            . '&amp;search_tmp=' . $FORM{'search_tmp'}
            . '&amp;search_form=' . $FORM{'search_form'}
            . '&amp;search_pag=' . $i
            . '&amp;search_resxpag=' . $FORM{'search_resxpag'}
            . '&amp;search_maxpags=' . $FORM{'search_maxpags'}
            . '&amp;search_orden=' . $FORM{'search_orden'}
            . '&amp;search_meta1=' . &lib_search::escapehtml($FORM{'search_meta1'})
            . '&amp;search_meta2=' . &lib_search::escapehtml($FORM{'search_meta2'})
            . '&amp;search_meta3=' . &lib_search::escapehtml($FORM{'search_meta3'})
            . '&amp;search_seccion=' . &lib_search::escapehtml($FORM{'search_seccion'})
            . '&amp;search_tema=' . &lib_search::escapehtml($FORM{'search_tema'})
            . '&amp;search_subtema=' . &lib_search::escapehtml($FORM{'search_subtema'})
            . '&amp;search_fechaini=' . &lib_search::escapehtml($FORM{'search_fechaini'})
            . '&amp;search_fechafin=' . &lib_search::escapehtml($FORM{'search_fechafin'})
            . '&amp;search_texto=' . &lib_search::escapehtml($FORM{'search_texto'})
            . '&amp;search_modo=' . $FORM{'search_modo'}
            . '&amp;search_comodines=' . $FORM{'search_comodines'}
            . '&amp;vista=' . &lib_search::escapehtml($FORM{'vista'})
            . '">' . $i . '</a> '; # 1.7 1.26
    }else{
      $pags .= "<span class='pag_actual'> $i </span>";
    };
  };

  my $plantilla = $PLANTILLA;
  if ($plantilla =~ /<!--separador-->/si) {
    $plantilla = $'; # '
  };
  # Elimina el formulario si es que el mode era 0.
  if ($FORM{'search_form'} eq 'no') {
    $plantilla =~ s/<!--formulario-->(.+?)<!--\/formulario-->//sig;
  };
  if ($plantilla =~ /<!--resloop-->(.+?)<!--\/resloop-->/si) {
    $searchloop_tmp = $1;
  };
  # print "searchloop_tmp = [$searchloop_tmp]"; # debug
  $num = $min;
  # Ajusta valores para no pasar el 100%).
  $yeswords++;
  $MAXPALABRAS++;
  foreach $resultado (@resultados) {
    ($numresult,$numrepet,$fechap,$file,$tit,$meta1,$meta2,$meta3,$res,$sec,$tem,$sub,@metadata) = split(/\|/,$resultado); # 1.7
    # ($ts,$ext) = split(/\./,$file);
    # 1.12 Rescata la extension.
    if ($file =~ /\.([^\.]+)$/) {
      $ext = lc $1;
    };
    $rel = int(100 * ($numresult/$yeswords + $numrepet/($yeswords * $MAXPALABRAS))); # Calcula el ranking de este resultado
    # $rel = "$numresult $numrepet $yeswords $MAXPALABRAS $rel"; # debug
    # $dir = substr($file,0,8);
    $lnk = $file;
    if ($lnk =~ /\/(\w+)\/site\/artic\/\d{8}\/pags\/(\d{14})\.\w+$/) { # 1.27 1.27.2
      $prontus_id = $1;
      $ts =  $2;
      if ($CFG{'USEFRIENDLYURLS'} == 1) {
        #~ $lnk = &lib_search::friendlyUrl($prontus_id,$ts,$tit,$ext); # deprecated.
        $lnk = &lib_prontus::parse_filef('%%_FILEURL%%', $tit, $ts, $PRONTUS, $file, $sec, $tem, $sub);
      };
    };
    $fec = $fechap;
    $aux = $searchloop_tmp;
    # Elimina contenido condicional.
    if ($fec eq '') {
      $aux =~ s/%%if\(fec\)%%.+?%%\/if%%//isg;
    };
    if ($sec eq '') {
      $aux =~ s/%%if\(sec\)%%.+?%%\/if%%//isg;
    };
    if ($tem eq '') {
      $aux =~ s/%%if\(tem\)%%.+?%%\/if%%//isg;
    };
    if ($sub eq '') {
      $aux =~ s/%%if\(sub\)%%.+?%%\/if%%//isg;
    };
    # 1.19 Agrega procesamiento de ifs para los campos meta.
    if ($meta1 eq '') {
      $aux =~ s/%%if\(meta1\)%%.+?%%\/if%%//isg;
    };
    if ($meta2 eq '') {
      $aux =~ s/%%if\(meta2\)%%.+?%%\/if%%//isg;
    };
    if ($meta3 eq '') {
      $aux =~ s/%%if\(meta3\)%%.+?%%\/if%%//isg;
    };
    for ($i=1;$i<=10;$i++) { # 1.27.2
      if ($metadata[$i-1] eq '') {
        $aux =~ s/%%if\(metadata$i\)%%.+?%%\/if%%//isg;
      };
    };
    $aux =~ s/%%ext%%/$ext/isg; # 1.12
    $aux =~ s/%%num%%/$num/isg;
    $aux =~ s/%%rel%%/$rel/isg;
    $aux =~ s/%%lnk%%/$lnk/isg;
    $aux =~ s/%%tit%%/$tit/isg;
    $fec = &lib_search::iso2fechacorta($fec);
    $aux =~ s/%%fec%%/$fec/isg;
    $aux =~ s/%%res%%/$res/isg;
    $aux =~ s/%%meta1%%/$meta1/isg; # 1.7
    $aux =~ s/%%meta2%%/$meta2/isg; # 1.7
    $aux =~ s/%%meta3%%/$meta3/isg; # 1.7
    $aux =~ s/%%sec%%/$sec/isg;
    $aux =~ s/%%tem%%/$tem/isg;
    $aux =~ s/%%sub%%/$sub/isg;
    for ($i=1;$i<=10;$i++) { # 1.27.2
      $aux =~ s/%%metadata$i%%/$metadata[$i-1]/isg;
    };
    $num++;
    $searchloop .= $aux;
  };
  # En forma automatica, crea y parsea variables checked y las variables del formulario.
  foreach $key (keys %FORM) {
    $aux = $FORM{$key};
    if ($aux =~ /^[\w]+$/) { # 1.8
      $plantilla =~ s/%%chk_$key\_$aux%%/checked=\"checked\"/isg; # 1.25
      $plantilla =~ s/%%sel_$key\_$aux%%/selected=\"selected\"/isg; # 1.25
    };
    $plantilla =~ s/%%$key%%/$aux/isg;
  };
  if ($FORM{'search_orden'} eq 'cro') { # 1.3
    $msg = $MSGS{'order_cron'}; # 1.18 'cronol&oacute;gico.';
  }else{
    $msg = $MSGS{'order_rel'}; # 1.18 'de importancia.';
  };
  if ($RESULTADOSTOTALES > 0) {
    $msgsn = $MSGS{'results'} . ' ' . $msg; # 1.18 "Resultados en orden $msg";
    $msg = $MSGS{'results'} ." $min ". $MSGS{'to'} ." $max " . $MSGS{'of'} . ' '
         . &lib_search::formatInteger($RESULTADOSTOTALES) . ' ' . $msg; # 1.25
  }else{
    if ($FORM{'search_texto'} ne '') {
      $msg = $MSGS{'no_results'}; # 'No se encontraron resultados.';
    }else{
      $msg = '';
    };
    $msgsn = $msg;
    $plantilla =~ s/<!--pags-->(.+?)<!--\/pags-->//is;
  };
  if ($paginastotales < 2) { $plantilla =~ s/<!--pags-->(.+?)<!--\/pags-->//is; };
  if ($MSG ne '') { $msg = $MSG; };
  $plantilla =~ s/%%msg%%/$msg/is;
  $plantilla =~ s/%%msgsn%%/$msgsn/is; # 1.7
  $plantilla =~ s/%%pags%%/$pags/is;
  $plantilla =~ s/<!--resloop-->(.+?)<!--\/resloop-->/$searchloop/is;
  # 1.21 Parsea nombre de la CGI.
  $plantilla =~ s/%%scriptname%%/$scriptname/sg; # 1.21
  # Elimina tags sin parsear.
  $plantilla =~ s/%%[^%]+%%//sg;
  return $plantilla;
  # print "debug: fin plantilla<br>\n";
}; # parsea_plantilla2

# -------------------------------------------------------------------------#
# Lee y administra el cache de las plantillas del buscador.
sub leeplantilla {
  my($prontus_dir,$search_tmp) = @_;
  if ($search_tmp eq '') { $search_tmp = 'search.html'; };
  my($url) = 'http://' . $ENV{'HTTP_HOST'} . "/$PRONTUS/plantillas/extra/search/pags/$search_tmp";
  # print "<br>URL Plantilla=[$url]<br>\n"; # debug
  my($plantilla_file) = "$CACHE_DIR/$search_tmp"; # 1.10
  my($plantilla,$tiempo);
  # Por ahora, lee el archivo directamente.
  # return &lib_search::lee_archivo("$prontus_dir/plantillas/extra/search/pags/$search_tmp");
  # print 'http://' . $ENV{'HTTP_HOST'} . "$PRONTUS/plantillas/extra/search/pags/$search_tmp"; debug
  # Verifica si el cache de la plantilla es lo suficientemente reciente (5 minutos).
  if (-f $plantilla_file) {
    $tiempo = (stat($plantilla_file))[9];
    if ( $tiempo < (time - 300) ) {
      $plantilla = &lib_search::getHTML($url);
      if ($plantilla ne '') {
        &lib_search::escribe_archivo($plantilla_file,$plantilla);
      };
    }else{
      $plantilla = &lib_search::lee_archivo($plantilla_file);
    };
  }else{
    $plantilla = &lib_search::getHTML($url);
    if ($plantilla ne '') {
      &lib_search::escribe_archivo($plantilla_file,$plantilla);
    };
  };
  # Si la plantilla no esta disponible via http, entonces la lee del disco.
  if ($plantilla eq '') {
    $plantilla = &lib_search::lee_archivo("$prontus_dir/plantillas/extra/search/pags/$search_tmp");
  };
  # print "<br>Plantilla=[$plantilla]<br>\n"; # debug
  return $plantilla;
}; # leeplantilla

# -------------------------------------------------------------------------#
# Muestra los resultados en el orden requerido.
# En $RESULTADOS{"$idxdir$fidx"} esta la cantidad de veces que las palabras se encuentran dentro del archivo.
# En $NUMRESULT{"$idxdir$fidx"} esta el numero de palabras que está en ese archivo.
# En $FECHAP{"$idxdir$fidx"} esta la fecha de publicacion ese archivo.
# En $FILEDATA{"$idxdir$fidx"} esta los datos de ese archivo.
sub muestra_resultados {
  my ($resultcounter);
  my ($anofidx,$ano,$fidx,$idx,$contenido,$counter,$idxdirfidx);
  my $search_resxpag = $FORM{'search_resxpag'};
  my $search_pag = $FORM{'search_pag'};
  my $min = ($search_pag - 1) * $search_resxpag + 1;
  my $max = $search_pag * $search_resxpag;
  my @resultados;

  $resultcounter = 0;
  $MAXWORDS = 0;
  if ($FORM{'search_orden'} eq 'rel') {
    # Muestra resultados en orden relativo.
    # Usa truco de suponer que las palabras no apareceran mas de 1000 veces dentro de un archivo.
    foreach $idxdirfidx (sort {(1000 * $NUMRESULT{$b} + $RESULTADOS{$b}) <=> (1000 * $NUMRESULT{$a} + $RESULTADOS{$a})} keys %FILEDATA) {
      $resultcounter++;
      if ( ($min <= $resultcounter) && ($resultcounter <= $max) ) {
        push @resultados, $NUMRESULT{$idxdirfidx} . '|' . $RESULTADOS{$idxdirfidx} . '|' . $FILEDATA{$idxdirfidx};
        if ($MAXWORDS < $NUMRESULT{$idxdirfidx}) {
          $MAXWORDS = $NUMRESULT{$idxdirfidx};
        };
        # print "<p>$anofidx pushed! "; # debug
      };
    };
  }else{
    # Muestra resultados en orden cronologico.
    foreach $idxdirfidx (sort {$FECHAP{$b} <=> $FECHAP{$a}} keys %FILEDATA) {
      $resultcounter++;
      if ( ($min <= $resultcounter) && ($resultcounter <= $max) ) {
        push @resultados, $NUMRESULT{$idxdirfidx} . '|' . $RESULTADOS{$idxdirfidx} . '|' . $FILEDATA{$idxdirfidx};
        # print "<p>[" . $FECHAP{$idxdirfidx} . "] $idxdirfidx pushed! "; # debug
        if ($MAXWORDS < $NUMRESULT{$idxdirfidx}) {
          $MAXWORDS = $NUMRESULT{$idxdirfidx};
        };
      };
    };
  };
  return &parsea_plantilla2(@resultados);
}; # muestra_resultados

# -------------------------------------------------------------------------#
# Busca las palabras en el indice de palabras, encontrando los indices de archivo.
# En $RESULTADOS{"$idxdir$fidx"} queda la cantidad de veces que las palabras se encuentran dentro del archivo.
# En $NUMRESULT{"$idxdir$fidx"} queda el numero de palabras que esta en ese archivo.
# En $FECHAP{"$idxdir$fidx"} queda la fecha de publicacion ese archivo.
# En $FILEDATA{"$idxdir$fidx"} quedan los datos de ese archivo.
sub busca_archivos {
  my($idxdir) = $_[0];
  my($widx,$locations,$fidx,$wcount,%resultados,$yeswords,$idx,$contenido);
  my($lalinea,$theword);
  my $counter = 0;
  my $wordcount = 0;
  my %nofiles; # Hash de archivos a omitir.
  my ($frase,$palabra,$palabraIdx,@wordSequence); # 1.24
  # print "Busca Archivos $ano:\n";

  # Busqueda binaria en el archivo de palabras.
  foreach $theword (@FOUNDWORDSIDX) {
    # print "theword=$theword<br>\n"; # debug
    $lalinea = &lib_search::binsearch("$idxdir/$WORDSINDEX_FILENAME",$theword,'num');
    if ($lalinea ne '') {
      # print "lalinea=$lalinea<br>\n"; # debug
      ($widx,$locations) = split(/=/,$lalinea);
      if ($theword == $widx) {
        while ($locations =~ /\|(\d+) (\d+)/g) {
          ($fidx,$wcount) = ($1,$2);
          # Veta los archivos donde se encuentra una not word.
          if (grep {$widx == $_} @NOTWORDSIDX) {
            $nofiles{$fidx} = 1;
            # print '-';
          }else{
            $resultados{$fidx} = 1; # Marca resultado. Se usa un hash para eliminar automaticamente los repetidos.
            $RESULTADOS{"$idxdir$fidx"} += $wcount;
            $NUMRESULT{"$idxdir$fidx"}++;
            # Detecta el maximo de palabras encontradas para construir el ranking.
            if ($MAXPALABRAS < $RESULTADOS{"$idxdir$fidx"}) { $MAXPALABRAS = $RESULTADOS{"$idxdir$fidx"}; };
            # print '+ '; # debug
          };
        };
      }; # if
    }; # if
  }; # foreach

  # Elimina los resultados vetados por not words.
  # print "Borrando de los resultados ";
  foreach $fidx (keys %nofiles) {
    # print ".";
    delete $resultados{$fidx};
    delete $RESULTADOS{"$idxdir$fidx"};
    delete $NUMRESULT{"$idxdir$fidx"};
  };
  # Si el modo es AND, elimina los resultados con menos del total de palabras requeridas.
  if ($FORM{'search_modo'} eq 'and') {
    foreach $fidx (keys %resultados) {
      # print ".";
      $yeswords = $#YESWORDS + 1;
      if ($NUMRESULT{"$idxdir$fidx"} < $yeswords) {
        delete $resultados{$fidx};
        delete $RESULTADOS{"$idxdir$fidx"};
        delete $NUMRESULT{"$idxdir$fidx"};
      };
    };
  };

  # Lee los datos del archivo de cada resultado, aplicando filtros si es pertinente.
  if (-f "$idxdir/$FILES_FILENAME") { # 1.27.2 Verifica que archivo existe antes de abrirlo.
    open (IN,"<$idxdir/$FILES_FILENAME") || die "No puedo abrir $idxdir/$FILES_FILENAME $!";
    $counter = 0;
    foreach $fidx (sort {$a <=> $b} keys %resultados) { # Ordena por numero, ya que asi estan ordenados en el indice.
      while (<IN>) {
        $counter++;
        last if ($counter == $fidx); # Se salta las lineas que no son, hasta que encuentra la correcta.
      };
      chomp;
      ($idx,$contenido) = split(/=/,$_,2);
      if ($fidx != $idx) { print "<p>Desfase $idxdir/$FILES_FILENAME: $fidx != $idx\n"; last; }; # debug
      if (&filtraresultado($contenido) == 1) {
        # Mete los resultados al hash de resultados
        $FILEDATA{"$idxdir$fidx"} = $contenido;
        $FECHAP{"$idxdir$fidx"} = (split(/\|/,$contenido))[0];
        $RESULTADOSTOTALES++;
      };
    };
    close IN;
  };

  # 1.24 Si se ha buscado por frases, elimina los archivos donde las palabras de la frase no estan en secuencia.
  return if ($#FRASES < 0);
  if (-f "$idxdir/$FILESINDEXF_FILENAME") { # 1.27.2 Verifica que archivo existe antes de abrirlo.
    open (IN,"<$idxdir/$FILESINDEXF_FILENAME") || die "No puedo abrir $idxdir/$FILESINDEXF_FILENAME $!";
    $counter = 0;
    foreach $fidx (sort {$a <=> $b} keys %resultados) { # Ordena por numero, ya que asi estan ordenados en el indice.
      while (<IN>) {
        $counter++;
        last if ($counter == $fidx); # Se salta las lineas que no son, hasta que encuentra la correcta.
      };
      chomp;
      ($idx,$contenido) = split(/=/,$_,2);
      if ($fidx != $idx) { print "<p>Desfase $idxdir/$FILESINDEXF_FILENAME: $fidx != $idx\n"; last; }; # debug
      # Verifica que las palabras de las frases son secuenciales en el archivo.
      # Tenemos "palabra1 palabra2 ..." contra widx ubic1 ubic2 ubic3...|widx2 ubic1 ubic2 ...
      foreach $frase (@FRASES) {
        # Crea secuencia patron de palabras.
        @wordSequence = ();
        foreach $palabra (split(/ /,$frase)) {
          if ($palabra =~ /[a-z0-9A-Z]{2}/) {
            push @wordSequence, $WORDSINDEXES{$palabra};
          };
        };
        # Comprueba si la secuencia se cumple para el archivo.
        if (&matchSequence(\@wordSequence,$contenido) == 0) {
          # Elimina el resultado del hash de resultados
          delete $FILEDATA{"$idxdir$fidx"};
          delete $FECHAP{"$idxdir$fidx"};
          $RESULTADOSTOTALES--;
        };
      };
    };
    close IN;
  };

}; # busca_archivos

# -------------------------------------------------------------------------#
# Busca las palabras en los archivos de indice del ano indicado.
# Retorna punteros a los arreglos de indices de las palabras encontradas
# y de indices de stopwords encontradas.
sub busca_palabras {
  my($idxdir) = $_[0];
  my(@searchwords,$count,$wordcount,$laletra,$palabra,$widx);
  my(@foundwordsidx,@notwordsidx,%wordsindexes); # 1.24
  my($lapalabra,$lalinea);
  # Si no hay wildcards, usa el indice de letras para acelerar la busqueda.
  if ($TURBOMODE == 1) {
    # Reconstruye las search words ya validadas.
    @searchwords = @YESWORDS;
    push @searchwords, @NOTWORDS;
    @searchwords = sort @searchwords;

    # Busqueda binaria.
    foreach $lapalabra (@searchwords) {
      # print "lapalabra=$lapalabra<br>\n"; # debug
      $lalinea = &lib_search::binsearch("$idxdir/$WORDS_FILENAME",$lapalabra,'str');
      if ($lalinea ne '') {
        ($palabra,$widx) = split(/=/,$lalinea);
        # 1.24 Registra equivalencia para ser usada en la busqueda por frases.
        $wordsindexes{$palabra} = $widx;
        # print "lalinea=$lalinea widx=$widx<br>\n"; # debug
        push @foundwordsidx, $widx; # Igual la guarda como parte de los resultados.
        if (grep {$palabra eq $_} @NOTWORDS) { # Registra indices de las not words.
          push @notwordsidx,$widx;
          # print "Not Word idx: $palabra $widx\n"; # debug
        };
      };
    };

  }else{ # Hay wildcards y cosas asi.
    # print "NOT Turbo Mode ***\n";
    # Lee indice de palabras. Implementa match con expresion regular,
    # asi que no puede usar el indice de letras ni busqueda binaria.
    # print "laletra=$laletra offset=" . $LETRAS{$laletra} . "\n"; # debug
    if (-f "$idxdir/$WORDS_FILENAME") { # 1.27.2
      open (IN,"<$idxdir/$WORDS_FILENAME");
      while (<IN>) {
        chomp;
        ($palabra,$widx) = split(/=/,$_);
        if (grep {$palabra =~ /$_/} @NOTWORDS) { # Registra indices de las not words.
          # print "Found Not: $palabra $widx\n"; # debug
          push @notwordsidx,$widx;   # Registra indices de las not words.
          push @foundwordsidx,$widx; # Igual la guarda como parte de los resultados.
        }elsif (grep {$palabra =~ /$_/} @YESWORDS) {
          # print "Found Yes: $ano $palabra $widx | @YESWORDS\n"; # debug
          push @foundwordsidx,$widx;
        };
      };
      close IN;
    };
  };
  return (\@foundwordsidx,\@notwordsidx,\%wordsindexes);
}; # busca_palabras

# -------------------------------------------------------------------------#
# Aplica los filtros pertinentes a los resultados.
# Si el resultado esta dentro de rango, retorna 1.
sub filtraresultado {
  return 1 if ($FILTROACTIVO == 0);
  my($fechap,$file,$tit,$meta1,$meta2,$meta3,$res,$sec,$tem,$sub) = split(/\|/,$_[0]); # 1.7
  if ($FORM{'search_meta1'} ne '') { # 1.7
    return 0 if ($FORM{'search_meta1'} !~ /(^| |,)$meta1($| |,)/i); # 1.23 Busca coincidencia con alguno de los parametros.
  };
  if ($FORM{'search_meta2'} ne '') { # 1.7
    return 0 if ($FORM{'search_meta2'} !~ /(^| |,)$meta2($| |,)/i); # 1.23 Busca coincidencia con alguno de los parametros.
  };
  if ($FORM{'search_meta3'} ne '') { # 1.7
    return 0 if ($FORM{'search_meta3'} !~ /(^| |,)$meta3($| |,)/i); # 1.23 Busca coincidencia con alguno de los parametros.
  };
  if ($FORM{'search_seccion'} ne '') {
    return 0 if ($FORM{'search_seccion'} ne $sec);
  };
  if ($FORM{'search_tema'} ne '') {
    return 0 if ($FORM{'search_tema'} ne $tem);
  };
  if ($FORM{'search_subtema'} ne '') {
    return 0 if ($FORM{'search_subtema'} ne $sub);
  };
  if ($FORMfechaini ne '') {
    return 0 if ($FORMfechaini > $fechap);
  };
  if ($FORMfechafin ne '') {
    return 0 if ($FORMfechafin < $fechap);
  };
  return 1;
}; # filtraresultado

# -------------------------------------------------------------------------#
# Encuentra los anos indexados.
sub get_anos {
  my($dir) = $_[0];
  my(@anos);
  my(@files) = &lib_search::lee_dir($dir);
  foreach my $entry (@files) {
    # print $entry; # debug
    if ($entry =~ /^\d{4}$/) {
      push @anos, $entry;
    };
  };
  return @anos;
}; # get_anos

# -------------------------------------------------------------------------#
# Encuentra los indices presentes en el directorio search.
sub get_idx {
  my($dir) = $_[0];
  my(@idx);
  my(@files) = &lib_search::lee_dir($dir);
  foreach my $entry (sort @files) { # 1.27.2
    # print $entry; # debug
    if ( ($entry !~ /^\./) && (-d "$dir/$entry") ) {
      push @idx, $entry;
    };
  };
  return @idx;
}; # get_idx

# -------------------------------------------------------------------------#
# Depura el texto ingresado para determinar las palabras a buscar.
sub depura_palabras {
  my($texto) = $FORM{'search_texto'};
  my(@searchwords,$caracteres,$palabra,$frase);
  my(@yeswords,@notwords,@frases,$turbomode,@aux);
  # 1.28 $texto = &lib_search::notildes($texto);
  $texto = &lib_search::notildesUtf8($texto); # 1.28
  $texto = lc $texto;
  $texto =~ s/[^0-9a-z\*\?\-\"]/ /g; # 1.24
  # 1.8 Si no hay letras validas, retorna al tiro.
  if ($texto !~ /[0-9a-z]{2}/) {
    return(\@yeswords,\@notwords,1,\@frases);
  };
  # 1.27.2 Si esta definido el archivo, loguea la busqueda.
  if ($CFG{'SEARCH_LOGFILE'} ne '') {
    if ( open(LOG,'>>'.$DOCUMENT_ROOT.$CFG{'SEARCH_LOGFILE'}) ) {
      print LOG &lib_search::timestamp_iso() . ' ' . $ENV{'REMOTE_ADDR'} . ' ' . $texto . "\n";
      close LOG;
    };
  };
  # 1.24 Detecta las frases.
  while ($texto =~ /\"([^\"]+)\"/g) {
    $frase = $1;
    $frase =~ s/[^0-9a-z]/ /g; # Depura la frase. Elimina stopwords, wildcards, etc.
    $frase =~ s/(^| )[0-9a-z]( |$)/ /g; # Elimina letras sueltas.
    $frase =~ s/ +/ /g; # Elimina los espacios multiples.
    push @frases, $frase;
  };
  if ($#frases >= 0) { @NOBUSCAR = (); }; # Cuando se busca por frases se busca por todo.
  # 1.24 Por el momento no hay mas procesamiento con las frases, lo cual significa que
  #      si alguien metio un comodin o una stopword dentro de la frase, habra resultados
  #      incorrectos.
  $texto =~ s/\"/ /g; # 1.24 Elimina las comillas.
  $texto =~ s/^ +//g; # 1.24 Elimina los espacios de adelante.
  $texto =~ s/ +$//g; # 1.24 Elimina los espacios de atras.
  $texto =~ s/ +/ /g; # 1.24 Elimina los espacios multiples.
  if ($DEBUG) { print "texto=[$texto]\n"; };
  @searchwords = split(/ /,$texto);
  # Detecta los "nots", valida palabras y procesa wildcards: * y ?
  $turbomode = 1; # TURBOMODE=1 => no hay wildcards. Es busqueda exacta.
  @notwords = ();
  foreach $palabra (@searchwords) {
    # Omite la palabra si tiene menos de dos caracteres significativos.
    $caracteres = $palabra;
    $caracteres =~ s/[^0-9a-z]//g;
    next if (length($caracteres) < 2);
    next if (grep {$_ eq $caracteres} @NOBUSCAR); # 1.14
    # Detecta stop words.
    if (substr($palabra,0,1) eq '-') {
      $palabra = substr($palabra,1);
      # Detecta wildcards si es que estan habilitadas.
      if ( (lc $FORM{'search_comodines'}) eq 'yes') {
        if ( ($palabra =~ s/\*/\.\*/g) || ($palabra =~ s/\?/\./g) ) {
          $turbomode = 0;
        };
      }else{
        # Elimina wildcards.
        $palabra =~ s/[\*\?]+//g;
      };
      push @notwords, $palabra;
      # print "Not word: $palabra\n"; # debug
    }else{
      # Detecta wildcards si es que estan habilitadas.
      if ( (lc $FORM{'search_comodines'}) eq 'yes') {
        if ( ($palabra =~ s/\*/\.\*/g) || ($palabra =~ s/\?/\./g) ) {
          $turbomode = 0;
        };
      }else{
        # Elimina wildcards.
        $palabra =~ s/[\*\?]+//g;
      };
      # 1.27.2 Separa palabras compuestas por guiones para no buscarlas como una sola palabra,
      # ya que el indexador no las considera como una sola palabra.
      @aux = ();
      if (@aux = split(/-/,$palabra)) {
        push @yeswords, @aux;
      }else{
        push @yeswords, $palabra;
      };
      # print "Yes word: $palabra\n"; # debug
    };
  };
  if ($turbomode == 0) {
    foreach $palabra (@yeswords) {
      $palabra = "\^$palabra\$"; # Agrega delimitadores regexp.
    };
    foreach $palabra (@notwords) {
      $palabra = "\^$palabra\$"; # Agrega delimitadores regexp.
    };
  };
  return(\@yeswords,\@notwords,$turbomode,\@frases);
}; # depura_palabras

# -------------------------------------------------------------------------#
# Lee el indice de letras.
sub leeletras {
  my($idxdir) = $_[0];
  my($letra,$posicion);
  # Lee indice de letras.
  if (-f "$idxdir/$CARS_FILENAME") { # 1.27.2
    open (IN,"<$idxdir/$CARS_FILENAME");
    while (<IN>) {
      chomp;
      ($letra,$posicion) = split(/=/,$_);
      $LETRAS{$letra} = $posicion;
    };
    close IN;
  };
}; # leeletras

# ------------------------------------------------------------------------- #
# 1.10 Elimina los archivos de mas de 10 minutos de antiguedad.
sub garbageCollection {
  my($eldir) = $_[0];
  my(@entries);
  # Abre directorio.
  if (opendir(DIR, $eldir)) {
    @entries = readdir(DIR);
    closedir DIR;
    foreach my $file (@entries) {
      # Por seguridad, solo limpia archivos con la firma de esta aplicacion.
      next if ($file !~ /search/);
      # Detecta si son archivos.
      if (-f "$eldir/$file") {
        if ((stat("$eldir/$file"))[9] < (time - 600)) {
          unlink "$eldir/$file";
        };
      };
    };
  };
}; # garbageCollection

# ------------------------------------------------------------------------- #
# 1.10 Escribe y entrega el archivo temporal.
sub muestraResultado {
  my $answerid = 'search' . time . $$;
  &lib_search::escribe_archivo("$CACHE_DIR/$answerid\.$EXT",$RESULTADO);
  if ($ENV{'SERVER_SOFTWARE'} =~ /nginx/i) { # 1.31
    print "X-Accel-Redirect: $CACHE_REL_DIR/$answerid\.$EXT\n\n";
  }else{
    print "Location: $CACHE_REL_DIR/$answerid\.$EXT\n\n";
  };
  &garbageCollection($CACHE_DIR); # Limpia directorio de cache.
  exit;
}; # muestraResultado

# -------------------------------------------------------------------#
# 1.24 Comprueba si la secuencia se cumple para el archivo.
# Los parametros son un arreglo de palabras y una linea del archivo xxx:
# &matchSequence(\@wordSequence,$linea);
sub matchSequence() {
  my($wordSeq,$line) = @_;
  my @wordSequence = @$wordSeq;
  my($widx,@words,@sequences,$i,$j,$k,$ubi2match,$ubi,@matches1,@matches2,$matched);
  # Extrae las secuencias de cada palabra, o sea, la lista de ubicaciones de esa palabra dentro del archivo,
  # representado por la linea $line que es asi: |id_palabra1 ubic11 ubic12 ubic13 ...|idpalabra2 ubic21 ubic22 ...
  foreach $widx (@wordSequence) {
    if ($DEBUG) { print "widx=[$widx]\n"; };
    # Extrae parte de la linea que contiene la palabra.
    if ($line =~ /\|$widx ([^\|]+)/) {
      if ($DEBUG) { print "Encuentra $1\n"; };
      push @sequences, [ split(/ /,$1) ];
    }else{
      if ($DEBUG) { print "palabra no esta en $line\n"; };
      return 0; # No hay match pq la palabra no se encuentra en la linea.
    };
  };
  # Matchea cada secuencia con la siguiente hasta encontrar 1 match.
  # Para que la frase exista dentro del archivo se debe dar que al menos una de las series de ubicaciones
  # debe ser consecutiva, o sea, p. e., ubic12 + 1 = ubic21; ubic21 + 1 = ubic34 y asi ...
  # Para determinar esto hay que verificar todos los "caminos" posibles, partiendo del primer
  # conjunto de ubicaciones, comparando con el siguiente conjunto para encontrar numeros que sean sucesivos.
  $matched = 0;
  @matches1 = @{$sequences[0]}; # Parte con todas las primeras palabras matcheando.
  for($i=0;$i<$#sequences;$i++) {
    # Matchea cada ubicacion de la secuencia i contra las ubicaciones de las secuencias i+i.
    @matches2 = ();
    for($j=0;$j<=$#{$sequences[$i]};$j++) {
      # Solo explora el nivel si fue matcheado.
      if (grep {$sequences[$i][$j] == $_} @matches1) {
        $ubi = $sequences[$i][$j];
        $ubi2match = $ubi + 1;
        if ($DEBUG) { print 'busca ' . $sequences[$i][$j] . ":\n"; };
        for($k=0;$k<=$#{$sequences[$i+1]};$k++) {
          # if ($DEBUG) { print '  ' . $sequences[$i+1][$k]; };
          if ($ubi2match == $sequences[$i+1][$k]) {
            if ($DEBUG) { print $sequences[$i+1][$k] . " esta! "; };
            push @matches2, $sequences[$i+1][$k]; # Recuerda que este nivel fue matcheado.
            # Si se trata del ultimo elemento en la secuencia, entonces da por matcheada la frase y sale.
            if (($i+1) == $#sequences) {
              $matched = 1;
              last;
            };
          }else{
            # if ($DEBUG) { print " NO esta! "; };
          };
        };
        if ($DEBUG) { print "\n"; };
      };
    };
    @matches1 = @matches2;
  };
  if ($matched == 1) {
    if ($DEBUG) { print "\nFrase encontrada en $line\n"; };
    return 1;
  }else{
    if ($DEBUG) { print "\nFrase NO encontrada en $line\n"; };
    return 0;
  };
}; # matchSequence

# -------------------------------------------------------------------#
# Rescata y valida las variables del chorro.
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
    $value =~ s/%00//sg; # 1.17
    $value =~ s/%([0-9A-Ha-h]{2})/pack("c",hex($1))/ge;
    # 1.9 $value =~ s/~!/ ~!/g;
    $value =~ s/\.\.\///g; # 1.4 Elimina toda referencia de directorios hacia atras.
    # 1.9 $value =~ s/\|//g;     # 1.4 Elimina toda posibilidad de activar pipes.
    $value =~ s/\x00//g;   # 1.4 Elimina nulls.
    $value =~ s/\x1B//g;   # 1.4 Elimina escapes.
    $value =~ s/[<>%!\|\\\~\$]/ /g; # 1.9 Elimina caracteres peligrosos
    # $value =~ s/[\+\.\^\$\(\)\[\]\{\}\|\\]//g;   # 1.8 Elimina caracteres reservados de Perl.
    $name = lc $name; # 1.3
    # print "$name = [$value]\n"; # debug
    if ( ($name ne 'search_seccion') && ($name ne 'search_tema') && ($name ne 'search_subtema') ) { # 1.3
      $FORM{$name} = lc $value;
    }else{
      $FORM{$name} = $value;
    };
  };
  # Valida variables.
  $FORM{'search_prontus'} =~ s/[^\w\-]//g; # 1.20 1.8 Elimina todos los eslaishes y caracteres raros (sorry, solo sirve para Prontus ubicados en la raiz del sitio).
  $FORM{'search_tmp'} =~ s/[^\w\-\.]//g; # 1.18 1.4 Elimina caracteres no validos como nombres de archivo.
  if ($FORM{'search_tmp'} eq '')     { $FORM{'search_tmp'} = 'search.html'; };
  $FORM{'search_idx'} =~ s/[^\w\-\.]//sg; # 1.18
  if ($FORM{'search_idx'} eq '')     { $FORM{'search_idx'} = $FORM{'search_prontus'}; };
  $FORM{'search_resxpag'} =~ s/[^0-9]//sg; # 1.18
  if ($FORM{'search_resxpag'} eq '') { $FORM{'search_resxpag'} = 20; };
  $FORM{'search_maxpags'} =~ s/[^0-9]//sg; # 1.18
  if ($FORM{'search_maxpags'} eq '') { $FORM{'search_maxpags'} = 20; };
  $FORM{'search_pag'} =~ s/[^0-9]//sg; # 1.18
  if ($FORM{'search_pag'} eq '')     { $FORM{'search_pag'} = 1; };
  $FORM{'search_orden'} =~ s/[^\w]//sg; # 1.18
  if ($FORM{'search_orden'} eq '')   { $FORM{'search_orden'} = 'cro'; };
  $FORM{'search_form'} =~ s/[^\w]//sg; # 1.18
  if ($FORM{'search_form'} eq '')    { $FORM{'search_form'} = 'yes'; };
  $FORM{'search_modo'} =~ s/[^\w]//sg; # 1.18
  if ($FORM{'search_modo'} eq '')    { $FORM{'search_modo'} = 'and'; };
  $FORM{'vista'} =~ s/[^\w]//sg; # 1.18
  $VISTA = ''; # 1.18
  if ($FORM{'vista'} ne '')    { $VISTA = '-' . $FORM{'vista'}; }; # 1.18
  if (($FORM{'search_seccion'} ne '')
      || ($FORM{'search_tema'} ne '')
      || ($FORM{'search_subtema'} ne '')
      || ($FORM{'search_fechaini'} ne '')
      || ($FORM{'search_fechafin'} ne '')
      || ($FORM{'search_meta1'} ne '')
      || ($FORM{'search_meta2'} ne '')
      || ($FORM{'search_meta3'} ne '')
     ) { # 1.7
    $FILTROACTIVO = 1;
  }else{
    $FILTROACTIVO = 0;
  };
  if (length($FORM{'search_texto'}) > 64) {
    $MSG = 'B&uacute;squeda no v&aacute;lida.';
    $FORM{'search_texto'} = '';
  };
  if ($FORM{'search_fechaini'} ne '') {
    $FORMfechaini = &lib_search::fecha2iso($FORM{'search_fechaini'});
    # CVI - Para limpiar/formatear la fecha
    if($FORMfechaini eq '') {
		$FORM{'search_fechaini'} = '';
	} else {
		$FORM{'search_fechaini'} = &lib_search::iso2fechacorta($FORMfechaini);  
	}
  };
  if ($FORM{'search_fechafin'} ne '') {
    $FORMfechafin = &lib_search::fecha2iso($FORM{'search_fechafin'});
    # CVI - Para limpiar/formatear la fecha
    if($FORMfechaini eq '') {
		$FORM{'search_fechafin'} = '';
	} else {
		$FORM{'search_fechafin'} = &lib_search::iso2fechacorta($FORMfechafin);  
	}
  };
  
  # CVI - se limpian las variables restantes
  $FORM{'search_comodines'} =~ s/[^\w]//sg;
  if ($FORM{'search_comodines'} ne 'yes')    { $FORM{'search_comodines'} = 'no'; };
  
  # print "<p>FILTROACTIVO = $FILTROACTIVO $FORMfechaini $FORMfechafin"; # debug
}; # getFormData
