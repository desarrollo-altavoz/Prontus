#!/usr/bin/perl

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

use strict;

my (%FORM);

my $URL_MANUAL = 'http://develop.prontus.cl';

main: {
  # Rescatar parametros recibidos
  &glib_cgi_04::new();
  $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');

  # Deduce path conf del referer, en caso de no ser suministrado.
  $FORM{'path_conf'} = &get_path_conf() if ($FORM{'path_conf'} eq '');

  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'path_conf'});
  $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  $FORM{'tab'} = &glib_cgi_04::param('tab');

  ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);

  print "Content-Type: text/html\n\n";
  # Generar pagina final (loopeando una fila modelo)
  my $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/prontus_help_main.html"; #_20110119
  my $pagina = &glib_fildir_02::read_file($plantilla);

  $pagina = &lib_prontus::set_coreplt_ppal($pagina);

  # Se parsean variables
  $pagina =~ s/%%_path_conf%%/$FORM{'path_conf'}/sg;
  $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/ig;

  my $version = $prontus_varglb::VERSION_PRONTUS;
  $version =~ s/^(\d+)\.(\d+)\.\d+.+$/\1_\2/;
  my $url_manual_desa = $URL_MANUAL . '/prontus_desarrollo_v' . $version;
  my $url_manual_oper = $URL_MANUAL . '/prontus_operacion_v' . $version;

  $pagina =~ s/%%_url_manual_desa%%/$url_manual_desa/ig;
  $pagina =~ s/%%_url_manual_oper%%/$url_manual_oper/ig;

  if ($FORM{'tab'} ne '') {
    if ($FORM{'tab'} =~ /^tab(\d+)$/) {
        $pagina =~ s/%%default_tab%%/$FORM{'tab'}/sg;
    } else {
        $pagina =~ s/%%default_tab%%//sg;
    };
  } else {
      $pagina =~ s/%%default_tab%%//sg;
  };

  print $pagina;


};
