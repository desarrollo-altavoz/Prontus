#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

package coment_varglb;

# ----------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Definir e inicializar variables globales utilizadas en proyecto Comentarios.
# 1.0 - 08/2006 - YCH
# --------------------------BEGIN LIBRERIA------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ---------------------------------------------------------------

$VERSION = '1.5.0 - 10/09/2010';

# Determinar Dir del server.
$IP_SERVER = $ENV{'HTTP_HOST'};
$DIR_SERVER = $ENV{'DOCUMENT_ROOT'};  # Unix

if ($DIR_SERVER eq '') {
  $DIR_SERVER = $ENV{'PATH_TRANSLATED'}; # 'c:/proyectos/ap'; # nt
  $DIR_SERVER =~ s/\\/\//g;
  $DIR_SERVER =~ s/\/cgi-cpn.*//g;
};

# Parametros para la conexion a la Base de Datos
$NOM_BD = 'comentarios';
if ($IP_SERVER =~ /^192\.168\./) {
  $USER_BD = 'myadm';
  $PWD_BD = 'myadm.98.20';
  $SERVER_BD = 'localhost';
}
else {
  $USER_BD = 'usuario';
  $PWD_BD = 'pass';
  $SERVER_BD = 'localhost';
};

# Parametros para envio de correo electronico
$SMTP_SERVER = 'localhost';
$MAIL_ADM = '';
$MAIL_ADM_REPLYTO_NAME = '';
$MAIL_ADM_REPLYTO_EMAIL = '';


# Icono de foto existente
$ICON_VERFOTO = '<img src="/cpan/imag/ficha/foto.gif" width="21" height="22" border="0" valign="middle">';

#--------------------------------------------------------------------#
sub test_htaccess {

# Incorporarla al comienzo de los scripts del cpan: &test_htaccess();

  if ($ENV{'REMOTE_USER'} ne '') {
    return; # request autenticado.
  };

  # Request no autenticado, aborta.
  &execAbort("951 - Error en los datos enviados");

}; # testServers.
#--------------------------------------------------------------------#
sub execAbort {
  # Pagina de error en RAM.
  my($str) = $_[0];
  print "Content-Type: text/html\n\n";
  print q{
    <HTML>
    <HEAD>
      <TITLE>Error de Configuraci&oacute;n</TITLE>
    </HEAD>
    <BODY BGCOLOR="#ffffff">

    <P><CENTER>&nbsp;</CENTER></P>

    <P><CENTER><B><FONT COLOR="#FF0000" SIZE=+2>
  };
  if ($str eq '') {
    print 'Error de Configuraci&oacute;n';
  }
  else {
    print $str;
  };
  print '</FONT></B></CENTER></P></BODY></HTML>';
  exit;
}; # execAbort.


# -------------------------------END LIBRERIA--------------------

return 1;
