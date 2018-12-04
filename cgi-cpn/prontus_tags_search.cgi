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
# prontus_tags_search.cgi
#
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /prontus/
#
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Para buscar en el campo de busqueda de los tags
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde el FID a través del autocomplete
#
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# No requiere plantillas
#
# ---------------------------------------------------------------
# Tablas.
# -------------------
# TAGS y TAGSART
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 20/05/2011 - CVI - Primera version.
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
use lib_secc;

$| = 1; # Sin buffer. Despliega a medida que va leyendo.

# ---------------------------------------------------------------
# MAIN.
# -------------
my ($BD, %FORM,);
# my (%XML_VISTAS);
my (%EXISTING, %TAGS);

main:{

  # Ejemplo de invocacion:
  # http://192.168.6.24/cgi-cpn/prontus_tags_search.cgi?_path_conf=/prontus_toolbox/cpan/prontus_toolbox.cfg&existing=&defaultstr=&q=te

  &glib_cgi_04::new();
  $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

  $FORM{'existing'} = &glib_cgi_04::param('existing');
  $FORM{'query'} = &glib_cgi_04::param('q');
  $FORM{'defaultstr'} = &glib_cgi_04::param('defaultstr');

  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
  $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # user no valido
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

#    # Acceso permitido solo para admin o editor
#    if ($prontus_varglb::USERS_PERFIL eq 'P') {
#      &glib_html_02::print_pag_result('Acceso a Area Restringida','La funcionalidad requerida no está disponible para perfil Redactor',1,'exit=1,ctype=1');
#    };

  print "Content-Type: text/plain\n\n";

  # Se limpia y comprueba el nombre del tag
  $FORM{'query'} = &glib_str_02::trim($FORM{'query'});
  # $FORM{'query'} = &lib_tags::limpiar_nom($FORM{'query'});
  print STDERR "query[$FORM{'query'}]\n";
  if($FORM{'query'} eq '') {
    # print "0|$FORM{'defaultstr'}\n";
    exit;
  }

  # Se comprueba si no es el valor por defecto
  if(lc($FORM{'query'}) eq lc($FORM{'defaultstr'})) {
    print "0|$FORM{'defaultstr'}\n";
    exit;
  }

  # Conectar a BD
  my $msg_err_bd;
  ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
  if (! ref($BD)) {
      &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_msg_generic_error'),$msg_err_bd,1,'exit=1');
  };

  # Se obtienen los que ya existen o han sido asignados
  &procesa_existing($FORM{'existing'});

  &busca_tags($FORM{'query'});

  my $maxartics = $lib_tags::MAX_ARTICS_PER_SEARCH;
  my $counter = 0;
  foreach my $tags_id (sort keys %TAGS) {
      # print STDERR "$tags_id -> $EXISTING{$tags_id}\n";
      next if($EXISTING{$tags_id} ne '');
      my $tags_tag = $TAGS{$tags_id};
      print "$tags_id|$tags_tag\n";
      $counter++;
      last if($counter >= $maxartics);
  };
}; # main

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub procesa_existing {
    my $existing = shift;
    # print STDERR 'Existing: '.$existing."\n";
    my @tagaux = split ',' , $existing;
    foreach my $str (@tagaux) {
        if($str =~ /^(.*?)\|(.*?)$/) {
            $EXISTING{$1} = $2;
            # print STDERR '-> '.$1.' -> '.$2."\n";
        };
    };
};
# ---------------------------------------------------------------
sub busca_tags {

  my $query = shift;
  my ($tags_id, $tags_tag);

  # &glib_dbi_02::ejecutar_sql($BD, "SET NAMES 'utf8' COLLATE 'utf8_general_ci'");
  # glib_dbi_02::ejecutar_sql($BD, "SET CHARACTER SET 'utf8'");

  $query = $BD->quote($query);
  $query =~ s/'$/%'/; # dirty

  my $sql = "select TAGS_ID,TAGS_TAG from TAGS where TAGS_MOSTRAR = 1 and TAGS_TAG like $query ";
  print STDERR "sql tags: $sql\n";
  my $salida = &glib_dbi_02::ejecutar_sql_bind($BD, $sql, \($tags_id, $tags_tag));
  while($salida->fetch){
    # $tags_tag = &lib_prontus::escape_html($tags_tag);
    $TAGS{$tags_id} = $tags_tag;
  };
};

# ----------------------------------------------------------------
# -------------------------END SCRIPT----------------------
