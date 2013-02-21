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
use lib_multiediting;
use glib_dbi_02;
use glib_fildir_02;
use DBI;
use lib_dd;

my ($BD, $RESTAR_ARTICS_PUB, %TABLA_SECC);
my (%HASH_NOMPORTS);
# ---------------------------------------------------------------
# MAIN.
# -------------
  # print STDERR "\n" . &get_time('Inicio');


main: {

    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_port'} = &glib_cgi_04::param('_port'); # portada.html
    $FORM{'_edic'} = &glib_cgi_04::param('_edic');
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    print "Cache-Control: no-cache\n";
    print "Cache-Control: max-age=0\n";
    print "Cache-Control: no-store\n";
    print "Content-Type: text/html\n\n";

    my $dir_cache = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache";
    my $file_cache = "listpub_" . $prontus_varglb::USERS_ID . "_$FORM{'_edic'}-$FORM{'_port'}";
    $file_cache =~ s/[^\w\-]//g;
    my $path_cache = "$dir_cache/$file_cache.html";

    if (-s $path_cache) {
        my $buffer_cache = &glib_fildir_02::read_file($path_cache);
        $buffer_cache = &port_dd_check_compatible($buffer_cache);
        print $buffer_cache;
        exit;
    };

    # CVI - 06/02/2012 - Se carga el Hash de Articulos publicados en portadas
    %HASH_ARTIC_PUBS = &lib_prontus::load_artic_pubs();

    my $buffer = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/prontus_art_listpub.html");

    $buffer = &lib_prontus::set_coreplt_ppal($buffer);

    $buffer =~ /<!--area_loop-->(.*)<!--\/area_loop-->/is;
    my $area_loop = $1;
    my $lista_artic = &generar_lista_artic_pub($area_loop); # retorna la lista de artics ya parseada
    $buffer =~ s/<!--area_loop-->.*<!--\/area_loop-->/$lista_artic/s;
    $buffer =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/g;
    $buffer =~ s/%%_path_conf%%/$FORM{'_path_conf'}/g;

    $buffer = &port_dd_check_compatible($buffer);
    
    # Indicador de si hay alguien mas editando la portada
    my $id_session = &get_sess_id();
    my $nom_recurso_concurrency = &get_nom_recurso_concurrency();

    # envia ping
    &lib_multiediting::send_ping($prontus_varglb::DIR_SERVER,
                                 $prontus_varglb::PRONTUS_ID,
                                 $nom_recurso_concurrency,
                                 'port',
                                 $prontus_varglb::USERS_USR,
                                 $id_session);

    # ve si hay alguien mas editando el recurso
    my $concurrency = &lib_multiediting::get_concurrency( $prontus_varglb::DIR_SERVER,
                                                          $prontus_varglb::PRONTUS_ID,
                                                          $nom_recurso_concurrency,
                                                          'port',
                                                          $prontus_varglb::USERS_USR,
                                                          $id_session);

    $buffer =~ s/%%_concurrency%%/otros users editando esta port: $concurrency/g;


    $buffer =~ s/%%_port%%/$FORM{'_port'}/g;
    $buffer =~ s/%%_edic%%/$FORM{'_edic'}/g;


    $buffer =~ s/<!--\w.*?\w-->//sg;
    $buffer =~ s/<!--\/\w.*?\w-->//sg;
    my ($crlf) = $lib_prontus::CRLF;
    $buffer =~ s/>($crlf| )+</>\x0a</sg;
    $buffer =~ s/ +/ /sg;
    $buffer =~ s/($crlf)+/\x0a/sg;

    # CVI - 16/06/2011
    my $open_fid_in_pop = 'open_normally';
    if($prontus_varglb::ABRIR_FIDS_EN_POP eq 'SI') {
        $open_fid_in_pop = 'open_in_pop';
    }
    $buffer =~ s/%%_class_open_fid%%/$open_fid_in_pop/ig;
    
    my $portada_hdd = $prontus_varglb::DIR_SERVER . "/" . $prontus_varglb::PRONTUS_ID . "/site/edic/$FORM{'_edic'}/port/$FORM{'_port'}";
    print STDERR "portada: $portada_hdd\n";
    if(-f $portada_hdd) {
        #~ my $fh = open($portada_hdd);
        my $modtime = (stat($portada_hdd))[9];
        #~ my $localmodtime = localtime $modtime;
        $buffer =~ s/%%_localmodtime%%/$modtime/ig;
        print STDERR "localmodtime: $modtime\n\n";
        #~ print STDERR "buffer: $buffer\n\n";
        
        #~ eval "require POSIX;";  my $no_hay_libreria = $@;
        #~ unless($no_hay_libreria) {
        #~ 
            #~ use POSIX qw/strftime/;
            #~ 
            #~ my $moddate = strftime("%d/%m/%Y", );
            #~ my $modhour = strftime("%d/%m/%Y", localtime $modtime);
            #~ print STDERR "modtime: \n";
            #~ print STDERR "modtime: $modhuman\n";
            #~ 
            #~ my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
            #~ my $today = &glib_hrfec_02::fecha_human();
            #~ 
            #~ h	Formato de 12 horas de una hora con ceros iniciales	01 hasta 12
#~ H	Formato de 24 horas de una hora con ceros iniciales	00 hasta 23
#~ i	Minutos, con ceros iniciales	00 hasta 59
#~ s
#~ 
#~ <input type="hidden" name="_fecha_mod" value="%%_fecha_mod%%" />
#~ <input type="hidden" name="_hora_mod" value="%%_hora_mod%%" />
#~ 
                        #~ 
            #~ my ($)
        #~ }
    }
    
    $buffer =~ s/%%.*?%%//ig;
    
    #~ %%_fechahora_pub%%


    # Escribe cache
    &glib_fildir_02::check_dir($dir_cache);
    &glib_fildir_02::write_file($path_cache, $buffer);
    # print STDERR &get_time('Fin');

    print $buffer;

};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub get_nom_recurso_concurrency {
    my $nom_recurso = $FORM{'_edic'} . '-' . $FORM{'_port'};
    $nom_recurso =~ s/\.\w+$//; # borra ext.
    return $nom_recurso;
};
# ---------------------------------------------------------------
sub get_concurrency4port {
# Obtiene otros usuarios concurrentes a esta portada
    my $nom_recurso = shift;
    my $id_session  = shift;
    my $concurrency =
    return $concurrency;
};
# ---------------------------------------------------------------
sub get_sess_id {
    my $sess_obj = Session->new(
                    'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                    'document_root'     => $prontus_varglb::DIR_SERVER)
                    || die("Error inicializando objeto Session: $Session::ERR\n");
    return $sess_obj->{id_session};
};
# ---------------------------------------------------------------

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


#-------------------------------------------------------------------------#
sub read_file_ref {
# Lee un archivo por completo y devuelve la ref a el.

# Param. de entrada :
# 0) Path real del archivo.

# Retorna : El texto leido | '' en caso que el archivo no exista.

  my($archivo) = $_[0];
  my($size) = (-s $archivo);
  my($buffer) = '';

  if ((-s $archivo) and (! -d $archivo)) {
    open (ARCHIVO,"<$archivo")
      || die "Fail Open file $archivo \n $!\n";
    binmode ARCHIVO;
    read ARCHIVO,$buffer,$size;
    close ARCHIVO;

    my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
    $buffer =~ s/$crlf/\x0a/sg;
  };

  return \$buffer;

};

#-------------------------------------------------------------------------#
sub get_time {
  my $label = $_[0];
  my $dt = &glib_hrfec_02::get_dtime_pack4();
  $dt =~ /(\d{2})(\d{2})(\d{2})$/;
  return "\nHora $label [$1:$2:$3]";

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

            my ($dirfecha,$ts,$area,$prio,$ext_art,$pub, $vb) = '';
            ($dirfecha,$ts,$area,$prio,$vb,$pub) = ($1,$2,$3,$4,$6,$9);

            $HASH_ORDEN{$ts} = $prio; # 1.4
            $HASH_AREA{$ts} = $area; # 1.4
            $HASH_DIRFECHA{$ts} = $dirfecha; # aaaammdd Dir. corresp. al dia donde se ubica el articulo.

            $HASH_PUB{$ts} = $pub; # Indicador de si el art. esta o no publicado en el html

            $HASH_VB{$ts} = $vb;

            # $HASH_ARTICULOS{$art . $ext_art . '__' . $HASH_NOMPORTS{$entry}} = $area . '_' . $prio; #1.4

        }# while
    }# if

};# sub


