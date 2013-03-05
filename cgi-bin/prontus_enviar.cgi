#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# ##########################################
# Proposito.
#
# Envia por mail una pagina pasada como URL,
# insertando un mensaje en un lugar determinado
# de ella (tag %%msg%%).
#
# Para esto, toma los contenidos Prontus:
# Titular  - <!--TITULAR-->...<!--/TITULAR--> --> %%TITULAR%%
# Fecha    - <!--FECHAP=...-->                --> <!--FECHAP=%%FECHAP%%-->
#
# Basado en snd_page_01.pl
#
# ##########################################
# Funcionamiento.
#
# Primero se invoca desde un boton ubicado en la pagina que se
# desea transmitir (metodo GET, parametro ACCI=Showform).
#
# La pagina que muestra va en ventana pop-up y contiene un
# formulario donde se ingresa el mail de destino y un comentario.
#
# Al oprimir el boton "Enviar" de esa pagina, se obtiene,
# parsea y envia la pagina web (URL) al mail de destino.
#
# Luego de esto se muestra una pagina de agradecimiento.
#
# ##########################################
# Llamadas a Archivos Externos.
#
# Plantillas:
#   formulario.html          - Formulario para enviar la pagina.
#   <nom_plantilla_art>.html - Plantilla de la pagina a enviar por correo electronico.
#   enviar.html              - Plantilla de la pagina a enviar por correo electronico.
#   gracias.html             - Pagina de agradecimiento.
#
# ##########################################
# Invocaciones Aceptadas.
#
# Para mostrar formulario de envio:
#   ACCI = Showform
#   PRONTUS_DIR = /<prontus_dir>
#
# Ejemplo:
# <a href="javascript:window.open('/cgi-bin/enviar.cgi?ACCI=Showform','Enviar a...','toolbar=0,status=0,menubar=0,scrollbars=0,resizable=0,location=0,directories=0,width=480,height=410')" target="_blank">Enviar esta p&aacute;gina a...</a>
#
# Para enviar pagina:
#   ACCI = Enviar
#   TO   = <direccion de e-mail de destino>
#   FROM = <direccion de e-mail de origen>
#   SUB  = <subject>
#   COME = <comentario>
#   URL  = <url de la pagina> <- se parsea dentro del texto enviar.html
#   PRONTUS_DIR = Relativo a DOCUMENT_ROOT
#
# ##########################################
# Plantillas HTML utilizadas.
#
# Las plantillas deben ubicarse dentro del directorio <prontus_dir>/plantillas/extra/enviar/pags/.
#
# formulario.html Template del formulario
#   Marcas:
#     %%HIDDEN%% Para insertar el URL de la pagina a enviar
#                y el directorio de los templates como campos
#                hidden.
#
# gracias.html Template del formulario
#   Marcas:
#     %%MSG%% Mensaje de exito o error
#
# 4send.html  - Plantilla para enviar la pagina.
#   Marcas:
#     %%COME%%  Para insertar el comentario.
#     %%CONT%% Para insertar el contenido de la pagina original.
#     También parsea cualquier otra variable del formulario.
#
# ##########################################
# Falta:
#
# ##########################################
# Historia de versiones.
# 2.0 - 11/11/2002 - ALD - Primera version.
# 2.1 - 11/01/2003 - ALD - Adaptacion a La Nacion.
# 2.2 - 10/04/2003 - MCO - Se agrega la capacidad de mostrar fotos (puestas por prontus) que esten
#                          en el articulo. Estas deben tener las mismas marcas del prontus.
#                          Rescata SMTP (envio e-mail) y servidores permitidos para la ejecucion del
#                          script, desde el archivo de configuración prontus.
#                          Se agrega epigrafe.
# 2.3 - 17/04/2003 - MCO - Se agrega la capacidad de mostrar TEXTtitrecuadro y TEXTrecuadro.
# 2.4 - 14/05/2003 - MCO - Se estandariza el parseo de marcas, sin necesidad de identificar cada una.
#                          Se agrega el uso de plantillas (ubicadas en el mismo directorio imprimir)
#                          con el mismo nombre de la plantilla del articulo, para usar distintos
#                          formatos al imprimir, de acuerdo al articulo. Si no existe esta, se usa
#                          imprimir.html.
# 2.5 - 09/09/2003 - MCO - Se estandariza para ser usado tanto windows como en unix.
# 2.6 - 19/11/2004 - MCO - Calibrado para el prontus 10 (con xml).
# 2.7 - 09/2005 - YCH - Agrega subject por default.
#                     - reestructuracion general del codigo
#                     - TDIR ya no es un parametro sino q va fijo en $PRONTUS_DIR/plantillas/extra/enviar/pags
#                     - Agrega param _FILE en vez de URL
#                     - Elimina modo Showform
#                     - Elimina check del referer
#                     - Ahora todos los param. reservados comienzan con '_'
#                     - Soporta articulos de cualquier extension, no solo html
#                     - Elimina parseo de BASEHREF Y HTTP_HOST, Agrega _SERVER_NAME
#                     - Correccion de parseos Prontus
#                     - Subject por defecto
# 2.8 - 18/10/2007 - YCH - Determina DIR_SERVER usando funcion Prontus
# 2.9 - 06/11/2007 - YCH - varios seguridad, ademas redirige STDERR
# 2.10 - 24/07/2008 - ALD - Parsea datos para marca "Lo Mas" en pagina de respuesta.
# 2.11 - 23/04/2009 - CVI - Se parsea la marca FILEF
#
# ##############################################
# Paquetes utilizados.
BEGIN {

  # dir_cgi.pm trae algo como:
  # $DIR_CGI_CPAN = 'cgi-cpn';
  # $DIR_CGI_PUBLIC = 'cgi-bin';
  require 'dir_cgi.pm';
  my ($ROOTDIR) = $ENV{'DOCUMENT_ROOT'};  # desde el web
  $ROOTDIR .= '/' . $DIR_CGI_CPAN;
  unshift(@INC,$ROOTDIR); # Para dejar disponibles las librerias

};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);


