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
# Ficha del editor de imagenes
#
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------

# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 04/2010 - CVI - Primera Version

# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ---------------------------------------------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_fildir_02;
use glib_cgi_04;
use lib_prontus;
use lib_tax;
use glib_hrfec_02;

use strict;


# ---------------------------------------------------------------
# MAIN.
# -------------
my (%COOKIES, %FORM);

main: {

  # Rescatar parametros recibidos
  &glib_cgi_04::new();
  $FORM{'path_conf'} = &glib_cgi_04::param('path_conf');

  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

  # TS del Artículo
  $FORM{'ts'} = &glib_cgi_04::param('ts');
  $FORM{'foto'} = &glib_cgi_04::param('foto');

  $FORM{'ts'} =~ /(\d{8})\d{6}/;
  my $dirfecha = $1;

  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'path_conf'});  # Prontus 6.0
  $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  # Control de usuarios obligatorio chequeando la cookie contra el dbm.
  ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

  # Se revisa el dbm
  if (&lib_prontus::open_dbm_files() ne 'ok') {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","No fue posible abrir archivos dbm.");
    exit;
  };

  # Se chequea la imagen


  my $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . '/prontus_imag_ficha.html';
  my $pagina = &glib_html_02::rellenar_plantilla(1, '%%path_conf%%', $FORM{'path_conf'},'','',
                                                                       $plantilla);


  my $image_path = "/$prontus_varglb::PRONTUS_ID/site/artic/$dirfecha/imag/$FORM{'foto'}";
  if(!(-f $prontus_varglb::DIR_SERVER . $image_path)) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","La imagen no es válida");
    exit;
  };

  my ($idfoto, $wimgOrig, $himgOrig) = &getImageSize($prontus_varglb::PRONTUS_ID, $FORM{'ts'}, $FORM{'foto'});
  if($idfoto eq '' || $wimgOrig == 0 || $himgOrig == 0) {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","La imagen no pudo ser editada");
    exit;
  };

  $pagina =~ s/%%nom_foto%%/$idfoto/isg;
  $pagina =~ s/%%image_path%%/$image_path/isg;
  $pagina =~ s/%%wimage_orig%%/$wimgOrig/isg;
  $pagina =~ s/%%himage_orig%%/$himgOrig/isg;

  $pagina =~ s/%%REL_PATH_PRONTUS%%/$prontus_varglb::RELDIR_BASE\/$prontus_varglb::PRONTUS_ID/isg;
  $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/isg;
  $pagina =~ s/<!--\w+-->//sg;
  $pagina =~ s/<!--\/\w+-->//sg;
  print "Cache-Control: no-cache\n";
  print "Cache-Control: max-age=0\n";
  print "Cache-Control: no-store\n";
  print "Content-Type: text/html\n\n";
  print $pagina;
};

# ------------------------------------------------
sub getImageSize {

  my ($prontus, $ts, $foto) = @_;
  return (0, 0) unless($ts =~ /(\d{8})\d{6}/);
  my $dirfecha = $1;
  my $xml = '/'.$prontus.'/site/artic/'.$dirfecha.'/xml/'.$ts.'.xml';
  my $buffer = &glib_fildir_02::read_file($prontus_varglb::DIR_SERVER . $xml);

  my $width = 0;
  my $height = 0;
  my $idfoto = '';

  if($buffer =~ /<_nom([\w]+)>$foto<\/_nom\1>/) {
    $idfoto = $1;
    if($buffer =~ /<_w$idfoto>(\d+)<\/_w$idfoto>/) {
      $width = $1;
    };
    if($buffer =~ /<_h$idfoto>(\d+)<\/_h$idfoto>/) {
      $height = $1;
    };
  };
  return ($idfoto, $width, $height);
};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

# -------------------------------END SCRIPT----------------------
