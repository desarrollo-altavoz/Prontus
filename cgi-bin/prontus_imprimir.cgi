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
# Genera una pagina susceptible de ser impresa, en base a un template
# predefinido. Para esto, toma los contenidos Prontus:
# Titular  - <!--TITULAR-->...<!--/TITULAR--> --> %%TITULAR%%
# Fecha    - <!--FECHAP=...-->                --> <!--FECHAP=%%FECHAP%%-->
# Pagina   - pagina
# ESTE IMPRIMIR ES SOLO PARA LOS DIARIOS REGIONALES, YA QUE ELIMINA TODAS LAS IMAGENES DEL ARTICULO.
#
# ##########################################
# Funcionamiento.
#
# Se invoca desde un link ubicado en la pagina que se
# desea imprimir (metodo GET, parametro URL=<el url>).
#
# Basado en print_page_01.cgi (www.primeralinea.cl)
#
#
# ##########################################
# Llamadas a Archivos Externos.
#
# Plantillas:
#   <nom_plantilla_art>.html - Plantilla para mostrar la pagina.
#   imprimir.html - Plantilla para mostrar la pagina.
#
# ##########################################
# Invocaciones Aceptadas.
#
# Para mostrar la pagina:
#   URL  = <el url>
#
#
# ##########################################
# Plantillas HTML utilizadas.
#
# La plantillas debe ubicarse dentro del directorio TDIR.

# Los links y las imagenes del contenido.
#     %%HTTP_HOST%% Para localizar la pagina en el servidor.
#
# ##########################################
# Historia de versiones.
# 2.0 - 11/01/2003 - ALD - Primera version.
# 2.1 - 16/01/2003 - ALD - Elimina fotos para que se imprima solo el texto.
#                        - Agrega capacidad para imprimir paginas no-estandar.
# 2.2 - 10/04/2003 - MCO - Se agrega la capacidad de mostrar fotos (puestas por prontus) que esten
#                          en el articulo. Estas deben tener las mismas marcas del prontus.
#                          Rescata servidores permitidos para la ejecucion del
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

# 2.7 - 09/2005 - YCH - Reestructuracion completa de la aplicacion.
# 2.8  18/10/2007 - YCH - Determina DIR_SERVER usando funcion Prontus
# 2.9 - 06/11/2007 - ych - varios seguridad
# 2.10 - 09/10/2009 - ych - Graba pagina y le hace location, al final hace garbage.
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
use glib_fildir_02;
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
my (%FORM, $RUTA_PRONTUS, $TDIR, $SMTP);
my ($CRLF) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
my ($ROOTDIR) = $prontus_varglb::DIR_SERVER; # 2.8

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

main: {


  # Parametros minimos: _URL
  %FORM = &getFormData();
  $FORM{'_URL'} =~ s/%3f/\?/ig; # corrije escapeo http
  $FORM{'_URL'} =~ s/%3a/:/ig; # corrije escapeo http
  $FORM{'_URL'} =~ s/%23/#/ig; # corrije escapeo http
  $FORM{'_URL'} =~ s/\#.*$//; # Elimina posible gato final.
  $FORM{'_URL'} =~ s/\?.+$//ig;

  # 2.9
  &aborta('Solicitud no válida') if ($FORM{'_URL'} =~ /[<>]/is);


  $FORM{'_FILE'} = $FORM{'_URL'};
  # $FORM{'_FILE'} =~ s/https?:\/\/$ENV{'SERVER_NAME'}//i;
  # $FORM{'_FILE'} =~ s/https?:\/\/$ENV{'HTTP_HOST'}//i;
  $FORM{'_FILE'} =~ s/https?:\/\/[^\/]+//i; # CVI

  # 2.9
  &aborta('Art&iacute;culo no v&aacute;lido') if ((! -f "$ROOTDIR$FORM{'_FILE'}") || (! -s "$ROOTDIR$FORM{'_FILE'}"));

  # Obtiene prontus dir.
  my $ruta = $FORM{'_FILE'};         # onda /prontus_dir/site/artic/20050823/pags/20050823163215.html
  $ruta =~ s/\/site\/artic\/\d{8}\/pags\/.*$//si;   # 2.2.
  $RUTA_PRONTUS = $ruta; # path del prontus, desde la raiz del web server, ie /prontus_noticias

  # Dir de Plantillas usadas por la aplicacion.
  $TDIR = "$ROOTDIR$RUTA_PRONTUS/plantillas/extra/imprimir/pags";
  if ($FORM{'_MV'}) { # nombre de la vista.
    $TDIR = $TDIR . '-' . $FORM{'_MV'};
  };
  &aborta('Dir de plantillas no v&aacute;lido.') if (! -d $TDIR);

  # Lee xml del artic.
  my $xml_data = &get_xml_data();

  # Carga plantilla generar pagina imprimiblr
  my $buffer_print = &get_plt_print($xml_data);

  # Parsea datos
  $buffer_print = &parse_prontus($buffer_print, $xml_data);
  $buffer_print = &parse_noprontus($buffer_print);

  # 2.10 Graba pagina y le hace location, al final hace garbage.
  my $cache_rel_dir = "$RUTA_PRONTUS/site/cache/imprimir/pags"; # Directorio de cache para el direccionamiento web.
  my $cache_dir = "$ROOTDIR$cache_rel_dir"; # Directorio de cache.
  &glib_fildir_02::check_dir($cache_dir);
  my $ext;
  if ($FORM{'_FILE'} =~ /\.([\w]+)$/) {
    $ext = $1;
  };
  my $answerid = 'imprimir' . time . $$;
  &glib_fildir_02::write_file("$cache_dir/$answerid\.$ext", $buffer_print);
  print "Location: $cache_rel_dir/$answerid\.$ext\n\n";
  &garbageCollection($cache_dir); # Limpia directorio de cache.


  # print $buffer_print;

};


# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
# 2.10 Elimina los archivos de mas de 10 minutos de antiguedad.
sub garbageCollection {
  my($eldir) = $_[0];
  my(@entries);
  # Abre directorio.
  if (opendir(DIR, $eldir)) {
    @entries = readdir(DIR);
    closedir DIR;
    foreach my $file (@entries) {
      # Por seguridad, solo limpia archivos con la firma de esta aplicacion.
      next if ($file !~ /imprimir/);
      # Detecta si son archivos.
      if (-f "$eldir/$file") {
        if ((stat("$eldir/$file"))[9] < (time - 600)) {
          unlink "$eldir/$file";
        };
      };
    };
  };
}; # garbageCollection
# ---------------------------------------------------------------
sub parse_prontus {
# Realiza parseos prontus a la pagina a imprimir.

  my ($buffer_tpl, $xml_data) = @_;
  my ($ruta_dir) = "$FORM{'_FILE'}"; $ruta_dir =~ s/\/\d{14}\.\w+$//;

  my (%data_campos, $nom_campo, $val_campo);
  while ($xml_data =~ /<(\w+?)>(.*?)<\/\1>/isg) {
    $nom_campo = $1;
    $val_campo = $2;
    $data_campos{$nom_campo} = $val_campo; # acumula para luego procesar las sentencias condicionales

    # Fotos
    if ($nom_campo =~ /^(FOTO_\w+)/i) {
      if ($val_campo =~ /<(_NOM$nom_campo)>(.+?)<\/\1>/i) {
        my $value = $2;
        my $path = $ruta_dir;
        $path =~ s/\/pags$/\/imag/is;
        $path = $path . '/' . $value;
        $buffer_tpl =~ s/%%$nom_campo%%/$path/isg;
      };
      if ($val_campo =~ /<(_A$nom_campo)>(.+?)<\/\1>/i) {
        my $value = $2;
        $buffer_tpl =~ s/%%_A$nom_campo%%/$value/isg;
      };
      if ($val_campo =~ /<(_W$nom_campo)>(.+?)<\/\1>/i) {
        my $value = $2;
        $buffer_tpl =~ s/%%_W$nom_campo%%/$value/isg;
      };
      if ($val_campo =~ /<(_H$nom_campo)>(.+?)<\/\1>/i) {
        my $value = $2;
        $buffer_tpl =~ s/%%_H$nom_campo%%/$value/isg;
      };
      if ($val_campo =~ /<(_TXT_P$nom_campo)>(.+?)<\/\1>/i) {
        my $value = $2;
        if ($value =~ /<!\[CDATA\[(.*?)\]\]>/) {
          $value = $1;
          $buffer_tpl =~ s/%%_TXT_P$nom_campo%%/$value/isg;
        };
      };
    }# if fotos
    elsif ($nom_campo =~ /^ASOCFILE_|^SWF_|^HTMLFILE_|^MULTIMEDIA_/i)  {
      my $dir_adjunto;
      $dir_adjunto = '/asocfile' if (($nom_campo =~ /^ASOCFILE_/i) or ($nom_campo =~ /^HTMLFILE_/i));
      $dir_adjunto = '/swf' if ($nom_campo =~ /^SWF_/i);
      $dir_adjunto = '/mmedia' if ($nom_campo =~ /^MULTIMEDIA_/i);
      my ($path) = $ruta_dir;
      $path =~ s/\/pags$/$dir_adjunto/is;
      $path = $path . '/' . $val_campo;
      $buffer_tpl =~ s/%%$nom_campo%%/$path/isg;
    }
    elsif ($nom_campo =~ /^_?TXT_\w+/i) {
      if ($val_campo =~ /<!\[CDATA\[(.*?)\]\]>/isg) {
        $val_campo = $1;
        $buffer_tpl = &lib_prontus::replace_in_artic($val_campo, $nom_campo, $buffer_tpl);
      };
    }
    elsif (uc $nom_campo eq '_FECHAP') {
      $buffer_tpl = &parser_fechap($buffer_tpl, $val_campo);
    }
    else {
      if ($val_campo =~ /<!\[CDATA\[(.*?)\]\]>/isg) {
        $val_campo = $1;
      };
      if ($nom_campo =~ /^vtxt_/) {
        # Elimina funcion q resetea tam. de imagenes en el vtxt.
        # $val_campo =~ s/cambiatam\(.*?\,.*?\,.*?\)//isg;
        $val_campo =~ s/ondblclick *= *".+?"//isg;
        $val_campo =~ s/<img (.*?)alt="FOTO_\w+(\&#13;)?\&#10;W:\d+(\&#13;)?\&#10;H:\d+"/<img \1 /isg;

        # Corrige issue ffox 3.6.11, elimina las rutas relativas, ppalmente de las imagenes.
        # Da por sentado que si encuentra alguna ruta relativa, al sacarle los puntos quedara absoluta
        # Esto siempre sera true para imagenes prontus
        if ($val_campo =~ /src *= *("|')\.\.\//i) {
          no warnings 'syntax'; # para evitar el msg "\2 better written as $2"
          $val_campo =~ s/src *= *("|')(\.\.\/)+(\w)/src=\1\/\3/ig;
          print STDERR 'reemplazando ../';
        } elsif ($val_campo =~ /src *= *("|')\w+?\//i) {
          no warnings 'syntax'; # para evitar el msg "\2 better written as $2"
          $val_campo =~ s/(src) *= *("|')(\w+?)\//\1=\2\/\3\//ig;
        };
      };
      print STDERR "marca: $nom_campo\n";
      # print stderr "antes replace en artic el vtxt\n";
      $buffer_tpl = &lib_prontus::replace_in_artic($val_campo, $nom_campo, $buffer_tpl);

      # Si el campo es un path de foto fija, parseo ademas las dimensiones de la foto en el articulo
      if ($nom_campo =~ /^FOTOFIJA_/i) {
        my ($msg, $foto_dimx, $foto_dimy) = &lib_prontus::dev_tam_img("$ROOTDIR$val_campo");
        $buffer_tpl =~ s/%%_W$nom_campo%%/$foto_dimx/isg;
        $buffer_tpl =~ s/%%_H$nom_campo%%/$foto_dimy/isg;
      };
    };# else
  };# while

  # Procesar Ifs
  $buffer_tpl = &procesa_condicional('IF', $buffer_tpl, \%data_campos);

  # Procesar NIfs
  $buffer_tpl = &procesa_condicional('NIF', $buffer_tpl, \%data_campos);

  # Realiza sustituciones especiales
  # %%_FECHACLONG%% = Fecha de creación, en formato largo
  #
  # %%_FECHACSHRT%% = Fecha de creación, en formato corto
  #
  # %%_FECHAC%%     = Fecha de creación, en formato ISO

  $FORM{'_FILE'} =~ /(\d{8})\d{6}\.\w+/;
  my $fechac = $1;

  my $fechaclong = &expande_fecha($fechac);
  $buffer_tpl =~ s/%%_FECHACLONG%%/$fechaclong/isg;

  my $fechacshrt = &des_normaliza_fecha($fechac);
  $buffer_tpl =~ s/%%_FECHACSHRT%%/$fechacshrt/isg;

  $buffer_tpl =~ s/%%_FECHAC%%/$fechac/isg;

  $FORM{'_FILE'} =~ /(\d{14})\.\w+/;
  my $ts = $1;
  $buffer_tpl =~ s/%%_TS%%/$ts/isg;
  $buffer_tpl =~ s/%%_FILE%%/$FORM{'_FILE'}/isg;
  $buffer_tpl =~ s/%%_PRONTUS_ID%%/$RUTA_PRONTUS/isg;

  return $buffer_tpl;

};
# ---------------------------------------------------------------
sub parse_noprontus {
# Realiza otros parseos a la pagina a imprimir (parseos no prontus)
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
sub get_plt_print {
# Obtiene contenido de la plantilla a usar para generar la pagina imprimible.

  my $xml_data = $_[0];

  # Obtiene el nombre de la plantilla del articulo.
  $xml_data =~ /<_plt>(.*?)<\/_plt>/si;
  my $plantilla_art = $1;

  # Lee el template de la pagina
  my $buffer_plt = &leeAllFile("$TDIR/$plantilla_art", '') if -s "$TDIR/$plantilla_art";
  $buffer_plt = &leeAllFile("$TDIR/imprimir.html", '') if $buffer_plt eq '';

  if ($buffer_plt eq '') {
    &show_msg('Error de configuraci&oacute;n: No hay plantilla para generar p&aacute;gina para imprimir.');
    exit;
  };

  $buffer_plt =~ s/$CRLF/\x0a/sg;
  return $buffer_plt;
};

# ---------------------------------------------------------------
sub get_xml_data {
# Obtiene xml del articulo a partir de la ruta del html

  my $url = $FORM{'_FILE'};
  $url =~ s/(\/\d{8})\/pags\//\1\/xml\//;
  $url =~ s/\.\w+$/\.xml/;
  $url =~ /(\d{14}\.xml)/;
  my $cont = &leeAllFile("$ROOTDIR$url", '');

  # Elimina marcas externas.
  $cont =~ s/.*?<_PRIVATE>(.*?)<\/_PRIVATE>.*?<_PUBLIC>(.*?)<\/_PUBLIC>.*?/$1\r\n$2/is;

  if ($cont eq '') {
    &show_msg('El servicio no est&aacute; disponible en este momento. [noxmldata] '
          . 'Intente nuevamente m&aacute;s tarde.');
    exit;
  };

  return $cont;

};
#~ # ---------------------------------------------------------------
#~ sub mail_html {
#~ # Version adaptada segun normas mailcenter.
  #~ my ($from,$to,$subject,$html_send) = @_;
  #~ my ($sender);
#~
  #~ $sender = new Mail::Sender { from => $from, smtp => $SMTP, headers => "MIME-Version: 1.0\r\nContent-type: text/html; charset=iso-8859-1\r\nContent-Transfer-Encoding: 7bit" };
  #~ $sender->Open({
    #~ from => $from,
    #~ to => $to,
    #~ subject => $subject
               #~ }) or die $Mail::Sender::Error,"\n";
  #~ $sender->Send($html_send);
  #~ $sender->Close();
#~ }; # mail_html

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
  my($msg) = $_[0];
  my($buffer) = &leeAllFile("$TDIR/gracias.html", '');
  if ($buffer =~ s/%%MSG%%/$msg/) {
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
  $RUTA_PRONTUS =~ /\/(\w+)$/si;
  my $nom_prontus = $1; # Nombre de la carpeta inicial del prontus, sin path, ie prontus_noticias

  my ($buffer) = &leeAllFile("$ROOTDIR$RUTA_PRONTUS/cpan/$nom_prontus" . '-var.cfg', '');
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
    my $clave = lc($1);
    if ($$vars_common{$clave} ne '')  {
      if ($$vars_common{$clave} =~ /<!\[CDATA\[(.*?)\]\]>/isg) {
        my $cdata_content = $1;
        if ($cdata_content) {
            $claves{$clave} = 'yes';
        } else {
            $claves{$clave} = 'no';
        };
      } else {
        $claves{$clave} = 'yes';
      };
    } else {
        $claves{$clave} = 'no';
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
      # print STDERR "X) $inicio $fin $elif\n"; # debug
      # Rescata la variable por la que se ha preguntado.
      my $var;
      if ($elif =~ /%%$sentencia\((\w+?)\)%%(.+?)%%\/$sentencia%%/s) {
        $var = lc($1);  # Variable de control.
        $cont = $2; # Contenido del IF

        if ($sentencia eq 'IF') {
          if ($claves{$var} ne 'yes') {
            # print STDERR "Se borra el IF\n";
            # Borra el IF, o sea, concatena el antes con el despues.
            $buffer = $aux1 . $aux2;
          }else{
            # print STDERR "Se deja el IF\n";
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


# -------------------------------END SCRIPT----------------------
