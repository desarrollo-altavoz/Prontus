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
# PROPOSITO.
# -----------
# Listar directorios relativos a la raiz del publicador para permitir la edicion de los archivos relacionados con este.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Genera el link para que se invoque a /cgi-cpn/prontus_edit_file.exe para editar el archivo clickeado.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde el web sin parametros o pasando por parametro el dir., relativo a la raiz del publicador, que se quiere examinar.
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# <dir_publicador>/cpan/core/prontus_edit/prontus_edit_arbol.html
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# TABLAS UTILIZADAS.
# -------------------
# NO
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 01_00  - 03/04/2002 - Primera Version.
# 1.1 - 03/05/2002 - Soporte para editar xml y xsl
# 1.2 - 06/05/2002 - Siu el usr. no es admin, tira un &nbsp;, para que no se repita el msg. de error junto con el de prontus_edit_file.exe
# ---------------------------------------------------------------
# Revision Prontus 8.0 - ych - 23/05/2002
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

use glib_cgi_04;
use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;
use lib_edit;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ------

my (%FORM, $LOOP, %COOKIES);
my ($DIR_DESDE, $IMG_FOLDER, $IMG_FILETEXT);
main:{

  my ($plantilla, $pagina, $lista, $aux);

  &glib_cgi_04::new();

  $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');

  # Deduce path conf del referer, en caso de no ser suministrado.
  $FORM{'path_conf'} = &get_path_conf() if ($FORM{'path_conf'} eq '');

  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'path_conf'});
  $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);

  print "Content-Type: text/html\n\n";
  # Acceso permitido solo para admin
  if (($prontus_varglb::PRONTUS_EDITOR ne 'SI') or $prontus_varglb::USERS_PERFIL ne 'A') {
    &glib_html_02::print_pag_result("Acceso a Area Restringida","La funcionalidad requerida está disponible sólo para el administrador del sistema.");
    exit;
  };

  # Generar pagina final (loopeando una fila modelo)
  $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . $lib_edit::REL_TMPL_MAIN;
  $pagina = &glib_fildir_02::read_file($plantilla);

  $pagina = &lib_prontus::set_coreplt_ppal($pagina);

  $pagina =~ s/%%path_conf%%/$FORM{'path_conf'}/sg;

  if(-d "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/plantillas/snippets") {
    $pagina =~ s/<!--snippets-->(.*?)<!--snippets-->/\1/isg;
  } else {
    $pagina =~ s/<!--snippets-->(.*?)<!--snippets-->//isg;
  }
  my $curr_dir = $DIR_DESDE;
  $curr_dir =~ s/^$prontus_varglb::DIR_SERVER//;
  $pagina =~ s/%%curr_dir%%/$curr_dir/is;

  $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/ig;
  my $uploads_permitidos_orig = $prontus_varglb::UPLOADS_PERMITIDOS_ORIG;
  $uploads_permitidos_orig =~ s/,/, /g;
  $pagina =~ s/%%uploads_permitidos_orig%%/$uploads_permitidos_orig/ig;

  print $pagina;
};


# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------

sub get_path_conf {
  # Deduce path conf del referer.
  $ENV{'HTTP_REFERER'} =~ /https?\:\/\/[^\/]+(\/.+\/cpan).+$/;
  my $path_conf = $1 . '/' . &get_id_prontus . '.cfg';
  return $path_conf;

};
# ---------------------------------------------------------------
sub get_id_prontus {
  # Deduce prontus_id del referer.
  $ENV{'HTTP_REFERER'} =~ /\/([^\/]+?)\/cpan.+$/;
  my $prontus_id = $1;
  return $prontus_id;
};
