#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

#-------------------------------COMENTARIO GLOBAL---------------
#---------------------------------------------------------------
# PROPOSITO.
#-----------
# Funciones para Carga de configuraciones sist. comentarios.

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 1.0 - ycc - 10/2006 - Primera version.
# 1.1 - cvi - 21/08/2008 - Agrega creación de archivo con total de comentarios.
# 1.2 - ycc - 16/06/2009 - Cambia estructura de almacenamiento de pags y agrega opcion ID_STYLE
# 1.3 - ycc - 24/08/2009 - Agrega parametros para captcha y envio de mail de publicacion
#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package lib_coment;

use lib_prontus;
use glib_fildir_02;
use glib_hrfec_02;
use strict;
my $CRLF = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
#----------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
#sub get_bd_params {
#  # Obtiene params de conex a BD
#  my $dir_server = $_[0];
#  my $path_cfg = "$dir_server/coment/cpan/cfg/base.php";
#  # print STDERR "[$path_cfg]";
#  my ($name, $id);
#  my $buffer = &glib_fildir_02::read_file($path_cfg);
#  $buffer =~ s/$CRLF/\n/sg;
#  my ($nom_bd, $server_bd, $user_bd, $pwd_bd);
#
#  if ($buffer =~ /\$NOM_BD\s*=\s*("|')(.+?)("|');/) {
#    $nom_bd = $2;
#  };
#
#  if ($buffer =~ /\$USER_BD\s*=\s*("|')(.+?)("|');/) {
#    $user_bd = $2;
#  };
#
#  if ($buffer =~ /\$PWD_BD\s*=\s*("|')(.+?)("|');/) {
#    $pwd_bd = $2;
#  };
#
#  if ($buffer =~ /\$SERVER_BD\s*=\s*("|')(.+?)("|');/) {
#    $server_bd = $2;
#  };
#
#  # print STDERR "[$buffer]";
#  # print STDERR "($nom_bd, $server_bd, $user_bd, $pwd_bd)\n";
#  return ($nom_bd, $server_bd, $user_bd, $pwd_bd);
#
#
#};
# ---------------------------------------------------------------
sub get_objtipos {
  # Lee cfg  y genera options para combo y hash con los tipos de objetos
  # Hash: key: id del tipo de objeto. value:
    my $dir_server = $_[0];
    my $id_seleccionado = $_[1];
    my $instancia_prontus = $_[2];
    my $path_cfg = "$dir_server/$instancia_prontus/cpan/$instancia_prontus-coment.cfg";
    my ($name, $id);
    my $buffer = &glib_fildir_02::read_file($path_cfg);
    $buffer =~ s/$CRLF/\n/sg;

    $buffer =~ s/\s*#.*$//gm; # elimina lineas con comentarios

    my ($options, %hash_tipos);

    while ($buffer =~ /\[(\w+)\](.*?)\[\/\1\]/sg) {

        my $id = $1;
        my $obj_data = $2;
        my ($nom, $url, $plt, $limit, $dir_pags_coment, $msg_moder, $msg_nomoder, $filasxpag_public);
        my ($php_session_name, $php_session_path);

        # ID_STYLE
        my ($id_style) = 'TIMESTAMP';
        if ($obj_data =~ /\s*ID_STYLE\s*=\s*("|')(.*?)("|')/) {
            $id_style = uc $2;
        };
        if ($id_style !~ /^(TIMESTAMP|NUMERIC)$/) {
            $id_style = 'TIMESTAMP';
            print STDERR "En conf de objeto [$id], no se especifica valor para la variable, se setea ID_STYLE = 'TIMESTAMP' (valor por omision)\n"
            # return ('', "Error al cargar configuraci&oacute;n de objeto [$id]. El par&aacute;metro ID_STYLE debe ser TIMESTAMP o NUMERIC.", '');
        };

        # PHP_SESSION_NAME
        if ($obj_data =~ /\s*PHP_SESSION_NAME\s*=\s*("|')(.*?)("|')/) {
            $php_session_name = $2;
        };
        if ($php_session_name eq '') {
            $php_session_name = 'PHPSESSID';
        };

        # PHP_SESSION_PATH
        if ($obj_data =~ /\s*PHP_SESSION_PATH\s*=\s*("|')(.*?)("|')/) {
            $php_session_path = $2;
        };


        if ($php_session_path ne '') {
            if (!-d $php_session_path) {
                return ('', "Error al cargar configuraci&oacute;n de objeto [$id]. El par&aacute;metro PHP_SESSION_PATH no es una ruta v&aacute;lida.", '');
            };
        } else {
            # utiliza el path de sesiones estandard de altavoz
            $php_session_path = $dir_server;
            $php_session_path =~ s/\/web$//;
            $php_session_path .= '/sesiones_php';
        };

        # MSG_MODER
        if ($obj_data =~ /\s*MSG_MODER\s*=\s*("|')(.*?)("|')/) {
            $msg_moder = $2;
        };

        # MSG_NOMODER
        if ($obj_data =~ /\s*MSG_NOMODER\s*=\s*("|')(.*?)("|')/) {
            $msg_nomoder = $2;
        };

        # NOM
        if ($obj_data =~ /\s*NOM\s*=\s*("|')(.*?)("|')/) {
            $nom = $2;
        };
        if ($nom eq '') {
            $nom = 'Artics';
            print STDERR "En conf de objeto [$id], no se especifica valor para la variable, se setea NOM = 'Artics' (valor por omision)\n"

            # return ('', "Error al cargar configuraci&oacute;n de objeto [$id]. El par&aacute;metro NOM se encuentra vac&iacute;o.", '');
        };
        $nom = &basic_escape_html($nom);

        # URL
        if ($obj_data =~ /\s*URL\s*=\s*("|')(.*?)("|')/) {
            $url = $2;
        };

        # si esta en blanco, pues la compone el coment_admin.cgi al listar.
#        if (!$url) {
#            $url = "/$instancia_prontus/cpan/core/coment/gadgets/ver_artic.html?art=<_file>"; # url al artic
#        };


        # PLT_VERCOMENT
        if ($obj_data =~ /\s*PLT_VERCOMENT\s*=\s*("|')(.*?)("|')/) {
            $plt = $2;
        };
        if ($plt) {
            if (!-f "$dir_server$plt") {
                return ('', "Error al cargar configuraci&oacute;n de objeto [$id]. El par&aacute;metro PLT_VERCOMENT no corresponde a un archivo v&aacute;lido.", '');
            };
        } else {
            $plt = "/$instancia_prontus/coment/plantillas/coment_articulo.html"; # usa el por defecto.
        };


        # DIR_PAGS_COMENT
        if ($obj_data =~ /\s*DIR_PAGS_COMENT\s*=\s*("|')(.*?)("|')/) {
            $dir_pags_coment = $2;
        };
        if ($dir_pags_coment) {
            if (! &glib_fildir_02::check_dir("$dir_server$dir_pags_coment")) {
                return ('', "Error al cargar configuraci&oacute;n de objeto [$id]. No es posible escribir en dir especificado por DIR_PAGS_COMENT.", '');
            };
        } else {
            $dir_pags_coment = "/$instancia_prontus/coment/site/articulo";
        };

        # FILASXPAG_PUBLIC
        $filasxpag_public = '10';
        if ($obj_data =~ /\s*FILASXPAG_PUBLIC\s*=\s*("|')([0-9]+)("|')/) {
            $filasxpag_public = $2;
        };

        # LIMIT_CHARS
        $limit = '1000';
        if ($obj_data =~ /\s*LIMIT_CHARS\s*=\s*("|')([0-9]+)("|')/) {
            $limit = $2;
        };

        # Captcha
        my $captcha = 'si';
        if ($obj_data =~ /\s*CAPTCHA\s*=\s*("|')(.*?)("|')/) {
            $captcha = $2;
        };
        
        # Moderacion
        my $MODERACION = 'SI';
        if ($obj_data =~ /\s*MODERACION\s*=\s*("|')(.*?)("|')/) {
            $MODERACION = $2;
        };


        # Extension de articulo prontus, se usa solamente si no viene URL
        my $artic_extension = 'html'; # default
        if ($obj_data =~ /\s*ARTIC_EXTENSION\s*=\s*("|')(.*?)("|')/) {
            $artic_extension = $2;
            $artic_extension =~ s/^\.//; # elimina punto inicial en caso q lo traiga
        };

        # ENVIAR_MAIL_PUBLICACION
        my $enviar_mail_publicacion = 'no';
        my $mail_publicacion_from = '';
        my $mail_publicacion_asunto = '';
        my $mail_publicacion_smtp = '';

        if ($obj_data =~ /\s*ENVIAR_MAIL_PUBLICACION\s*=\s*("|')(.*?)("|')/) {
            $enviar_mail_publicacion = $2;
        };
        if (lc $enviar_mail_publicacion eq 'si') {
            # MAIL_PUBLICACION_FROM
            if ($obj_data =~ /\s*MAIL_PUBLICACION_FROM\s*=\s*("|')(.*?)("|')/) {
                $mail_publicacion_from = $2;
            };
            if (!$mail_publicacion_from) {
                return ('', "Error al cargar configuraci&oacute;n de objeto [$id]. El par&aacute;metro MAIL_PUBLICACION_FROM se encuentra vac&iacute;o.", '');
            };

            # MAIL_PUBLICACION_ASUNTO
            if ($obj_data =~ /\s*MAIL_PUBLICACION_ASUNTO\s*=\s*("|')(.*?)("|')/) {
                $mail_publicacion_asunto = $2;
            };
            if (!$mail_publicacion_asunto) {
                return ('', "Error al cargar configuraci&oacute;n de objeto [$id]. El par&aacute;metro MAIL_PUBLICACION_ASUNTO se encuentra vac&iacute;o.", '');
            };
            # MAIL_PUBLICACION_SMTP
            if ($obj_data =~ /\s*MAIL_PUBLICACION_SMTP\s*=\s*("|')(.*?)("|')/) {
                $mail_publicacion_smtp = $2;
            };
            if (!$mail_publicacion_smtp) {
                return ('', "Error al cargar configuraci&oacute;n de objeto [$id]. El par&aacute;metro MAIL_PUBLICACION_SMTP se encuentra vac&iacute;o.", '');
            };

        };


        my $seleccionado = '';

        if ( $id eq $id_seleccionado ) {
            $seleccionado = 'selected';
        };
        $options .= "<option value=\"$id\" $seleccionado>$nom</option>\n";
        $hash_tipos{$id}{'NOM'} = $nom;
        $hash_tipos{$id}{'URL'} = $url;
        $hash_tipos{$id}{'PLT_VERCOMENT'} = $plt;
        $hash_tipos{$id}{'FILASXPAG_PUBLIC'} = $filasxpag_public;
        $hash_tipos{$id}{'LIMIT_CHARS'} = $limit;
        $hash_tipos{$id}{'DIR_PAGS_COMENT'} = $dir_pags_coment;
        $msg_nomoder =~ s/\|//g;
        $msg_moder =~ s/\|//g;
        $hash_tipos{$id}{'MSG_NOMODER'} = $msg_nomoder;
        $hash_tipos{$id}{'MSG_MODER'} = $msg_moder;

        $hash_tipos{$id}{'PHP_SESSION_NAME'} = $php_session_name;
        $hash_tipos{$id}{'PHP_SESSION_PATH'} = $php_session_path;
        $hash_tipos{$id}{'ID_STYLE'} = $id_style;
        $hash_tipos{$id}{'CAPTCHA'} = $captcha;
        $hash_tipos{$id}{'MODERACION'} = $MODERACION;
        $hash_tipos{$id}{'ENVIAR_MAIL_PUBLICACION'} = $enviar_mail_publicacion;
        $hash_tipos{$id}{'ARTIC_EXTENSION'} = $artic_extension;

        $hash_tipos{$id}{'MAIL_PUBLICACION_FROM'} = $mail_publicacion_from;
        $hash_tipos{$id}{'MAIL_PUBLICACION_ASUNTO'} = $mail_publicacion_asunto;
        $hash_tipos{$id}{'MAIL_PUBLICACION_SMTP'} = $mail_publicacion_smtp;

        # print STDERR "id[$id] ARTIC_EXTENSION[$hash_tipos{$id}{'ARTIC_EXTENSION'}]\n";
    };
    return ($options, '', \%hash_tipos);

};
# ---------------------------------------------------------------
sub basic_escape_html {
  my $toencode = $_[0];
  $toencode=~s/&([^#][^0-9]+)/&amp;\1/g;             # Antes que nada, traduce los ampersands. # 1.19 correccion a e.r.
  $toencode=~s/>/&gt;/g;              # >
  $toencode=~s/"/&quot;/g;            # " # 8.0
  $toencode=~s/'/&#39;/g;
  $toencode=~s/</&lt;/g;              # <
  $toencode=~s/\n/\n<br\/>/sg;
  return $toencode;
};
# ---------------------------------------------------------------
sub tildes2html {
    my($to_encode) = $_[0];

    $to_encode=~s/\x86/&Yacute;/g;
    $to_encode=~s/\x87/&brvbar;/g;
    $to_encode=~s/\x8B/&eth;/g;
    $to_encode=~s/\x95/&middot;/g;
    $to_encode=~s/\x96/&shy;/g;


    $to_encode=~s/\xA6/&#166;/g;
    $to_encode=~s/\xAF/&#175;/g;
    $to_encode=~s/\xB2/&#178;/g;
    $to_encode=~s/\xB3/&#179;/g;
    $to_encode=~s/\xB9/&#185;/g;
    $to_encode=~s/\xBC/&#188;/g;
    $to_encode=~s/\xBD/&#189;/g;
    $to_encode=~s/\xBE/&#190;/g;
    $to_encode=~s/\xD7/&#215;/g;

    $to_encode=~s/\xA1/&iexcl;/g;
    $to_encode=~s/\xA2/&cent;/g;
    $to_encode=~s/\xA3/&pound;/g;
    $to_encode=~s/\xA4/&curren;/g;
    $to_encode=~s/\xA5/&yen;/g;
    $to_encode=~s/\xA7/&sect;/g;
    $to_encode=~s/\xA8/&uml;/g;
    $to_encode=~s/\xA9/&copy;/g;
    $to_encode=~s/\xAA/&ordf;/g;
    $to_encode=~s/\xAC/&not;/g;
    $to_encode=~s/\xAD/&shy;/g;
    $to_encode=~s/\xAE/&reg;/g;
    $to_encode=~s/\xB0/&deg;/g;
    $to_encode=~s/\xB1/&plusmn;/g;
    $to_encode=~s/\xB4/&acute;/g;
    $to_encode=~s/\xB5/&micro;/g;
    $to_encode=~s/\xB6/&para;/g;
    $to_encode=~s/\xB7/&middot;/g;
    $to_encode=~s/\xB8/&cedil;/g;
    $to_encode=~s/\xBA/&ordm;/g;
    $to_encode=~s/\xBB/&raquo;/g;
    $to_encode=~s/\xBF/&iquest;/g;
    $to_encode=~s/\xC0/&Agrave;/g;
    $to_encode=~s/\xC1/&Aacute;/g;
    $to_encode=~s/\xC2/&Acirc;/g;
    $to_encode=~s/\xC3/&Atilde;/g;
    $to_encode=~s/\xC4/&Auml;/g;
    $to_encode=~s/\xC5/&Aring;/g;
    $to_encode=~s/\xC6/&AElig;/g;
    $to_encode=~s/\xC7/&Ccedil;/g;
    $to_encode=~s/\xC8/&Egrave;/g;
    $to_encode=~s/\xC9/&Eacute;/g;
    $to_encode=~s/\xCA/&Ecirc;/g;
    $to_encode=~s/\xCB/&Euml;/g;
    $to_encode=~s/\xCC/&Igrave;/g;
    $to_encode=~s/\xCD/&Iacute;/g;
    $to_encode=~s/\xCE/&Icirc;/g;
    $to_encode=~s/\xCF/&Iuml;/g;
    $to_encode=~s/\xD1/&Ntilde;/g;
    $to_encode=~s/\xD2/&Ograve;/g;
    $to_encode=~s/\xD3/&Oacute;/g;
    $to_encode=~s/\xD4/&Ocirc;/g;
    $to_encode=~s/\xD5/&Otilde;/g;
    $to_encode=~s/\xD6/&Ouml;/g;

    $to_encode=~s/\xD8/&Oslash;/g;
    $to_encode=~s/\xD9/&Ugrave;/g;
    $to_encode=~s/\xDA/&Uacute;/g;
    $to_encode=~s/\xDB/&Ucirc;/g;
    $to_encode=~s/\xDC/&Uuml;/g;
    $to_encode=~s/\xDD/&Yacute;/g;
    $to_encode=~s/\xDE/&THORN;/g;
    $to_encode=~s/\xDF/&szlig;/g;
    $to_encode=~s/\xE0/&agrave;/g;
    $to_encode=~s/\xE1/&aacute;/g;
    $to_encode=~s/\xE2/&acirc;/g;
    $to_encode=~s/\xE3/&atilde;/g;
    $to_encode=~s/\xE4/&auml;/g;
    $to_encode=~s/\xE5/&aring;/g;
    $to_encode=~s/\xE6/&aelig;/g;
    $to_encode=~s/\xE7/&ccedil;/g;
    $to_encode=~s/\xE8/&egrave;/g;
    $to_encode=~s/\xE9/&eacute;/g;
    $to_encode=~s/\xEA/&ecirc;/g;
    $to_encode=~s/\xEB/&euml;/g;
    $to_encode=~s/\xEC/&igrave;/g;
    $to_encode=~s/\xED/&iacute;/g;
    $to_encode=~s/\xEE/&icirc;/g;
    $to_encode=~s/\xEF/&iuml;/g;
    $to_encode=~s/\xF0/&eth;/g;
    $to_encode=~s/\xF1/&ntilde;/g;
    $to_encode=~s/\xF2/&ograve;/g;
    $to_encode=~s/\xF3/&oacute;/g;
    $to_encode=~s/\xF4/&ocirc;/g;
    $to_encode=~s/\xF5/&otilde;/g;
    $to_encode=~s/\xF6/&ouml;/g;
    $to_encode=~s/\xF7/&divide;/g;
    $to_encode=~s/\xF8/&oslash;/g;
    $to_encode=~s/\xF9/&ugrave;/g;
    $to_encode=~s/\xFA/&uacute;/g;
    $to_encode=~s/\xFB/&ucirc;/g;
    $to_encode=~s/\xFC/&uuml;/g;
    $to_encode=~s/\xFD/&brvbar;/g;
    $to_encode=~s/\xFE/&thorn;/g;
    $to_encode=~s/\xFF/&yuml;/g;


    $to_encode=~s/\x83/&#131;/g;

    $to_encode=~s/\x85/&#133;/g;

    $to_encode=~s/\x88/&#136;/g;
    $to_encode=~s/\x89/&#137;/g;
    $to_encode=~s/\x8A/&#138;/g;

    $to_encode=~s/\x8C/&#140;/g;

    $to_encode=~s/\x8E/&#142;/g;


    $to_encode=~s/\x91/&#145;/g;
    $to_encode=~s/\x92/&#146;/g;

    $to_encode=~s/\x97/&#151;/g;

    $to_encode=~s/\x99/&#153;/g;
    $to_encode=~s/\x9A/&#154;/g;

    $to_encode=~s/\x9C/&#156;/g;

    $to_encode=~s/\x9E/&#158;/g;
    $to_encode=~s/\x9F/&#159;/g;

    return $to_encode;
};

# ---------------------------------------------------------------
sub generar_comentarios {
  my ($bd, $dir_server, $objtipo, $objid, $prontus_id) = @_;
  # print STDERR "($bd, $dir_server, $objtipo, $objid, $prontus_id)\n";

  my ($options_tipo, $msg_err, $hash_tipos_ref) = &lib_coment::get_objtipos($dir_server, '', $prontus_id); # desde el cfg
  my %hash_tipos = %$hash_tipos_ref;

  # Precarga Plantilla
  # Plantilla completa --> %BUF_PLT
  # Loop --> %BUF_PLT_LOOP
  my $plt = $hash_tipos{$objtipo}{'PLT_VERCOMENT'};
  my $buf_plt = &glib_fildir_02::read_file("$dir_server$plt");
  $buf_plt =~ s/$CRLF/\n/sg;
  $buf_plt =~ s/%%_prontus_id%%/$prontus_id/ig;

  my $buf_plt_loop;
  my $ext_plt;
  if ($buf_plt =~ /<!--LOOP-->(.*?)<!--\/LOOP-->/isg) {
    $buf_plt_loop = $1;
  };
  $buf_plt_loop =~ s/%%_prontus_id%%/$prontus_id/ig;
  $ext_plt = $1 if ($plt =~ /\.(\w+)$/);


  # datos de comentarios
  my %hash_data;
  my $sql = "SELECT "
       . "COMENT_ID, "
       . "COMENT_DATETIME, "
       . "COMENT_TEXTO, "
       . "COMENT_NICK "
       . "from COMENT where COMENT_OBJID = \"$objid\" and COMENT_OBJTIPO = \"$objtipo\" and COMENT_STATUS = \"1\"  order by COMENT_ID DESC";

  # warn $sql;
  my $salida_c = &glib_dbi_02::ejecutar_sql_bind($bd, $sql, \(
           $hash_data{'COMENT_ID'},
           $hash_data{'COMENT_DATETIME'},
           $hash_data{'COMENT_TEXTO'},
           $hash_data{'COMENT_NICK'}
           ));




  my $tot_opin = &get_tot_opin_by_artic($bd, "SELECT COUNT(COMENT_ID) FROM COMENT WHERE COMENT_OBJID = \"$objid\" and COMENT_STATUS = \"1\"");
  my $nomdir_dst;
  if ($hash_tipos{$objtipo}{'ID_STYLE'} eq 'TIMESTAMP') {
    $nomdir_dst = substr($objid, 0, 8);
  } elsif ($hash_tipos{$objtipo}{'ID_STYLE'} eq 'NUMERIC') {
    $nomdir_dst = ($objid - ($objid % 1000)) / 1000; # division entera
  };
  my $reldir_dst = $hash_tipos{$objtipo}{'DIR_PAGS_COMENT'} . "/$nomdir_dst/$objid";
  my $dir_dst = "$dir_server$reldir_dst";
  &glib_fildir_02::check_dir($dir_dst);
  my $filasxpag = $hash_tipos{$objtipo}{'FILASXPAG_PUBLIC'};

  # tot_opin:0, reldir_dst://20081119191205, filasxpag:, ext_plt:
  print STDERR "tot_opin:$tot_opin, reldir_dst:$reldir_dst, filasxpag:$filasxpag, ext_plt:$ext_plt\n";
  my ($total_pages, $nrosdepag) = &get_nrosdepag($tot_opin, $reldir_dst, $filasxpag, $ext_plt);


  my $filas;
  my $nro_filas = 0;
  my $coment_pos = $tot_opin;
  my %paginas_escritas;
  my $nro_pag = 0;
  while ($salida_c->fetch) {

    $filas .= &generar_fila($coment_pos, $buf_plt_loop, \%hash_data);
    $coment_pos--;

    # escribir la pag actual y cambiar a la pagina siguiente
    $nro_filas++;
    if ($nro_filas >= $filasxpag) {
      $nro_pag++; # avanza pag
      my $path_pag = &write_pag($nro_pag, $filas, $nrosdepag, $dir_dst, $buf_plt, $ext_plt, $filasxpag, $tot_opin, $total_pages, $objid, $objtipo);
      $paginas_escritas{$path_pag} = 1 if ($path_pag);
      $nro_filas = 0; # resetea conta de filas para empezar del ppio en la pagina que viene.
      $filas = '';

    };
    # print STDERR "nro_filas:$nro_filas\n";
  };


  # escribir lo que haya quedado
  if ($nro_filas) {
    $nro_pag++; # avanza pag
    my $path_pag = &write_pag($nro_pag, $filas, $nrosdepag, $dir_dst, $buf_plt, $ext_plt, $filasxpag, $tot_opin, $total_pages, $objid, $objtipo);
    $paginas_escritas{$path_pag} = 1 if ($path_pag);
  };

  $salida_c->finish;

  # borra archivos que no correspondan
  # 1.1.3 - CVI - Se saca comprobación de si se escribieron las páginas o no
  my @files = glib_fildir_02::lee_dir($dir_dst);
  foreach my $file (@files) {
    next if ($file !~ /^\d+\.\w+$/);
    if (! $paginas_escritas{"$dir_dst/$file"}) {
      unlink "$dir_dst/$file";
    };
  };

  &glib_fildir_02::write_file("$dir_dst/total.txt", $tot_opin); # 1.1

};



# ---------------------------------------------------------------
sub write_pag {

  my ($nro_pag, $filas, $nrosdepag, $dir_dst, $buf_plt, $ext_plt, $filasxpag, $tot_opin, $total_pages, $objid, $objtipo) = @_;
  # print STDERR "nro_pag[$nro_pag] - nrosdepag[$nrosdepag]\n";
  # parsea pagina
  my $pagina = $buf_plt;
  $pagina =~ s/<!--LOOP-->(.*?)<!--\/LOOP-->/$filas/isg;
  my $pagina_usuario;
  if ($tot_opin > $filasxpag) {
    $nrosdepag =~ s/<a href="[^"]+?\/$nro_pag\.$ext_plt'\)">(\d+)<\/a>/\1/; # deslinkea pagina actual
    $pagina =~ s/%%_HTML_NROS_PAG%%/$nrosdepag/ig;
    $pagina =~ s/%%\/?_paginacion%%//isg;
  }
  else {
    $pagina =~ s/%%_HTML_NROS_PAG%%//ig;
    $pagina =~ s/%%_paginacion%%.*?%%\/_paginacion%%//isg;
  };

  $pagina =~ s/%%_filasxpag%%/$filasxpag/ig;
  $pagina =~ s/%%_nro_pag%%/$nro_pag/ig;
  $pagina =~ s/%%_tot_opin%%/$tot_opin/ig;
  $pagina =~ s/%%_tot_pags%%/$total_pages/ig;
  $pagina =~ s/%%_obj_id%%/$objid/ig;
  $pagina =~ s/%%_obj_tipo%%/$objtipo/ig;

  $pagina =~ s/<!--COMENTARIOS-->(.*?)<!--\/COMENTARIOS-->//isg if (!$filas);

  # Escribe pagina
  my $path_pag = "$dir_dst/$nro_pag.$ext_plt";
  &glib_fildir_02::write_file($path_pag, $pagina);
  &lib_prontus::purge_cache($path_pag);
  if (-s $path_pag) {
    # CVI - Esto no debería ir al STDERR ya que no es un error, salvo que se
    # manejara un error_log propio
    # print STDERR "write[$path_pag]\n";
    return $path_pag;
  }
  else {
    return 0;
  };


};

# ---------------------------------------------------------------
sub get_nrosdepag {
  # paginacion NORMAL
  my ($tot_opin, $reldir_dst, $filasxpag, $ext_plt) = @_;
  my ($tpl_nropag) = '<a href="javascript:recarga_coment(\'%%lnk%%\')">%%cnro_pag%%</a> ';
  my $html_nros_pag;
  my $pagN = int($tot_opin/$filasxpag);
  $pagN++ if (($tot_opin % $filasxpag) > 0);

  for(my $pag = 1; $pag <= $pagN; $pag++) {

      my $tpl_nropag_aux = $tpl_nropag;
      my $lnk = "$reldir_dst/$pag.$ext_plt";
      $tpl_nropag_aux =~ s/%%lnk%%/$lnk/;
      $tpl_nropag_aux =~ s/%%cnro_pag%%/$pag/;
      $html_nros_pag .= $tpl_nropag_aux;

  };
  return ($pagN, $html_nros_pag);
};

# ---------------------------------------------------------------
sub get_tot_opin_by_artic {
  my ($bd) = $_[0];
  my ($sql) = $_[1];

  my ($count_art);
  my $salida = &glib_dbi_02::ejecutar_sql_bind($bd, $sql, \($count_art));
  $salida->fetch;
  $salida->finish;
  $count_art = '0' if $count_art eq '';
  return $count_art;

};
# ---------------------------------------------------------------
sub generar_fila {
# Genera y retorna cada fila de la tabla.
  my $coment_pos = $_[0];
  my $loop = $_[1];
  my $aux = $_[2]; my %hash_data = %$aux;
  my ($fila);

  $fila = $loop;

  # custom
  if ($hash_data{'COMENT_ID'}) {
    # Armar la fila.
    $hash_data{'COMENT_DATETIME'} = &print_date_and_time($hash_data{'COMENT_DATETIME'});
    $fila =~ s/%%_COMENT_DATETIME%%/$hash_data{'COMENT_DATETIME'}/ig;

    $hash_data{'COMENT_TEXTO'} = &basic_escape_html($hash_data{'COMENT_TEXTO'});
    # $hash_data{'COMENT_TEXTO'} = &tildes2html($hash_data{'COMENT_TEXTO'});
    # $hash_data{'COMENT_NICK'} = &tildes2html($hash_data{'COMENT_NICK'});

    $fila =~ s/%%_COMENT_TEXTO%%/$hash_data{'COMENT_TEXTO'}/ig;
    $fila =~ s/%%_COMENT_NICK%%/$hash_data{'COMENT_NICK'}/ig;
    $fila =~ s/%%_COMENT_ID%%/$hash_data{'COMENT_ID'}/ig;
    $fila =~ s/%%_COMENT_POS%%/$coment_pos/ig;

  }else {
    # Armar la fila sin datos.
    $fila =~ s/%%\w+?%%/&nbsp;/ig;
  };
  return $fila;
};
# ---------------------------------------------------------------
sub print_date_or_time {
  # Escribe la fecha u hora, dependiendo si la fecha del art. es de hoy o no.
  my ($ts) = $_[0];
  my $isofec = &glib_hrfec_02::get_date_pack4();
  return $ts if ($ts !~ /^\d{14}$/);
  $ts =~ /^(\d{8})(\d{6})$/;
  my $aaaammdd = $1;
  my $hhmmss = $2;
  if ($aaaammdd eq $isofec) { # es de hoy
    # Escribe hora (puede venir formateada o no.)

    if ($hhmmss =~ /^(\d\d)(\d\d)(\d\d)$/) {
      return $1 . ':' . $2 . ':' . $3;
    }
    else {
      return '';
    };

  }
  else {
    # Escribe fecha

    if ($aaaammdd =~ /^(\d\d\d\d)(\d\d)(\d\d)$/) {
      return $3 . '/' . $2 . '/' . $1;
    }
    else {
      return '';
    };

  };
};
# ---------------------------------------------------------------
sub print_date_and_time {
  # Escribe la fecha y hora siempre.
  my ($ts) = $_[0];
  my $isofec = &glib_hrfec_02::get_date_pack4();
  return $ts if ($ts !~ /^\d{14}$/);
  $ts =~ /^(\d{8})(\d{6})$/;
  my $aaaammdd = $1;
  my $hhmmss = $2;

  if ($hhmmss =~ /^(\d\d)(\d\d)(\d\d)$/) {
    $hhmmss = $1 . ':' . $2 . ':' . $3;
  }
  else {
    $hhmmss = '00:00:00';
  };

  # Escribe fecha

  if ($aaaammdd =~ /^(\d\d\d\d)(\d\d)(\d\d)$/) {
    $aaaammdd = $3 . '/' . $2 . '/' . $1;
  }
  else {
    $aaaammdd = 'sin fecha';
  };

	return "$aaaammdd - $hhmmss"

};


return 1;

# -------------------------------END LIBRERIA--------------------
