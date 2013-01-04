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
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.1 - 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.2 - 16/05/2001 - Revision general de detalles de forma.

# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0
# Prontus 8.0 - 03/06/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    unshift(@INC,$Bin); # Para dejar disponibles las librerias
};

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_fildir_02;
use lib_prontus;
use glib_cgi_04;
use DBI;

$| = 1;

# ---------------------------------------------------------------
# MAIN.
# -------------
my $AMBIENTE_WEB;

main : {
  my ($buffer, $root_web, $path_conf, $path_lista_prontus);
    
  if ($ENV{'SERVER_NAME'} ne '') { # ambiente web
    &glib_cgi_04::new();
    $FORM{'prontus'} = &glib_cgi_04::param('prontus');
    $FORM{'ports'} = &glib_cgi_04::param('ports'); # port1/port2/port3 (OPTATIVO, portadas a procesar, si viene, se procesan solo estas ports en vez de todas)
    print "Content-Type: text/html\n\n";
    $| = 1;
    $AMBIENTE_WEB = 1;
    &valida_param();
  } else {
    $FORM{'prontus'} = $ARGV[0];
    $prontus_varglb::IP_SERVER = $ARGV[1];
    $FORM{'ports'} = $ARGV[2];
    &valida_param();
  };

  &check_prontus();


}; # main



# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub valida_param {

  if ( (! -d "$prontus_varglb::DIR_SERVER/$FORM{'prontus'}") || ($FORM{'prontus'} eq '') || ($FORM{'prontus'} =~ /^\//) )  {
    print "\nError: Directorio del publicador no es válido.";
    if ($AMBIENTE_WEB) {
      print "<br>Debe indicar el nombre del Prontus a procesar, ejemplo: prontus=prontus_noticias";
    }
    else {
      print "\nDebe indicar el nombre del Prontus a procesar (ej: prontus_noticias), como primer parametro de esta CGI\n";
    };
    exit;
  };

  if (!$AMBIENTE_WEB) {
    if ($prontus_varglb::IP_SERVER eq '') {
        print "\nDebe indicar el nombre del servidor (ej: www.altavoz.net), como segundo parametro de esta CGI\n";
        exit;
    };
  };


  # Carga variables de configuracion.
  my $path_conf = &get_path_conf();

  &lib_prontus::load_config($path_conf);

};
# ---------------------------------------------------------------
sub get_path_conf {

  return "$prontus_varglb::DIR_SERVER/$FORM{'prontus'}/cpan/$FORM{'prontus'}.cfg";

};

# ---------------------------------------------------------------
sub check_prontus {

  my ($filler, $entry);

  if ($prontus_varglb::CONTROL_FECHA ne 'SI') {
    print "\n Error : El Prontus indicado no corresponde a uno con Control de Fechas. \n";
    exit;
  };

  # Chequea ediciones.
  # procesa edicion vigente, la ultima y la base.
  my (@ediciones) = &lib_prontus::get_edics4update();
  foreach $entry (@ediciones) {
    $EDIC = $entry;
    &get_main_data();
    &check_portadas();
    # Borra cache de listas de articulos del cpan
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");

  };

};