# ---------------------------------------------------------------
sub generar_lista_artic_pub {
# Genera el html correspondiente a la lista de
# articulos publicados en la portada seleccionada.

    my $area_loop = shift;
    # print STDERR "area_loop[$area_loop]\n";

    # Dir destino de las portadas.
    my $path_port = $prontus_varglb::DIR_SERVER .
                    $prontus_varglb::DIR_CONTENIDO .
                    $prontus_varglb::DIR_EDIC .
                    "/$FORM{'_edic'}" .
                    $prontus_varglb::DIR_SECC .
                    "/$FORM{'_port'}";

    # Cargar en hash la info de articulos publicados en port actual
    &generar_hash_articulos_pub($path_port);

    # Detecta areas de la portada desde la plantilla ppal.
    my %hash_loops = &get_loops_from_plt(); # ret. nro. y nombre de cada area de la portada


    # Ordenar ascendentemente por area / orden / id articulo.
    my (@arr_art) = (keys %HASH_DIRFECHA); # arts publicados en esta portada.
    @arr_art = sort {$HASH_AREA{$a} <=> $HASH_AREA{$b} or $HASH_ORDEN{$a} <=> $HASH_ORDEN{$b} or $b <=> $a} (@arr_art);


    $area_loop =~ /<!--articulo_loop-->(.*)<!--\/articulo_loop-->/is;
    my $articulo_loop = $1;

    # Parsea cada area
    my $areas_parsed;

    foreach my $nro_area (sort{$a <=> $b}(keys %hash_loops)) {

        my $loop_tpl = $area_loop;
        my $nom_area = $hash_loops{$nro_area};
        $loop_tpl =~ s/%%_area%%/$nro_area/g;
        if ($nom_area eq '') {
            $loop_tpl =~ s/%%_areanom%%/$nro_area/g;
        } else {
            $loop_tpl =~ s/%%_areanom%%/$nro_area: $nom_area/g;
        };



        # Para esta area, parsear sus articulos.
        my $artics_parsed;
        foreach my $ts (@arr_art) {
            next if ($HASH_AREA{$ts} ne $nro_area);
            my $loop_art_tpl = $articulo_loop;

            my $area = $HASH_AREA{$ts};
            my $orden = $HASH_ORDEN{$ts};

            # Desformatear
            $area = sprintf("%0.0d",$area);
            $orden = sprintf("%0.0d",$orden);

            # Imprimir solo los art. que esten publicados con area y orden
            next if (($orden eq '0') || ($orden eq ''));

            $artics_parsed .= &get_artic_parsed($loop_art_tpl, $ts, $area, $orden);
        };# foreach artics

        $loop_tpl =~ s/<!--articulo_loop-->(.*)<!--\/articulo_loop-->/$artics_parsed/s;
        $areas_parsed .= $loop_tpl;

    };# foreach areas

    return $areas_parsed;

};# sub

