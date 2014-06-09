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
# Parsea una plantilla para usarlo como player
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
#
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
#
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.1 - 03/07/2009 - PRB - Primera version
# 1.0.1 - 18/05/2010 - YCC - En Begin{} usa $Bin para determinar ruta de las libs CGI

# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);

    $pathLibsProntus =~ s/\/dam$//;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use strict;
use dam_varglb;
use glib_cgi_04;
use glib_fildir_02;

# ---------------------------------------------------------------
# MAIN.
# -------------
my (%FORM);

main: {
  # Rescatar parametros recibidos
  &glib_cgi_04::new();
  $FORM{'view_prontus'}    = &glib_cgi_04::param('view_prontus');
  $FORM{'view_tmpl'}    = &glib_cgi_04::param('view_tmpl');
  $FORM{'view_file'}    = &glib_cgi_04::param('view_file');

  print "Content-Type: text/html\n\n";

  if($FORM{'view_tmpl'} =~ /[\/\\]/) {
    print "Plantilla no válida";
    exit;
  };
  my $prontus = $ENV{'DOCUMENT_ROOT'} . '/' . $FORM{'view_prontus'};
  if(!(-d $prontus)) {
    print "Prontus no válido";
    exit;
  };
  my $tmpl = $prontus . $dam_varglb::DIR_TMPL . $FORM{'view_tmpl'};
  if(!(-f $tmpl)) {
    print "Plantilla no válida";
    exit;
  };

  my $buffer = glib_fildir_02::read_file($tmpl);
  $buffer =~ s/%%view_file%%/$FORM{'view_file'}/g;
  $buffer =~ s/%%view_prontus%%/$FORM{'view_prontus'}/g;
  print $buffer;
  exit;
}