use POSIX; # paquete que viene con Perl (manejo de fechas)

use strict;
no strict "refs";

use prontus_varglb; &prontus_varglb::init(); # 2.8
use lib_prontus;
use lib_mail;
use lib_captcha;
use lib_captcha2;
use Artic;
use glib_str_02;
use lib_maxrunning;

# Soporta un maximo de n copias corriendo.
if (&lib_maxrunning::maxExcedido(5)) {
    print "Content-type: text/html\n";
    print "\n<html><body><p>Error: Servidor ocupado. Intente otra vez m&aacute;s tarde.</p></body></html>.\n";
    exit;
};


# ##############################################
# Inicializaciones varias.


# Variables globales.
my (%FORM, $TDIR);
my ($CRLF) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
my ($ROOTDIR) = $prontus_varglb::DIR_SERVER; # 2.8
my $FILEURL;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

main: {

    # Parametros minimos: _ACCI _URL _TO _COME _SUB (optativo, asume valor por default)
    %FORM = &getFormData();
    $FORM{'_URL'} =~ s/%3f/\?/ig; # corrije escapeo http
    $FORM{'_URL'} =~ s/%3a/:/ig; # corrije escapeo http
    $FORM{'_URL'} =~ s/%23/#/ig; # corrije escapeo http
    $FORM{'_URL'} =~ s/\#.*$//; # Elimina posible gato final.
    $FORM{'_URL'} =~ s/\?.+$//ig;

    # 2.9
    &aborta('Solicitud no v&aacute;lida') if ($FORM{'_URL'} =~ /[<>]/is);

    $FORM{'_TO'} =~ s/\s+//sig;
    $FORM{'_FROM'} =~ s/\s+//sig;
    # warn($FORM{'_SUB'});
    if (! $FORM{'_SUB'}) {
        $FORM{'_SUB'} = "Artículo de $ENV{'SERVER_NAME'}";
    } else {
        utf8::decode($FORM{'_SUB'});
        $FORM{'_SUB'} =~ s/\#$//; # Elimina posible gato final.
    };

    # 2.9
    $FORM{'_SUB'} = &lib_prontus::escape_html($FORM{'_SUB'});

    $FORM{'_FILE'} = $FORM{'_URL'}; # onda /prontus_dir/site/artic/20050823/pags/20050823163215.html
    #$FORM{'_FILE'} =~ s/https?:\/\/$ENV{'SERVER_NAME'}//i;
    #$FORM{'_FILE'} =~ s/https?:\/\/$ENV{'HTTP_HOST'}//i;
    $FORM{'_FILE'} =~ s/https?:\/\/[^\/]+//i; # CVI

    &aborta('Solicitud de ejecuci&oacute;n no v&aacute;lida.') if ($FORM{'_ACCI'} ne 'Enviar');
    # 2.9
    print STDERR "file[$ROOTDIR$FORM{'_FILE'}]\n";
    &aborta('Art&iacute;culo no v&aacute;lido') if ((! -f "$ROOTDIR$FORM{'_FILE'}") || (! -s "$ROOTDIR$FORM{'_FILE'}"));

    # Obtiene prontus dir.
    my $prontus_id;
    my $ts;
    if ($FORM{'_FILE'} =~ /^\/(\w+)\/site\/artic\/\d{8}\/pags(-\w+)?\/(\d{14})\.\w+$/i) {   # 2.2.
        $prontus_id = $1;
        $ts = $3;
    } else {
        &aborta('No se pudo localizar directorio Prontus');
    };

    # Dir de Plantillas usadas por la aplicacion.
    $TDIR = "$ROOTDIR/$prontus_id/plantillas/extra/enviar/pags";

    if ($FORM{'_MV'}) { # nombre de la vista.
        $TDIR = $TDIR . '-' . $FORM{'_MV'};
    };

    &aborta('Dir de plantillas no v&aacute;lido.') if (! -d $TDIR);

    # Usando la nueva lib_captcha se manejan ambos formatos
    my $captcha_input = $FORM{'_CAPTCHA'};
    my $captcha_type = 'enviar'; # custom
    my $captcha_img = $FORM{'_captcha_img'};
    my $captcha_code = $FORM{'_captcha_code'};
    $captcha_input = $FORM{'_captcha_text'} unless($captcha_input);
    #~ require 'dir_cgi.pm';
    &lib_captcha2::init($prontus_varglb::DIR_SERVER, $prontus_varglb::DIR_CGI_CPAN);
    my $msg_err_captcha = &lib_captcha2::valida_captcha($captcha_input, $captcha_code, $captcha_type, $captcha_img);
    if ($msg_err_captcha ne '') {
        print "Content-Type: text/html\n\n";
        &show_msg($msg_err_captcha . '<br/>Por favor, vuelva '
                . '<a href="javascript:history.back()">atr&aacute;s</a> y corrija el error.', $FORM{'_URL'});
        exit;
    };

    # Smtp extraido del cfg del prontus
    my $smtp = &rescata_smtp_servers_del_cfg($prontus_id);
    &aborta('SMTP no especificado') if (! $smtp);

    # Path de cfg de prontus
    my $path_conf = "/$prontus_id/cpan/$prontus_id.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);

    # Carga variables de configuracion de prontus.
    &lib_prontus::load_config($path_conf);
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;


    print "Content-Type: text/html\n\n";

    # Validaciones para el usuario, usando plantilla para el html del error
    &valida_casillas();

    # Lee xml del artic.
    my $xml_data = &get_xml_data();

    # Carga plantilla para envio del correo
    my $buffer_enviar = &get_plt_enviar($xml_data);
    if ($buffer_enviar eq '') {
        &show_msg('Error de configuraci&oacute;n: No hay plantilla para enviar correo', $FORM{'_URL'});
        exit;
    };

    # Parsea datos
    my $titular;
    ($buffer_enviar, $titular) = &parse_prontus($buffer_enviar, $prontus_id, $ts);
    $buffer_enviar = &parse_noprontus($buffer_enviar);

    # Envia el correo electronico.



    my $to_con_nombre = $FORM{'_TO'};
    if ($FORM{'_TO_NOMBRE'} ne '') {
        utf8::decode($FORM{'_TO_NOMBRE'});
        $to_con_nombre =  &glib_str_02::solo_texto($FORM{'_TO_NOMBRE'}) . ' <' . $FORM{'_TO'} . '>';
    };

    my $from_con_nombre = $FORM{'_FROM'};
    if ($FORM{'_FROM_NOMBRE'} ne '') {
        utf8::decode($FORM{'_FROM_NOMBRE'});
        $from_con_nombre =  &glib_str_02::solo_texto($FORM{'_FROM_NOMBRE'}) . ' <' . $FORM{'_FROM'} . '>';
    };

    # $smtp = 'mail.altavoz.net'; # debug
    my $envio_ok = &lib_mail::mail_text($from_con_nombre,$to_con_nombre,$from_con_nombre,$FORM{'_SUB'},$buffer_enviar,1,$smtp);
    if ($envio_ok) {
        # Entrega pagina de exito.
        &show_msg("La p&aacute;gina fue enviada exitosamente.", $FORM{'_URL'}, $titular);
    } else {
        &show_msg("No fue posible enviar el mensaje.", $FORM{'_URL'}, $titular);
    };

};


# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub parse_prontus {
# Realiza parseos prontus a la pagina a enviar.

  my ($buffer_enviar, $prontus_id, $ts) = @_;


  # Parsea datos del artic
  my $artic_obj = Artic->new(
                'prontus_id'=>$prontus_id,
                'public_server_name'=>$prontus_varglb::IP_SERVER,
                'cpan_server_name'=>$prontus_varglb::IP_SERVER,
                'document_root'=>$prontus_varglb::DIR_SERVER,
                'ts'=>$ts,
                'campos'=>{}) || die "Error inicializando objeto articulo: $Artic::ERR\n";
  my %campos_xml = $artic_obj->get_xml_content();

  # Recupera marcas externas (desde /xdata)
  my %claves_adicionales = $artic_obj->get_xdata($buffer_enviar);

  $buffer_enviar = &lib_prontus::procesa_condicional($buffer_enviar, \%campos_xml, \%claves_adicionales);

  my $fullpath_vista = $artic_obj->get_fullpath_artic('', $campos_xml{'_plt'});
  $buffer_enviar = $artic_obj->parse_artic_data($fullpath_vista, $buffer_enviar, \%campos_xml, \%claves_adicionales); # ojo que esta NO rutina elimina las marcas sin sustituir

  # CVI - se agrega parseo para Friendly, que se puede usar en Lo Mas
  # JOR - 23/07/2012 - Agrega seccion, tema y subtema a la funcion parse_filef para versión 2.0 de friendly.
  $FILEURL = &lib_prontus::parse_filef('%%_fileurl%%', $campos_xml{'_txt_titular'}, $ts, $prontus_id, $FORM{'_FILE'}, $campos_xml{'_nom_seccion1'}, $campos_xml{'_nom_tema1'}, $campos_xml{'_nom_subtema1'});

  return ($buffer_enviar, $campos_xml{'_txt_titular'});

};
# ---------------------------------------------------------------
sub parse_noprontus {
# Realiza otros parseos al email a enviar (parseos no prontus)
  my $buffer = $_[0];

  $buffer =~ s/%%_SERVER_NAME%%/$ENV{'SERVER_NAME'}/sig;

  # Introduce retornos de carro para no marear a los clientes de correo.
  $buffer =~ s/<br>/<br>\r\n/isg;
  $buffer =~ s/<p/\r\n<p/isg;

  # Parsea tambien los datos submitidos.
  my ($valor, $key);
  foreach $key (keys %FORM) {
    $valor = $FORM{$key};
    $valor = &lib_prontus::escape_html($valor); # 2.9
    $buffer =~ s/%%$key%%/$valor/isg;
  };

  # Elimina cualquier marca no sustituida
  $buffer =~ s/%%.*?%%//sig;

  $buffer =~ s/<a href="#.*?">.*?<\/a>//sig; # Elimina los anchors.

  return $buffer;
};
# ---------------------------------------------------------------
sub get_plt_enviar {
# Obtiene contenido de la plantilla a usar para enviar el correo.

  my $xml_data = $_[0];

  # Obtiene el nombre de la plantilla del articulo.
  $xml_data =~ /<_plt>(.*?)<\/_plt>/si;
  my $plantilla_art = $1;

  # Lee el template de la pagina a enviar por correo.
  my $buffer_plt = &leeAllFile("$TDIR/$plantilla_art", '') if -s "$TDIR/$plantilla_art";
  $buffer_plt = &leeAllFile("$TDIR/enviar.html", '') if $buffer_plt eq '';

  $buffer_plt =~ s/$CRLF/\x0a/sg;
  return $buffer_plt;
};
# ---------------------------------------------------------------
sub valida_casillas {
# Realiza validaciones.
  if ($FORM{'_TO'} !~ /^[A-Za-z0-9\.\-\_]+@[A-Za-z0-9\.\-\_]+\.[A-Za-z]{2,3}$/) {
    &show_msg('La direcci&oacute;n de correo electr&oacute;nico de destino que Ud. '
          . 'ha ingresado no es v&aacute;lida. Por favor, vuelva '
          . '<a href="javascript:history.back()">atr&aacute;s</a> y corrija el error.', $FORM{'_URL'});
    exit;
  };
  if ($FORM{'_FROM'} !~ /^[A-Za-z0-9\.\-\_]+@[A-Za-z0-9\.\-\_]+\.[A-Za-z]{2,3}$/) {
    &show_msg('La direcci&oacute;n de correo electr&oacute;nico del remitente que Ud. '
          . 'ha ingresado no es v&aacute;lida. Por favor, vuelva '
          . '<a href="javascript:history.back()">atr&aacute;s</a> y corrija el error.', $FORM{'_URL'});
    exit;
  };
};
# ---------------------------------------------------------------
sub get_xml_data {
# Obtiene xml del articulo a partir de la ruta del html

  my $url = $FORM{'_FILE'};
  $url =~ s/(\/\d{8})\/pags(-\w+)?\//\1\/xml\//;
  $url =~ s/\.\w+$/\.xml/;
  $url =~ /(\d{14}\.xml)/;
  my $cont = &leeAllFile("$ROOTDIR$url", '');

  # Elimina marcas externas.
  $cont =~ s/.*?<_private>(.*?)<\/_private>.*?<_public>(.*?)<\/_public>.*?/$1\r\n$2/is;

  if ($cont eq '') {
    &show_msg('El servicio no est&aacute; disponible en este momento. [noxmldata] '
          . 'Intente nuevamente m&aacute;s tarde.', $FORM{'_URL'});
    exit;
  };

  return $cont;

};