# ---------------------------------------------------------------
sub get_loops_from_plt {
    # plantillas de port
    my $dir_tpl_port = $prontus_varglb::DIR_SERVER .
                       $prontus_varglb::DIR_TEMP .
                       $prontus_varglb::DIR_EDIC .
                       $prontus_varglb::DIR_NROEDIC .
                       $prontus_varglb::DIR_SECC;

    my $dir_macros = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/plantillas/edic/nroedic/macros";
    my $path_tpl = "$dir_tpl_port/$FORM{'_port'}";

    my $mv = '';
    my $buffer = &lib_prontus::carga_buffer_plt($path_tpl, $dir_macros, $mv);
    # print STDERR "buffer[$buffer]\n";
    my %loops;
    while ($buffer =~ /%%LOOP(\d+)(\(([^)]+)\))?%%.*?%%\/LOOP%%/isg) {
        my ($nro, $nombre) = ($1, $3);
        $loops{$nro} = $nombre;
    };
    return %loops;

};

# ---------------------------------------------------------------
sub get_artic_parsed {
    # 1.5
    # Genera html correspondiente a un articulo de la lista.

    my ($loop_art_tpl, $ts, $area, $orden) = @_;

    # Inicializa obj artic para leer XML
    my $artic_obj = Artic->new(
                    'prontus_id'=>$prontus_varglb::PRONTUS_ID,
                    'public_server_name'=>$prontus_varglb::PUBLIC_SERVER_NAME,
                    'cpan_server_name'=>$prontus_varglb::IP_SERVER,
                    'document_root'=>$prontus_varglb::DIR_SERVER,
                    'ts'=>$ts,
                    'campos'=>{}) || die "Error inicializando objeto articulo: $Artic::ERR\n";

    my %campos_xml = $artic_obj->get_xml_content();

    my $ts_art_ext = $artic_obj->get_nom_artic($campos_xml{'_plt'});

    my $path_artic = $artic_obj->get_fullpath_artic('', $campos_xml{'_plt'});


    # Art. inexistente
    if (! -f $path_artic) {
        $loop_art_tpl =~ s/%%_ts%%/$ts/g;
        $loop_art_tpl =~ s/%%_artic_sin_file%%/_artic_sin_file/g;
        $loop_art_tpl =~ s/%%_vobo_class_name%%/vobo_disabled/g;
        $loop_art_tpl =~ s/%%\w+?%%//g;
        return $loop_art_tpl;
    };
    $loop_art_tpl =~ s/%%_artic_sin_file%%//g;

    $loop_art_tpl =~ s/%%_area%%/$area/g;
    $loop_art_tpl =~ s/%%_orden%%/$orden/g;

    # status de publicacion
    my $st_pub = $HASH_PUB{$ts};
    if ($st_pub) {
        $st_pub = 'pub';
    } else {
        $st_pub = 'nopub';
    };
    $loop_art_tpl =~ s/%%_status_pub%%/$st_pub/g;

    my $st_vb = $HASH_VB{$ts};
    $st_vb = 1 if ($st_vb eq '');
    if ($st_vb) {
        $loop_art_tpl =~ s/%%_status_vobo%%/No publicar en esta portada/g;
        $loop_art_tpl =~ s/%%_vobo_st_img%%/pub/g;
    } else {
        $loop_art_tpl =~ s/%%_status_vobo%%/Publicar en esta portada/g;
        $loop_art_tpl =~ s/%%_vobo_st_img%%/nopub/g;
    };

    
    $loop_art_tpl =~ s/%%_vobo_class_name%%/vobo/g;
    $loop_art_tpl =~ s/%%_voboboto_class_name%%/voboboto/g;
    $loop_art_tpl =~ s/%%_vobo%%/$st_vb/g;

    # Campos del xml del artic

    my $fid = $campos_xml{'_fid'};
    my $users_id = $campos_xml{'_users_id'};
    my $art_autoinc = $campos_xml{'_art_autoinc'};
    $art_autoinc = '0' if ($art_autoinc eq '');
    my $alta = $campos_xml{'_alta'};
    my $titulo = $campos_xml{'_txt_titular'};

    $titulo = &lib_prontus::get_minitext_value($titulo);
    $titulo = &lib_prontus::escape_xml($titulo);

    my $nom_seccion = $campos_xml{'_nom_seccion1'};
    my $art_fechap = $campos_xml{'_fechap'};
    my $art_horap = $campos_xml{'_horap'};
    my $art_fechae = $campos_xml{'_fechae'};
    my $art_horae = $campos_xml{'_horae'};

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
  	  $marca_file = &lib_prontus::parse_filef('%%_FILEURL%%', $titulo, $ts, $prontus_varglb::PRONTUS_ID, $marca_file, $campos_xml{'_nom_seccion1'}, $campos_xml{'_nom_tema1'}, $campos_xml{'_nom_subtema1'});
  	}
    $loop_art_tpl =~ s/%%_file%%/$marca_file/g;
    $loop_art_tpl =~ s/%%_autoinc%%/$art_autoinc/g;
    $loop_art_tpl =~ s/%%_titular%%/$titulo/g;

    if ($nom_seccion) {
        $nom_seccion = "<b>Secci&oacute;n: </b> $nom_seccion";
    } else {
        $nom_seccion = "Sin Secci&oacute;n";
    };
    $loop_art_tpl =~ s/%%_nom_seccion%%/$nom_seccion/g;
    $loop_art_tpl =~ s/%%_labelfid%%/$glosa_tipo_ficha/g;

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

sub port_dd_check_compatible {
    my $buffer = $_[0];
    my $path_port_plt = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_TEMP . "/edic/nroedic/port/$FORM{'_port'}";
    my $path_port_site = $prontus_varglb::DIR_SERVER . "/" . $prontus_varglb::PRONTUS_ID . "/site/edic/$FORM{'_edic'}/port/dd_$FORM{'_port'}";
    if (&lib_dd::check_portada($path_port_plt, $path_port_site) eq '') {
        $buffer =~ s/%%_port_dd_compatible%%/1/g;
    } else {
        $buffer =~ s/%%_port_dd_compatible%%//g;
    };
    return $buffer;
};




# -------------------------------END SCRIPT----------------------