# --------------------------------------------------------------------#
sub get_main_data {
 # print "Content-Type: text/html\n\n"; # debug
# Obtiene datos principales del formulario.
my($id, $cod, @campos);


  $DDIR = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . '/%%DIR_FECHA%%';

  # Directorio de Secciones existentes
  $DST_SEC = $prontus_varglb::DIR_SERVER .
             $prontus_varglb::DIR_CONTENIDO .
             $prontus_varglb::DIR_EDIC .
             "/$EDIC" .
             $prontus_varglb::DIR_SECC;

  # Path absoluto al dir. donde residen los templates de portadas.
  $DST_TSEC = $prontus_varglb::DIR_SERVER .
              $prontus_varglb::DIR_TEMP .
              $prontus_varglb::DIR_EDIC .
              $prontus_varglb::DIR_NROEDIC .
              $prontus_varglb::DIR_SECC;



  $DST_PAG = $prontus_varglb::DIR_SERVER . $DDIR . $prontus_varglb::DIR_PAG;

  # Path absoluto a Directorio destino de las imagenes.
  $DST_IMG = $prontus_varglb::DIR_SERVER . $DDIR . $prontus_varglb::DIR_IMAG;

  # Path absoluto a Directorio destino de las swf. # 8.0
  $DST_SWF = $prontus_varglb::DIR_SERVER . $DDIR . $prontus_varglb::DIR_SWF;

  # Path absoluto a Directorio destino de los archivos windowsmedia. # 8.1
  $DST_WMEDIA = $prontus_varglb::DIR_SERVER . $DDIR . $prontus_varglb::DIR_MMEDIA;

  # Path absoluto a Directorio destino de los archivos gericos asociados. # 1.2
  $DST_ASOCFILE = $prontus_varglb::DIR_SERVER . $DDIR . $prontus_varglb::DIR_ASOCFILE;


  return 1;
};
# --------------------------------------------------------------------#
sub is_base_port {
    my ($port) = $_[0];
    foreach my $bport (@prontus_varglb::BASE_PORTS) {
      if ($port eq $bport) {
        return 1;
      };
    };
    return 0;
};
# --------------------------------------------------------------------#
sub check_portadas {
# Regenera todas las portadas publicadas.

my ($pathdir_pags, $pathdir_seccs, @entries, $entry, $arch_seccion, $text_seccion, $text_final, $id);

  my @ports = split(/\//, $FORM{'ports'});

  # Deduce del path completo de la portada, el del xml.
  my ($pathdir_seccs_xml) = $DST_SEC;
  $pathdir_seccs_xml =~ s/\/port$/\/xml/;

  @entries = &glib_fildir_02::lee_dir($pathdir_seccs_xml);
  #~ print "pathdir_seccs_xml[$pathdir_seccs_xml]\n";
  # Recorre las secciones publicadas

  foreach $entry (@entries) {
    if (($entry !~ /^\./g) and ($entry !~ /^preview/ig)) {

      my $procesar_port = 1; # por omision las procesa todas
      # si esta el param correspondiente, procesa solo las portadas especificadas

      if ($#ports >= 0) {
        $procesar_port = 0;
        foreach my $specific_port (@ports) {
            if ($entry eq "$specific_port.xml") {
                $procesar_port = 1;
                last;
            };
        };
      };
      next if (!$procesar_port);

      $arch_seccion = "$pathdir_seccs_xml/$entry";
      
      if ((-s $arch_seccion) and (! -d $arch_seccion)) {
        $text_seccion = &glib_fildir_02::read_file($arch_seccion);
        # $text_final = $text_seccion;
        # Rescatar la info de c/artic de la seccion correspondiente

        while ($text_seccion =~ /<rowartic>[ \n]*?<dir>(\d+?)<\/dir>[ \n]*?<file>(.*?)<\/file>[ \n]*?<area>(\d*?)<\/area>[ \n]*?<ord>(\d*?)<\/ord>[ \n]*?(<vb>(\w*?)<\/vb>)?[ \n]*?<?i?n?>?([\w\/\-]*?)<?\/?i?n?>?[ \n]*?<?o?u?t?>?([\w\/\-]*?)<?\/?o?u?t?>?[ \n]*?<?p?u?b?>?(\d?)<?\/?p?u?b?>?[ \n]*?<\/rowartic>/isg) {

          # print STDERR "ENTRA";
          my ($dirfecha,$art,$area,$prio,$pub,$ext_art,$vb) = '';
          ($dirfecha,$art,$area,$prio,$vb,$pub) = ($1,$2,$3,$4,$6,$9);

          $lib_prontus::AREA{$art} = $area;      # Asocia area al articulo.
          $lib_prontus::PRIO{$art} = $prio;      # Asocia prioridad correspondiente.
          if ($vb eq '') { $vb = 1; };
          $lib_prontus::VB{$art} = $vb;      # Asocia VoBo correspondiente.
          $lib_prontus::DIR_FECHA{$art} = $dirfecha;

        };# while

        $entry = &get_nom_port($entry); # obtener nombre de la portada a re-escribir
        #~ print "entry[$entry]\n";
        
        if ($prontus_varglb::MULTI_EDICION eq 'SI') {
            # solo para multi-edicion: si la edicion es la base, actualiza solo las portadas declaradas como BASE_PORTS
            next if (($EDIC eq 'base') && (! &is_base_port($entry)));
        };
        
        if ($entry) {

          print "<br>Actualizando Portada [$entry]" if ($AMBIENTE_WEB);

          # Primero para la vista por defecto (o sea, sin vista)
          my $mv = '';
          my $sin_regen_xml = 0;
          my $ts_preview = '';
          my $users_perfil = 'A';
          &lib_prontus::make_portada("$DST_SEC/$entry", $DST_TSEC . "/$entry", $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
                                   $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
                                   $EDIC, $sin_regen_xml, $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
                                   $ts_preview, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $users_perfil);


          # Ahora proceso multivistas

          $sin_regen_xml = 1; # para no reescribir el xml
          $ts_preview = '';
          $users_perfil = 'A';
          foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
            &lib_prontus::make_portada("$DST_SEC/$entry", $DST_TSEC . "/$entry", $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
                                     $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
                                     $EDIC, $sin_regen_xml, $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
                                     $ts_preview, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $users_perfil);
          };

          &lib_prontus::write_log('Actualizar', 'Portada', "$DST_SEC/$entry");
        }
        else {
          if($arch_seccion =~ /^(.*?)\/([^\/]+)$/) {
            my $dirxml = $1;
            my $namexml = $2;
            &glib_fildir_02::check_dir("$dirxml/bak/cron_fechas");
            File::Copy::move($arch_seccion, "$dirxml/bak/cron_fechas/$namexml");
            print "\n Warning: se mueve xml sin portada [$arch_seccion] a bak/cron_fechas\n";
            print "<br>" if ($AMBIENTE_WEB);
          } else {
            print "\n Warning: no existe portada para [$arch_seccion]\n";
            print "<br>" if ($AMBIENTE_WEB);
          };
        };

        %lib_prontus::AREA = ();
        %lib_prontus::PRIO = ();
        %lib_prontus::VB = ();
        %lib_prontus::DIR_FECHA = ();

      };# if

    };# if

  };# foreach

  print "<br><br>Proceso terminado." if ($AMBIENTE_WEB);


};

# ---------------------------------------------------------------
sub get_nom_port {
# Obtiene de la lista de tpls. de portadas la primera cuyo nombre sin extension coincida con el q viene por param.
  my $port_xml = $_[0];
	my $dir_tpl_seccs = $DST_TSEC;

  $port_xml =~ s/\.\w+$//;
  my ($entry);
  foreach $entry (keys %prontus_varglb::PORT_PLTS) {
    if ((-s "$dir_tpl_seccs/$entry") and (! -d "$dir_tpl_seccs/$entry")) {
      # print "entry[$entry] - port_xml[$port_xml]\n";
      if ($entry =~ /^$port_xml\.\w+$/) {
        return $entry;
      };
    };
  };

  return '';
};


# -------------------------------END SCRIPT----------------------
