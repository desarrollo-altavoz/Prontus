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
# SCRIPT.
# -----------
# prontus_tags_quick_search.cgi
#
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Para la busqueda rapida de tags desde el FID
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde el FID
#
# ---------------------------------------------------------------
# Tablas.
# -------------------
# TAGS
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 01/08/2011 - CVI - Primera version.
#
# ---------------------------------------------------------------

# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use DBI;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_dbi_02;
use glib_fildir_02;

use lib_prontus;
use lib_tags;
use strict;
use glib_cgi_04;
use lib_tags;

$| = 1; # Sin buffer. Despliega a medida que va leyendo.

# ---------------------------------------------------------------
# MAIN.
# -------------
my ($BD, %FORM);
# my (%XML_VISTAS);
#my (%EXISTING, %TAGS);

main:{

  # Ejemplo de invocacion:
  # http://192.168.6.24/cgi-cpn/prontus_tags_search.cgi?_path_conf=/prontus_toolbox/cpan/prontus_toolbox.cfg&existing=&defaultstr=&q=te

  &glib_cgi_04::new();
  $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
  $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  # Control de usuarios obligatorio
  ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

  # user no valido
  if ($prontus_varglb::USERS_ID eq '') {
      &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
  };

#  # Acceso permitido solo para admin o editor
#  if ($prontus_varglb::USERS_PERFIL eq 'P') {
#    &glib_html_02::print_pag_result('Acceso a Area Restringida','La funcionalidad requerida no está disponible para perfil Redactor',1,'exit=1,ctype=1');
#  };

  # Se define y comprueba la ruta del cache
  my $rutacache = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID$lib_tags::SITE_4FIDS";
  $rutacache =~ /^(.*?)\/[^\/]+$/;
  my $dircache = $1;
  &glib_fildir_02::check_dir($dircache);

  if(! -f $rutacache) {

    # Conectar a BD
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
      &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),$msg_err_bd,1,'exit=1');
    };

    # Se crea el cache
    &lib_tags::make_cache($BD, $prontus_varglb::PRONTUS_ID);
  }
  my $buffer = &glib_fildir_02::read_file($rutacache);

  # Se borra el botón para ir al admin de tags, si es redactor
  if ($prontus_varglb::USERS_PERFIL eq 'P') {
    $buffer =~ s/<!--admin_tags-->.*?<!--\/admin_tags-->//isg;
  };

  print "Content-Type: text/html\n\n";
  print $buffer;

}; # main

# ----------------------------------------------------------------
# -------------------------END SCRIPT----------------------