# ---------------------------------------------------------------
sub leeAllFile {
# Lee un archivo completo.
  my($archivo, $url) = ($_[0], $_[1]);
  my($buffer);

  if (-f $archivo) {
    open (ARCHIVO,"<$archivo")
      || die "Fail Open file $archivo \n $!\n";
    read ARCHIVO,$buffer,-s $archivo;
    close ARCHIVO;
  }else{
    # $buffer = &getHTML($url) if $url ne '';
    return '';
  };

  return $buffer;

}; # leeAllFile

# ---------------------------------------------------------------
# Rescata las variables del chorro

sub getFormData {
  my($pair,$buffer);

  if ($ENV{'REQUEST_METHOD'} eq 'GET') {
    $buffer = $ENV{'QUERY_STRING'};
  }else{
    read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
  };

  my(@pairs) = split(/&/, $buffer);
  my %form;
  foreach $pair (@pairs) {
    my($name, $value) = split(/=/, $pair);

    # Un-Webify plus signs and %-encoding
    $value =~ tr/+/ /;
    $value =~ s/%00//sg; # 2.9
    $value =~ s/%([0-9A-Ha-h]{2})/pack("c",hex($1))/ge;

    # Stop people from using subshells to execute commands
    # Not a big deal when using sendmail, but very important
    # when using UCB mail (aka mailx).
    $value =~ s/~!/ ~!/g;

    $form{$name} = $value;
  };
  return %form;
}; # getFormData

