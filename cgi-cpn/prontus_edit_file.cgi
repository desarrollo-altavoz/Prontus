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
# Editar un archivo pasado por parametro con path completo absoluto, cargando su contenido en un objeto textarea de la plantilla utilizada.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# NO
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde prontus_edit_arbol.exe, via generacion de link.
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# <dir_publicador>/cpan/core/prontus_edit/prontus_edit_file.html
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
# ---------------------------------------------------------------
# Revision Prontus 8.0 - ych - 23/05/2002
# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use glib_cgi_04;
use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_edit;
use lib_prontus;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ------

my (%FORM, $LOOP);

main:{

  my ($plantilla, $pagina, $lista, $aux, $text_file);

  &glib_cgi_04::new();

  $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');

  # Deduce path conf del referer, en caso de no ser suministrado.
  $FORM{'path_conf'} = &get_path_conf() if ($FORM{'path_conf'} eq '');

  # Carga variables de configuracion.
  &lib_prontus::load_config(&lib_prontus::ajusta_pathconf($FORM{'path_conf'}));
  $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
  # Acceso permitido solo para admin
  if (($prontus_varglb::PRONTUS_EDITOR ne 'SI') or $prontus_varglb::USERS_PERFIL ne 'A') {
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result(&lib_language::_msg_prontus('_access_restricted_area'),&lib_language::_msg_prontus('_functionality_available_administrator'));
    exit;
  };

  $FORM{'path_file'} = &glib_cgi_04::param('_path_file');

  # Validaciones generales
  print "Content-Type: text/html\n\n";
  if ( (!(-f "$prontus_varglb::DIR_SERVER$FORM{'path_file'}")) && ($FORM{'path_file'} ne '') ) {
    print "<span class=\"error\">".&lib_language::_msg_prontus('_invalid_edit_file')."</span>";
    exit;
  };
  $FORM{'full_edit'} = &lib_edit::check_full_edit("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/extra.txt");
  if($FORM{'path_file'} ne '') {
    my $curr_dir = "$prontus_varglb::DIR_SERVER$FORM{'path_file'}";
    $curr_dir =~ s/^(.*?)\/[^\/]+$/\1/;
    my $msgdir = &lib_edit::valida_dirs($curr_dir, $FORM{'path_file'}, $FORM{'full_edit'});
    if($msgdir) {
      utf8::encode($msgdir);
      print "<span class=\"error\">$msgdir</span>";
      exit;
    };
  };

  # Se obtiene el nombre del archivo
  my $nom_archivo_editado;
  if($FORM{'path_file'} eq '') {
    $nom_archivo_editado = 'Sin Archivo';

  } elsif ($FORM{'path_file'} =~ /(.*?)\/([\w-\.]+)$/) {
    #$FORM{'path_file'} \1\/<span class="red">\2<\/span>/;
    $nom_archivo_editado = $2;

  } else {
    print STDERR "No se pudo extraer el nombre del archivo: $FORM{'path_file'}\n";
    print "<span class=\"error\">".&lib_language::_msg_prontus('_unable_extract_file_name')."</span>";
    exit;
  };

  # Se elige la plantilla a utilizar
  my $path_tmpl = '';
  if ($FORM{'path_file'} eq '') {
    $path_tmpl = $lib_edit::REL_TMPL_EDIT_EMPTY;

  } elsif (&lib_edit::is_editable($FORM{'path_file'})) {
    $path_tmpl = $lib_edit::REL_TMPL_EDIT_TEXT;

  } elsif (&lib_edit::is_image($FORM{'path_file'})) {
    $path_tmpl = $lib_edit::REL_TMPL_EDIT_IMG;

  } else {
    $path_tmpl = $lib_edit::REL_TMPL_EDIT_BIN;
  }

  # Se lee la plantilla a utilizar
  $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . $path_tmpl;
  if((! -f $plantilla) || (! -s $plantilla)) {
    print "<span class=\"error\">".&lib_language::_msg_prontus('_template_empty_or_no_exist')."</span>";
    exit;
  } else {
    $pagina = &glib_fildir_02::read_file($plantilla);
  }

  # Se parsean varias variables globales
  $FORM{'path_file'} =~ s/^$prontus_varglb::DIR_SERVER//; # por si las moscas
  $pagina =~ s/%%path_file%%/$FORM{'path_file'}/isg;
  $pagina =~ s/%%path_file_label%%/$nom_archivo_editado/isg;
  $pagina =~ s/%%_?path_conf%%/$FORM{'path_conf'}/ig;
  $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/ig;

  if ($FORM{'path_file'} ne '') {
    if (&lib_edit::is_editable($FORM{'path_file'})) {

      # Leer archivo que se va a editar y se hacen escapeos
      $text_file = '';
      $text_file = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$FORM{'path_file'}") if (-f "$prontus_varglb::DIR_SERVER$FORM{'path_file'}");
      $text_file =~ s/&/&amp;/sg;
      $text_file =~ s/</&lt;/sg;
      $text_file =~ s/>/&gt;/sg;
      # ajusta formato para presentarlo bien en la caja de edicion
      $text_file = &lib_prontus::ajusta_crlf($text_file);

      # Se detecta el tipo de retorno de carro
      my $formato_retcarro = 'unix';
      $formato_retcarro = 'windows' if ($text_file =~ /\r/); # mac o dos --> dos
      $pagina =~ s/%%formato_retcarro%%/$formato_retcarro/ig;

      # Se detecta la codificacion del archivo
      # my $charset_encoding = 'utf8';
      if ($text_file ne '') {
        my $tester = $text_file;
        my $es_utf8 = utf8::decode($tester);
        if($es_utf8) {
          # Do nothing
          $pagina =~ s/%%selected_utf8%%/selected="selected"/ig;
          $pagina =~ s/%%selected_ansi%%//ig;
        } else {
          utf8::encode($text_file);
          $pagina =~ s/%%selected_utf8%%//ig;
          $pagina =~ s/%%selected_ansi%%/selected="selected"/ig;
        };
      };

      # Se cargan los snippets
      $pagina = &lib_edit::carga_snippets($pagina);

      # Si es una plantilla de articulo, carga marcas del FID asociado a ella
      if ($FORM{'path_file'} !~ /\/plantillas\//) {
        $pagina =~ s/<!--combos_marcas-->.*?<!--\/combos_marcas-->//isg;
      } else {
        my $nom_plt_artic = $nom_archivo_editado;
        $nom_plt_artic = '' if ($FORM{'path_file'} !~ /\/plantillas\/artic\/fecha\/pags\//);
        # print STDERR "nom_plt_artic[$nom_plt_artic] path_file[$FORM{'path_file'}]\n";
        $pagina = &parsea_marcas_fid($pagina, $nom_plt_artic);
      };

      # borra marcas que no apliquen al contexto
      if ($FORM{'path_file'} !~ /\/plantillas\/edic\/nroedic\//) {
        $pagina =~ s/<!--marcas_port-->.*?<!--\/marcas_port-->//isg;
      };

      # Finalmente se limpia todo
      $pagina =~ s/<!--\/?\w+?-->//ig;

      # Reemplazar marca por el contenido del archivo a editar.
      # Esto al final para no interferir con el contenido.
      $pagina =~ s/%%text_file%%/$text_file/is;

    } else {

      my ($size, $lastmod, $wimg, $himg, $dim) = &lib_edit::get_datos_archivo("$prontus_varglb::DIR_SERVER$FORM{'path_file'}");

      $pagina =~ s/%%_file_nom%%/$nom_archivo_editado/sg;
      $pagina =~ s/%%_img_dim%%/$dim/;
      $pagina =~ s/%%_file_siz%%/$size/;
      $pagina =~ s/%%_file_mod%%/$lastmod/;

      $pagina =~ s/%%path_file%%/$FORM{'path_file'}/sg;
      $pagina =~ s/%%_wimagen%%/$wimg/;
      $pagina =~ s/%%_himagen%%/$himg/;
    }

  }
  print $pagina;
};


# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
# FORM_PLTS = 'fid_rotulo.html:Rotulo(rotulo.php)'
sub parsea_marcas_fid {
  my ($pagina) = $_[0];
  my ($nom_plantilla) = $_[1];

  my $marcas_usr_options;
  # Determinar tpls. validos.
  foreach my $key (keys %prontus_varglb::FORM_PLTS) { # key = fid_general.html:General

    my $nom_fid = $key;
    if ($nom_fid =~ /^([^\\\/:\*\?"><\|]+?):.+?$/) {
      $nom_fid = $1;
    } else {
      next;
    };
    my $value = $prontus_varglb::FORM_PLTS{$key}; # uno o mas nombre de template separados por ;
    # $nom_plantilla = qr/[^\\\/:\*\?"><\|;]+/ if (!$nom_plantilla);
    if (($value =~ /(^|;)$nom_plantilla(;|$)/) || (!$nom_plantilla)) {

      # Lee el fid y recopila las marcas ubicadas al interior de divs bodys
      my ($dir_macros_fid) = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/fid/macros";
      my $buffer_fid = &lib_prontus::carga_buffer_plt("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/fid/$nom_fid.html", $dir_macros_fid, '');

      # Se cambia esto por una forma más carretera
      if ($buffer_fid =~ /<!--INICIO_CONTENIDO_FID-->(.+?)<!--FIN_CONTENIDO_FID-->/isg) {
        my $campos_fid;
        my $area_con_campos = $1;
        # _txt
        while ($area_con_campos =~ /%%(_txt_\w+?)%%/ig) {
          $campos_fid .= "$1,";
        };
        # txt
        while ($area_con_campos =~ /%%(txt_\w+?)%%/ig) {
          $campos_fid .= "$1,";
        };
        # vtxt
        while ($area_con_campos =~ /%%(vtxt_\w+?)%%/ig) {
          $campos_fid .= "$1,";
        };

        # inputs de texto simple
        while ($area_con_campos =~ /<input\s+.*?\s+value\s*=\s*["']%%(\w+?)%%["']/isg) {
          $campos_fid .= "$1,";
        };

        # rdo
        while ($area_con_campos =~ /%%(rdo_\w+?)%%/ig) {
          $campos_fid .= "$1,";
        };
        # chk
        while ($area_con_campos =~ /%%(chk_\w+?)%%/ig) {
          $campos_fid .= "$1,";
        };
        # cmb
        while ($area_con_campos =~ /%%(cmb_\w+?)%%/ig) {
          $campos_fid .= "$1,";
        };
        # fotofija
        while ($area_con_campos =~ /%%(fotofija_(\w+))(\(?|%%)/ig) {
          $campos_fid .= "$1,_WFOTOFIJA_$2,_HFOTOFIJA_$2,";
        };
        # asocfile
        while ($area_con_campos =~ /%%(asocfile_(\w+?))%%/ig) {
          $campos_fid .= "$1,_SASOCFILE_$2,_EASOCFILE_$2,";
        };
        # swf
        while ($area_con_campos =~ /%%(swf_\w+?)%%/ig) {
          $campos_fid .= "$1,";
        };
        # multimedia
        while ($area_con_campos =~ /%%(multimedia_\w+?)%%/ig) {
          $campos_fid .= "$1,";
        };

        if ($campos_fid) {
          $campos_fid = uc $campos_fid;
          $marcas_usr_options .= "<option value=\"\" style=\"font-weight:bold;color:red;\">&raquo; $nom_fid:</option>\n";
          my @marcas = split(/\,/, $campos_fid);
          foreach my $marca (@marcas) {
            $marcas_usr_options .= "<option value=\"$marca\">$marca</option>\n";
          };
        };

      };
    };
  };

  if ($nom_plantilla && !$marcas_usr_options) {
    $marcas_usr_options = "<option value=\"\" style=\"color:red;\">".&lib_language::_msg_prontus('_template_without_fid_associated')."!</option>\n";
  };

  $pagina =~ s/%%marcas_usr_options%%/$marcas_usr_options/i;
  return $pagina;
};
# ---------------------------------------------------------------
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


# -------------------------------END SCRIPT----------------------

