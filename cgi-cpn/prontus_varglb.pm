#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

package prontus_varglb;

# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Definir e inicializar variables globales utilizadas en el Sistema
# Auto-Publicador.

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.1 - 05/07/2000 - Se agrega posibilidad de manipular archivos realmedia.
# 1.2 - 24/11/2000 - DEclaracion global de $PRONTUS_KEY, para que este disponible para .pl y .pm.
# 1.3 - 02/12/2000 - Nueva variable $EXTENSION_CGI, indica si el publicador se esta usando como .exe o .pl
# 1.4 - 15/05/2001 - Extensiones Prontus 5.(Estas se implementaron antes de efectuar esta documentacion).
# 1.5 - 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.6 - 16/05/2001 - Revision general de detalles de forma.

# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0

# Prontus 8.0 - 13/05/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# Prontus 8.1 - 09/09/2002 - YCH - Soporte windows media. Ver detalles en /release_prontus81.txt
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# Especial DRs - 08/01/2004 - YCH - Agrega soporte Antialone (parseo de antialone_tmp.html) analogo a lanacion.cl.
# -------------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------


sub init { # Prontus 6.0
  # dir_cgi.pm trae algo como:
  # $DIR_CGI_CPAN = 'cgi-cpn';
  # $DIR_CGI_PUBLIC = 'cgi-bin'; # 1.13
  require 'dir_cgi.pm';

  $VERSION_PRONTUS = '11.2.60 - 05/03/2013';
  $RAMA_INSTALADA = '';
  $NRO_REVISION_INSTALADA = '';
  $BETA_REVISION_INSTALADA = '';
  &set_info_version_prontus();


  $MSG_BLOQUEOSYSADMIN = 'Este Administrador de Contenidos se encuentra actualmente en mantención, para mayor información comuníquese con el Webmaster.';

  $MAX_NRO_ARTIC = '';
  $RTEXT_ENABLED = '';
  $PORT_INI_SELECTED = '';
  $PORT_HOME = '';

  $UPLOADS_PERMITIDOS = '';
  $UPLOADS_PERMITIDOS_ORIG = 'jpg,jpeg,jpe,gif,png,bmp,tif,tiff,ico,asf,asx,wax,wmv,wmx,avi,divx,flv,mov'
                       . ',qt,mpeg,mpg,mpe,3gp,txt,rtx,css,htm,html,mp3,m4a,mp4,m4v,ra,ram,wav,ogg,mid'
                       . ',midi,wma,rtf,pdf,doc,docx,pot,pps,ppt,pptx,wri,xla,xls,xlsx,xlt,xlw,mdb'
                       . ',mpp,swf,tar,zip,gz,gzip,odt,odp,ods,odg,odc,odb,odf';

  $BD_CONN = '';

  $IP_SERVER = $ENV{'HTTP_HOST'};

  # Determinar Dir del server.
  $DIR_SERVER = &get_dir_server();

  $MOTOR_BD = ''; # MYSQL | PRONTUS

  # Parametros de conexion a BD
  $MOTOR_BD = '';
  $NOM_BD = '';
  $USER_BD = '';
  $PWD_BD = '';
  $SERVER_BD = '';

  # Taxonomia
  $TAXONOMIA_NIVELES = '';
  $CONTROLAR_ALTA_ARTICULOS = '';
  $NUM_RELAC_DEFAULT = '';
  $DIR_TAXONOMIA = '/cache/taxonomia/pags'; # cuelga de <prontus_id>/<dir_temp>|<dir_contenido>/
  $DIR_PTEMA = '/tax/port'; # cuelga de <prontus_id>/<dir_temp>|<dir_contenido>/
  $DIR_PTEMA_MACROS = '/tax/macros';

  # [NRO DE ART. POR PAGINA QUE APARECERAN EN LAS TAXPORTS]
  $TAXPORT_ARTXPAG;

  # SORT ORDER DE TAXPORTS
  $TAXPORT_ORDEN;

  # VALIDACION DE SEGURIDAD PARA TAXPORT_MAXARTICS
  $TAXPORT_MAXARTICS_SECURITY = 100000;

  # [CANTIDAD DE SEGUNDOS DE ANTIGUEDAD MAXIMA QUE TENDRAN LAS TAXPORTS]
  #~ $TAXPORT_REFRESH_SEGS;

  # Tiene que cambiar esto
  $ABRIR_FIDS_EN_POP = '';

  # 8.0
  $PERIODISTA_VER_ARTICULOS_AJENOS = '';
  $PERIODISTA_EDITAR_ARTICULOS_AJENOS = '';

  $EDITOR_VER_ARTICULOS_AJENOS = '';
  $EDITOR_EDITAR_ARTICULOS_AJENOS = '';

  $DEFAULT_TITHTML = '<A NAME=%%_SUBTIT_ANAME%%>%%_SUBTIT%%</A><a href="#top" class="linkSubtit">&nbsp;|&nbsp;subir</a>';

  $STAMP_DEMO = '';
  $STAMP_DEMO_RSS = '';
  $SERIE_DEMO = 'DEM';
  $ORDEN_LISTA_ARTICULOS = '';

  $PRONTUS_EDITOR = '';
  $ACTUALIZACION_MASIVA = '';
  $VERIFICAR_INSTALACION = '';

  $ADMIN_BASEDATOS = '';
  $ADMIN_BUSCADOR = '';

  $COMENTARIOS = '';

  $SCRIPT_QUOTA = '';
  $FOTO_MAX_PIXEL = '';
  $BLOQUEO_EDICION = '0';


  # Prontus 6.0
  my %USERS = ();
  my %ARTUSERS = ();
  my %PORTUSERS = ();

  $FOTOS_ARTIC_SI_IMG = 'fotos_artic_si';
  $FOTOS_ARTIC_NO_IMG = 'fotos_artic_no';
  $ARTIC_PUB_SI_IMG = 'port_artic_si';
  $ARTIC_PUB_NO_IMG = 'port_artic_no';

  # Directorios correspondientes al contenido de las paginas generadas por el autopublicador,
  # relativos al publicador
  $DIR_CONTENIDO = '/site';

  $DIR_LIST = '/list/port';
  $DIR_LIST_MACROS = '/list/macros';
  $DIR_ARTIC = '/artic';
  $DIR_FECHA = '/fecha';
  $DIR_PAG = '/pags'; # Dir. donde se almacenaran las paginas generadas
  $DIR_IND = '/pags/subtit';
  $DIR_SECC = '/port';   # Dir. de portadas
  $DIR_SPARE = '/port_recambio';   # Dir. de portadas de recambio
  $DIR_MACROS = '/macros';   # Dir. de portadas
  $DIR_IMAG = '/imag';   # Dir. donde se almacenaran las imagenes incluidas por el autopublicador en las paginas generadas
  $DIR_SWF = '/swf';   # Dir. donde se almacenaran las SWF incluidas por el autopublicador en las paginas generadas # 8.0
  $DIR_RTEXT = '/rtext';   # Dir. donde se almacenaran las fotos del rtext # rc15

  $DIR_WMEDIA = '/wmedia';   # 8.1 # Dir. donde se almacenaran los archivos de windows media incluidos en las paginas publicadas.
  $DIR_MMEDIA = '/mmedia';   # Dir. donde se almacenaran los archivos de windows media incluidos en las paginas publicadas.

  $DIR_RMEDIA = '/rmedia';   # 1.1 # Dir. donde se almacenaran los archivos de real media incluidos en las paginas publicadas.
  $DIR_ASOCFILE = '/asocfile';   # 1.2 # Dir. donde se almacenaran los archivos genericos asociados en las paginas publicadas.

  $DIR_FSET_PAG = '/fset';   # Dir. donde se almacenaran los framesets apuntando al indice y a la pagina, cuando se trate de Menu de subtitulos en pag aparte.

  # Directorios correspondientes a los templates, relativos al publicador
  $DIR_TEMP = '/plantillas';

  # Directorios del panel de control, relativos al server, donde estan los formularios usados por el autopublicador.
  $DIR_CPAN = '/cpan';
  $DIR_CORE = '/cpan/core';

  $MULTI_EDICION = '';

  $EDICBASE_INI_SELECTED = '';
  $SERVER_SMTP = '';


  # Directorios correspondientes al contenido del sitio web, relativos a $DIR_CONTENIDO
  $DIR_HPAGES = '/home';
  # $DIR_MENU = '/menu';
  $DIR_EDIC = '/edic';
  $DIR_NROEDIC = '/nroedic';
  $DIR_UNICAEDIC = '/base';

  $BANCO_IMG_MAX = 8;


  # Nombre del template de homepage de cada edicion, ubicado dentro del dir $DIR_HPAGES del dir. de los templates ($DIR_TEMP)
  # 8.0 Se toma el primer arch. que se encuentre en el directorio y se usa ese nombre, salvo para el wizard.
  $INDEX_EDIC = 'home.html';

  $INDEX_SITIO = 'index.html'; # En la raiz del sitio, este es el index que es manipulado por
                                # por el Adm. de Ediciones para setear la ed. vigente.
                                # El template es index_tmp.shtml SOLO MULTI-ED
  $TPL_INDEX_SITIO = 'index_tmp.html';        # SOLO MULTI-ED
  $ANTIALONE       = 'antialone.html';        # 9.0 SOLO MULTI-ED
  $TPL_ANTIALONE   = 'antialone_tmp.html';    # 9.0 SOLO MULTI-ED

  $TITLE_INDEX = '';

  $PAG_WORKING = 'working.html'; # Relativo a $DIR_SERVER, esta pagina se usa para inicializar las secciones antes de que se empiece a publicar en ellas.   SOLO MULTI-ED

  @MENUS_EDIC = (); # nombres de los archivos con ext. y sin path correspondientes a los menus de edicion.

  # Relacion entre formularios de ingreso de articulos y templates de articulos utilizados por c/formulario.
  # Las claves del hash son los .html correspondientes a los formularios de ingreso/modif de articulos.
  # Los valores del hash son listas de .htmls separadas por ';'factibles de usar como templates en cada formulario.
  # Ejemplo :  $FORM_PLTS{'ap_art_ficha_act.html:Actividades'} = 'actividades1.html;actividades1.html';
  %FORM_PLTS = ();


  # Relacion entre templates de portadas y plantillas spare de cada una.
  # Las claves del hash son los .html correspondientes a las portadas.
  # Los valores del hash son listas de .htmls separadas por ';'factibles de usar como plantillas spare para cada portada.
  # Ejemplo :  $PORT_PLTS{'portada.html'} = 'portada_domingo.html;portada_lunes.html';
  %PORT_PLTS = ();

  %MULTIVISTAS = ();

  %POST_PROCESO = ();

  # Portadas publicables en la edición base.
  @BASE_PORTS = ();


  # Lista de servidores permitidos (informacion usada para validacion de referers).
  # se configura en el .cfg con lineas de la forma SERVER_NAME = 'www.australvaldivia.cl'
  @SERVER_NAME = ();
  # EJEMPLO : $SERVER_PERM[0] = '192.168.1.74';

  # Para conocimiento de todos los scripts y librerias.
  $PRONTUS_KEY = '';

  # 1.3
  $EXTENSION_CGI = 'cgi';

  # Valores por defecto para la construccion de las tablas
  $STAB_DEFAULT = '30%,3,1,0,#ffdd99,#FFFFFF,#FFFFFF,LEFT,RECU';
  # (ancho, padding, borde, spacing, color 1ra fila, color 1ra columna, color fondo,
  #  alineamiento, y estilo a aplicar (CSS) a la tabla). Este se utiliza en caso de que los
  # seteos de la tabla no vengan en el template como <!--STABi=....-->.
  # Ademas de lo anterior se utilizan los css P.TFLIN, P.TFCOL, P.TCELL, P.TSPAN para
  # definir los estilos de texto de la 1a. fila, 1a. columna, resto de las celdas, y celdas
  # con colspan > 1, respectivamente.


  # 8.1
  $WMEDIA_LINK = '<img src="%%path%%/wmedia.gif" border="0" alt="Reproducir">'; # Cod. html que se linkeara con el arch. windows media en el Articulo. (En la portada, esto se pone en el template.)

  # 1.1
  $RMEDIA_LINK = '<img src="%%path%%/rmedia.gif" border="0" alt="Reproducir">'; # Cod. html que se linkeara con el arch. realmedia en el Articulo. (En la portada, esto se pone en el template.)

  # 1.2
  $ASOCFILE_LINK = '<img src="%%path%%/afile.gif" border="0" alt="Ver / Bajar Archivo">'; # Cod. html que se linkeara con el arch. asociado en el Articulo. (En la portada, esto se pone en el template.)

  # 1.3
  # $LINK_MAS = '<img src="%%path%%/mas.gif" border="0" alt="Más información...">'; # Cod. html que se linkeara con el link 'mas' que va al detalle del articulo.
  $LINK_MAS = ''; # Cod. html que se linkeara con el link 'mas' que va al detalle del articulo.

  # Las marcas %%path%% se reemplazan al momento de cargar el cfg del prontus.


  $USERS_PERFIL = ''; # 1.4

  $DIR_DBM = '';  # 1.4


  # Prontus 6.0
  $USERS_ID = '';
  $TIPO_PRONTUS = '';
  $AREA_MENU = '';
  $AREA_CONT = '';
  $PRONTUS_KEY = '';

  $USERS_USR = ''; # se carga con el nombre de usuario al realizar el login.


  # Prontus 6.0

  $FECHA_HOY = ''; # Se carga en funcion check_dirs() lib_prontus.pm
  $TS_PREVIEW = ''; # Se recibe al previsualizar portada con prontus ctrl. fecha.


  # Mostrar en la adm. de articulos y ediciones las xx ultimas ediciones, ordenadas por tmstamp
  $NRO_EDICS_WORK = 10000;
  $DIR_LOG = ''; # Dir. absoluto al dir donde se deja el log del publicador.
  $PRONTUS_LOG = ''; # SI | NO.

  $ADMIN_PORT = '';


#
#   <NOTAS>
# <![CDATA[
#
# There are 5 predefined entity references in XML:
# Regla uno (R1):
# &lt; < less than
# &gt; > greater than
# &amp; & ampersand
# &apos; ' apostrophe
# &quot; " quotation mark
# ]]>
#
#   </NOTAS>
#


# "<?xml version='1.0' encoding='iso-8859-1'?>
# <PORT_DATA>
#      <rowartic>
#        <dir></dir>
#        <file></file>
#        <area></area>
#        <ord></ord>
#        <vb></vb>
#        <pub></pub>
#      </rowartic>
# </PORT_DATA>";


};