# ---------------------------------------------------------------
# Muestra la pagina de mensaje con el mensaje.

sub show_msg {
  my($msg, $url, $tit) = @_;
  my($buffer) = &leeAllFile("$TDIR/gracias.html", '');
  # 2.10 Parsea marcas para "Lo Mas".
  $buffer =~ s/%%_TITULAR%%/$tit/ig;
  $buffer =~ s/%%_URL%%/$url/ig;
  # CVI se agrega parseo para Friendly, que se puede usar en Lo Mas
  $buffer =~ s/%%_FILEURL%%/$FILEURL/ig;

  if ($buffer =~ s/%%_MSG%%/$msg/ig) {
    print $buffer;
  }else{
    print "<html><body><p>$msg</body></html>";
  };
}; # show_msg

# ---------------------------------------------------------------
# Muestra una pagina de error fatal.

sub aborta {
  my($msg) = $_[0];
  print "Content-Type: text/html\n\n";
  print "<html><body><p>$msg</body></html>";
  exit;
}; # aborta


# ---------------------------------------------------------------
 # Toma una fecha en formato ISO y la escribe como "Lunes 10 de Mayo de 2000"
 # Param : string con la fecha ISO.
 # Retorna : string con la fecha convertida.

 sub expande_fecha {
   my($fecha) = $_[0];
   my(@dias) = ('Domingo','Lunes','Martes','Mi&eacute;rcoles','Jueves','Viernes','S&aacute;bado');
   my(@meses) = ('Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio',
                    'Agosto','Septiembre','Octubre','Noviembre','Diciembre');
   $fecha =~ /(\d\d\d\d)(\d\d)(\d\d)/g;
   my($dia,$mes,$ano) = ($3,$2,$1);
   my($tiempo) = &POSIX::mktime(0,0,12,$dia,($mes - 1),($ano - 1900));
   my($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($tiempo);
   $dia = $dia + 0; # Para extraer los ceros de adelante.
   return $dias[$wday] . " $dia de " . $meses[($mes - 1)] . " de $ano";

 }; # expande_fecha

# ---------------------------------------------------------------
sub rescata_smtp_servers_del_cfg { # 2.2.
  my $prontus_id = $_[0];

  my ($buffer) = &leeAllFile("$ROOTDIR/$prontus_id/cpan/$prontus_id" . '-var.cfg', '');
  my ($smtp);
  if ($buffer ne '') {
    $buffer =~ /SERVER_SMTP.*?=.*?\'(.*?)\'/si; # Obtiene IP o URL del servidor de e-mails.
    $smtp = $1;
  };
  return $smtp;
}; # rescata_smtp_servers_del_cfg.

# ---------------------------------------------------------------
sub parser_fechap {
# Parsea fechaplong y fechapshrt en base a fechap en el articulo.
  my ($buffer, $val_campo) = @_;
  # %%FECHAPLONG%% = Fecha de publicación, en formato largo
  # %%FECHAPSHRT%% = Fecha de publicación, en formato corto
  # %%FECHAP%%     = Fecha de publicación, en formato ISO --> Calza con el 2o. tipo de sustitucion estandar por tanto no se hace nada especial.

  if ($val_campo) {
    $buffer =~ s/%%_FECHAP%%/$val_campo/isg;
    my $fechaplong = &expande_fecha($val_campo);
    $buffer =~ s/%%_FECHAPLONG%%/$fechaplong/isg;

    my $fechapshrt = &des_normaliza_fecha($val_campo);
    $buffer =~ s/%%_FECHAPSHRT%%/$fechapshrt/isg;
  }
  else {
    $buffer =~ s/%%_FECHAPSHRT%%//isg;
    $buffer =~ s/%%_FECHAPLONG%%//isg;
  };

  return $buffer;
}; # parser_fechap.


# -------------------------------------------------------------------------#
sub procesa_condicional {

  my($sentencia) = $_[0];
  my($buffer) = $_[1];
  my($vars_common) = $_[2];
  my($inicio,$fin,$otro,$aux1,$aux2,$elif,$cont, $marca_ini, $marca_fin, $cont1, $cont2);

  # Almacena las claves.
  my (%claves);
  while ($buffer =~ /%%$sentencia\((\w+?)\)%%/ig) {
    my $clave = $1;

    if ($$vars_common{$clave} ne '')  {
      if ($$vars_common{$clave} =~ /<!\[CDATA\[(.*?)\]\]>/isg) {
        my $cdata_content = $1;
        $claves{$clave} = 'yes' if ($cdata_content);
      }
      else {
        $claves{$clave} = 'yes';
      };
    };

  };


  # print STDERR "----------------- $sentencia ---------------";
  $cont1 = 0;
  do {
    $cont1++;
    if ($cont1 >= 1000) {
      return $buffer;
    };
    # Busca el primer <!--IF( y el primer <!--/IF--> desde el principio del string.
    $marca_ini = '%%' . $sentencia . '(';
    $inicio = index $buffer, $marca_ini;
    $marca_fin = '%%/' . $sentencia . '%%';
    $fin = index $buffer, $marca_fin;
    # Si encontró ambos, prosigue.
    if (($inicio >= 0) && ($fin >= 0) && ($fin > $inicio)) {
      # Busca otro comienzo de IF que este despues del recien
      # encontrado, pero antes del fin de IF.
      $cont2 = 0;
      do {
        $cont2++;
        if ($cont2 >= 1000) {
          return $buffer;
        };

        $otro = index $buffer, $marca_ini, $inicio + 1;
        # Cada vez que encuentra uno, lo toma como el verdadero comienzo del IF.
        if (($otro > $inicio) && ($otro < $fin)) { $inicio = $otro; };
      } until (($otro < 0) || ($otro > $fin));
      # Ahora tenemos un IF sin ningun otro IF adentro.
      # Rescata el IF, lo que hay antes y lo que hay despues.

      $elif = substr $buffer, $inicio, ($fin - $inicio + length $marca_fin);
      $aux1 = substr $buffer, 0, $inicio;

      $aux2 = substr $buffer, $fin + length $marca_fin;
      # print STDERR "$inicio $fin $elif\n"; # debug
      # Rescata la variable por la que se ha preguntado.
      my $var;
      if ($elif =~ /%%$sentencia\((\w+?)\)%%(.+?)%%\/$sentencia%%/s) {
        $var = $1;  # Variable de control.
        $cont = $2; # Contenido del IF

        if ($sentencia eq 'IF') {
          if ($claves{$var} ne 'yes') {
            # Borra el IF, o sea, concatena el antes con el despues.
            $buffer = $aux1 . $aux2;
          }else{
            # Deja el contenido, sin poner las marcas.
            $buffer = $aux1 . $cont . $aux2;
          };
        };

        if ($sentencia eq 'NIF') {
          # print STDERR "NIF con var[$var] y value[$claves{$var}]\n";
          if ($claves{$var} eq 'yes') {
            # Borra el NIF, o sea, concatena el antes con el despues.
            $buffer = $aux1 . $aux2;
          }else{
            # Deja el contenido, sin poner las marcas.
            $buffer = $aux1 . $cont . $aux2;
          };
        };

      };
    };
    # Repite todo esto hasta que no encuentra ningun otro IF.
  } until (($inicio < 0) || ($fin < 0) || ($fin < $inicio));
  # print STDERR "buffer = \n$buffer\n"; # debug
  return $buffer;
};

# ---------------------------------------------------------------
sub des_normaliza_fecha {
# Toma una fecha en formato ISO y la escribe como dia/mes/ano.

# Param : string con la fecha a des-normalizar.

# Retorna : "$dia/$mes/$ano"

  my($fecha) = $_[0];
  $fecha =~ /(\d\d\d\d)(\d\d)(\d\d)/g;
  my($dia,$mes,$ano) = ($3,$2,$1);

  return "$dia/$mes/$ano";
}; # des_normaliza_fecha.
