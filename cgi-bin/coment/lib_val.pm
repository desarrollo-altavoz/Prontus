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
# Funciones custom, dependientes de la implementacion.

#---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
#-----------------------
# 1.0 - ycc - 12/2006 - Primera version.
#-------------------------------BEGIN LIBRERIA------------------
#---------------------------------------------------------------
# DECLARACIONES GLOBALES.
#------------------------

package lib_val;

use strict;
use coment_varglb;
use glib_fildir_02;
use glib_hrfec_02;
use lib_phpsession;
#----------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub validation {
# Validaciones custom.
# Retorna un msg en caso de haber problemas y '' en caso de ok.
  my $aux1 = $_[0];
  my $aux2 = $_[1];
  my %hash_tipos = %$aux1;
  my %form = %$aux2;
  undef $aux1;
  undef $aux2;

  # Obtiene campos del artic desde su xml
  my $fecha = substr($form{'OBJID'}, 0, 8);
  my $path_artic_xml = "$coment_varglb::DIR_SERVER/$form{'_prontus_id'}/site/artic/$fecha/xml/$form{'OBJID'}.xml";
  my ($protegido, $forocerrado,
      $apert_fecha, $apert_hora,
      $cierre_fecha, $cierre_hora) = &get_xml_data($path_artic_xml);
  # print STDERR "cierre_fecha[$cierre_fecha]\n";
  # valida q el foro no este cerrado, esto afecta indistintamente de si el foro requiere o no autenticacion
  if ($forocerrado) {
    return 'Este foro se encuentra cerrado.';
  };

  # fechas vienen como dd/mm/aaaa y horas como hh:mm
  my $cierre = &glib_hrfec_02::normaliza_fecha($cierre_fecha) . substr($cierre_hora,0,2) .  substr($cierre_hora,3,2); # aaaammddhhmm
  my $apert = &glib_hrfec_02::normaliza_fecha($apert_fecha) . substr($apert_hora,0,2) .  substr($apert_hora,3,2); # aaaammddhhmm
  my $ts_now = substr(&glib_hrfec_02::get_dtime_pack4(), 0, 12); # aaaammddhhmm
  if (($cierre <= $ts_now) and ($cierre >= $apert)) {
    return "Este foro se encuentra cerrado desde el $cierre_fecha - $cierre_hora hrs.";
  };
  if ($apert > $ts_now) {
    return "Este foro se encuentra cerrado hasta el $apert_fecha - $apert_hora hrs.";
  };

  my ($session_name, $session_path) = ($hash_tipos{$form{'OBJTIPO'}}{'PHP_SESSION_NAME'}, $hash_tipos{$form{'OBJTIPO'}}{'PHP_SESSION_PATH'});
  my ($ses_nickname) = &lib_phpsession::get_php_session_var('NICKNAME', $session_name, $session_path);
  my ($ses_bloqforos) = &lib_phpsession::get_php_session_var('BLOQFOROS', $session_name, $session_path);

  # ve si el foro esta protegido.
  if ($protegido) {
    # Si esta protegido y el user no esta autenticado...
    if (! $ses_nickname) {
      return 'Este foro requiere autenticación.';
    };
    # Si esta autenticado pero esta bloqueado...
    if ($ses_bloqforos == 'S') {
      return 'Acceso denegado.';
    };
  };

  # Validaciones Custom
  eval "require lib_custom_val;";
  if ($@) {
    # La libreria no existe, entonces no se hace nada
    return '';

  } else {
    # Si la librería se encuentra, se ejecuta la custom_validation
    my $result;
    my $sentencia = '$result = &lib_custom_val::custom_validation;';
    eval($sentencia);
    if ($@) {
      print STDERR 'Error ejecutando &lib_custom_val::custom_validation : ' . "$@\n";
    };
    return $result;
  };

};
# ---------------------------------------------------------------
sub get_xml_data {
# Cargar campos del xml del articulo.

  my ($path_xml) = $_[0];

  my $xml = &glib_fildir_02::read_file($path_xml);
  my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;
  $xml =~ s/$crlf/\x0a/sg;

  return (&get_xml_field($xml, 'CHK_protegido'),
          &get_xml_field($xml, 'CHK_forocerrado'),
          &get_xml_field($xml, 'apert_fecha'),
          &get_xml_field($xml, 'apert_hora'),
          &get_xml_field($xml, 'cierre_fecha'),
          &get_xml_field($xml, 'cierre_hora'));
};
# ---------------------------------------------------------------
sub get_xml_field {
# Obtiene el valor de un campo del xml del artic
  my ($xml, $nom_campo) = @_;
  my ($valor_campo);

  if ($xml =~ /<$nom_campo>(.*?)<\/$nom_campo>/isg) {
    $valor_campo = $1;
    if ($valor_campo =~ /<!\[CDATA\[(.*?)\]\]>/isg) {
      $valor_campo = $1;
    };
  };

  return $valor_campo;

};
# ---------------------------------------------------------------
return 1;

# -------------------------------END LIBRERIA--------------------