#------------------------------------------------------------------------#
sub get_dir_server {
  # DIR_SERVER:
  #   En unix queda algo asi como /sites/misitio.cl/web
  #   En win queda algo asi como c:/sites/misitio.cl/web

    my $dir_server = $ENV{'DOCUMENT_ROOT'};  # Unix y Abyss
    $dir_server =~ s/\\/\//g; # cambia \ por /, por si win
    if ($dir_server eq '') {
        use FindBin '$Bin';
        $dir_server = $Bin; # por ej /sites/misitio.cl/web/cgi-cpn
        $dir_server =~ s/\\/\//g; # cambia \ por / por si es win
        # Queda por ej /sites/misitio.cl/web, se asume que el script q use este varglb siempre
        # estara en la carpeta cgi-xxx o similar, pero nunca mas niveles hacia adentro.
        $dir_server =~ s/\/[^\/]+$//;
    };

    # cvi - 26/07/2011 - para eliminar los slash del final
    $dir_server =~ s/\/+$//;

    if ((! -d $dir_server) || (!$dir_server)) {
        if ($ENV{'SERVER_NAME'} ne '') { # ambiente web
            print "Content-Type: text/html\n\n";
        };
        print 'Error, no se ha podido detectar DOCUMENT ROOT o éste no es válido';
        exit;
    };

    return $dir_server;
};
# ---------------------------------------------------------------
sub set_info_version_prontus {
    my ($version_prontus) = $prontus_varglb::VERSION_PRONTUS;
    if ($version_prontus =~ /([0-9]+\.[0-9]+)\.([0-9]+)(\.beta)?/) {
        $RAMA_INSTALADA = $1;
        $NRO_REVISION_INSTALADA = $2;
        $BETA_REVISION_INSTALADA = $3;
    };
};
# -------------------------------END LIBRERIA--------------------


# FIN DOC.


return 1;

