#!/usr/bin/perl


# -------------------------------COMENTARIO GLOBAL---------------
# ---------------------------------------------------------------
# PROPOSITO .
# -----------
# Desplegar pagina intermedia para preview o view de portada actual.
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
# ------------------------

# ---------------------------------------------------------------

# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 10/2006 - Primera Version.

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};
use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use lib_prontus;
use glib_html_02;

use glib_cgi_04;

use DBI;
use glib_dbi_02;
use lib_secc;

# ---------------------------------------------------------------
# MAIN.
# -------------

  my ($BD, %FORM);

  #  print "Content-Type: text/html\n\n"; # debug
  # Rescatar parametros recibidos.
  &glib_cgi_04::new();
  $FORM{'accion'} = &glib_cgi_04::param('accion'); # veractual | preview

  $FORM{'path_conf'} = &glib_cgi_04::param('path_conf');
  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

  &lib_prontus::load_config($FORM{'path_conf'});
  $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  my $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/prontus_port_view.html";

  my $pagina = &glib_fildir_02::read_file($plantilla);


  $pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/ig;


  if (($prontus_varglb::CONTROL_FECHA ne 'SI') || ($FORM{'accion'} eq 'veractual')) {
    $pagina =~ s/<!--CONTROL_FECHA-->.*?<!--\/CONTROL_FECHA-->//sg;
  }
  else {
    $pagina =~ s/<!--\/?CONTROL_FECHA-->//sg;
  };

  my $cmb_mv;
  if (keys(%prontus_varglb::MULTIVISTAS)) {
    $pagina =~ s/<!--\/?MULTIVISTAS-->//sg;
    $cmb_mv = &lib_prontus::generar_popup_multivistas();
    $pagina =~ s/%%_CMB_MV%%/$cmb_mv/;
  }
  else {
    $pagina =~ s/<!--MULTIVISTAS-->.*?<!--\/MULTIVISTAS-->//sg;
  };

  if ($FORM{'accion'} eq 'veractual') {
    $pagina =~ s/<!--PREVIEW-->.*?<!--\/PREVIEW-->//sg;
    $pagina =~ s/<!--\/?VERACTUAL-->//sg;
  }
  elsif ($FORM{'accion'} eq 'preview') {
    $pagina =~ s/<!--VERACTUAL-->.*?<!--\/VERACTUAL-->//sg;
    $pagina =~ s/<!--\/?PREVIEW-->//sg;
  }
  else {
    $pagina =~ s/<!--PREVIEW-->.*?<!--\/PREVIEW-->//sg;
    $pagina =~ s/<!--VERACTUAL-->.*?<!--\/VERACTUAL-->//sg;
  };

  $pagina =~ s/%%path_conf%%/$FORM{'path_conf'}/;

  print "Content-Type: text/html\n\n";
  print $pagina;



# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
# ---------------------------------------------------------------

# -------------------------------END SCRIPT----------------------
