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
  ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

  print "Content-Type: text/html\n\n";
  # Acceso permitido solo para admin
  if (($prontus_varglb::PRONTUS_EDITOR ne 'SI') or ($prontus_varglb::USERS_PERFIL ne 'A')) {
    print "<span class=\"error\">La funcionalidad requerida está disponible sólo para el administrador del sistema.</span>";
    exit;
  };

  # Se lee y limpia el parametro con el directorio
  $FORM{'curr_dir'} = &glib_cgi_04::param('_dir');
  $FORM{'curr_dir'} = '' if ($FORM{'curr_dir'} eq '/');
  $FORM{'curr_dir'} =~ s/\/$//; # borra ultimo slash si es que viene.
  $FORM{'curr_dir'} =~ s/\.\.//g; # elimina puntos
  $FORM{'curr_dir'} =~ s/\/+/\//g;

  $FORM{'full_edit'} = &lib_edit::check_full_edit("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/extra.txt");

  # Si no viene el directorio se setea el directorio por defecto
  if(!$FORM{'curr_dir'}) {
    if (! $FORM{'full_edit'}) {
      $FORM{'curr_dir'} = "/$prontus_varglb::PRONTUS_ID" ;
    } else {
      $FORM{'curr_dir'} = "/";
    }
  }
  # Validaciones generales
  $DIR_DESDE = "$prontus_varglb::DIR_SERVER$FORM{'curr_dir'}";
  my $msgdir = &lib_edit::valida_dirs($DIR_DESDE, '', $FORM{'full_edit'});
  if($msgdir) {
    utf8::encode($msgdir);
    print "<span class=\"error\">$msgdir</span>";
    exit;
  }

  # Generar pagina final (loopeando una fila modelo)
  $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . $lib_edit::REL_TMPL_ARBOL;
  $pagina = &glib_fildir_02::read_file($plantilla);

  # En primer lugar, agrega macros
  my ($dir_macros_cpan) = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/macros";
  $pagina = &lib_prontus::add_macros($pagina, $dir_macros_cpan, '', '');
  $pagina =~ s/%25%25/%%/sg;

  # Rescatar imagenes de folder y filetext a usar.
  $IMG_FOLDER = 'dir';
  $IMG_FILETEXT = 'file';
#  if ($pagina =~ /<!--IMG_FOLDER:(.*?)-->/s) {
#    $IMG_FOLDER = $1;
#  };
#  if ($pagina =~ /<!--IMG_FILETEXT:(.*?)-->/s) {
#    $IMG_FILETEXT = $1;
#  };

  # Rescatar loop
  $pagina =~ /<!--LOOP-->(.*?)<!--\/LOOP-->/isg;
  $LOOP = $1;
  $lista = &show_dirs() . &show_files();
  $pagina =~ s/<!--LOOP-->.*?<!--\/LOOP-->/$lista/isg;

  # Se revisa si el directorio esta vacio
  if(! &lib_edit::is_empty_dir($DIR_DESDE)) {
    $pagina =~ s/<!--borrar-->.*?<!--\/borrar-->//isg;
  }

  # Se usa para formatear el directorio actual
  my $dirformat = $FORM{'curr_dir'};
  $dirformat = '/' if($dirformat eq '');
  $dirformat = &formateaDirectorio($dirformat, 0);
  $pagina =~ s/%%DIR_ACTUAL%%/$dirformat/ig;

  # Para el directorio superior
  $aux = $FORM{'curr_dir'};
  $aux =~ s/(.*)\/.+$/\1/;
  if($aux eq '') {
    if (! $FORM{'full_edit'}) {
      $pagina =~ s/%%dir_sup%%/\/$prontus_varglb::PRONTUS_ID/;
    } else {
      $pagina =~ s/%%dir_sup%%/\//;
    }
  } else {
    $pagina =~ s/%%dir_sup%%/$aux/;
  }

  # PArseo de variables globales
  $pagina =~ s/%%path_conf%%/$FORM{'path_conf'}/ig;
  $pagina =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/ig;
  $pagina =~ s/%%curr_dir%%/$FORM{'curr_dir'}/is;

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

# ---------------------------------------------------------------
sub show_files {

  # Los archivos posibles de editar son: .htm(l), .css, .cfg y .txt.
  my (@entries, $entry, $local_loop, $filas, $lnk, $target, $img, $css_class);

  @entries = &glib_fildir_02::lee_dir($DIR_DESDE);
  foreach $entry (sort{$a cmp $b} @entries) {
    # Solo files. validos.
    next unless( ($entry !~ /^\./g) and (-f "$DIR_DESDE/$entry") );

    if (! $FORM{'full_edit'}) {
      next if (($entry =~ /\.pl$/i) || ($entry =~ /\.exe$/i) || ($entry =~ /\.cgi$/i));
    };
    $local_loop = $LOOP;
    
    my $entryshort = &lib_edit::short_name($entry);
    $local_loop =~ s/%%nom_short_elemento%%/$entryshort/g;
    $local_loop =~ s/%%nom_elemento%%/$entry/g;
    $local_loop =~ s/%%tipo_elemento%%/$IMG_FILETEXT/g;

    my $file_name = "$entry";
    my $path_file = $DIR_DESDE;
    $path_file =~ s/^$prontus_varglb::DIR_SERVER//;
    $lnk = 'prontus_edit_main.' . $prontus_varglb::EXTENSION_CGI . "?_path_conf=$FORM{'path_conf'}&amp;_dir=$path_file&amp;_file=$file_name";
    $target = 'cont2';

    if (&lib_edit::is_editable($entry)) {
      $css_class = 'item edit';

    } elsif (&lib_edit::is_image($entry)) {
      $css_class = 'item imag';

    } else { # no linkear
      $css_class = 'item bin';
    };
    $local_loop =~ s/%%css_class%%/$css_class/;
    $local_loop =~ s/%%lnk%%/$lnk/;
    $local_loop =~ s/%%target%%/$target/;

    $filas .= $local_loop;
  };

  return $filas;

};
# ---------------------------------------------------------------
sub show_dirs {
  my (@entries, $entry, $local_loop, $filas, $lnk, $target);
  my $dir_base = '';
  $dir_base = $FORM{'curr_dir'} if($FORM{'curr_dir'} ne '/');

  @entries = &glib_fildir_02::lee_dir($DIR_DESDE);
  foreach $entry (sort{$a cmp $b} @entries) {
    # Solo dirs. validos.
    if ( ($entry !~ /^\./g) and (-d "$DIR_DESDE/$entry") ) {
      if (! $FORM{'full_edit'}) {
        next if ( ($entry =~ /^cgi/) || ($entry =~ /^wizard/) || ($entry eq 'prontus_edit') || ($entry eq 'core') || ($entry eq 'data'));
      };

      $local_loop = $LOOP;
      
      my $entryshort = &lib_edit::short_name($entry);
      $local_loop =~ s/%%nom_short_elemento%%/$entryshort/g;
      $local_loop =~ s/%%nom_elemento%%/$entry\//g;
      $local_loop =~ s/%%tipo_elemento%%/$IMG_FOLDER/g;

      $lnk = 'prontus_edit_arbol.' . $prontus_varglb::EXTENSION_CGI . "?_path_conf=$FORM{'path_conf'}&amp;_dir=$dir_base/$entry";

      $target = '_self';

      $local_loop =~ s/%%lnk%%/$lnk/;
      $local_loop =~ s/%%target%%/$target/;
      $local_loop =~ s/%%css_class%%/carpeta/;


      $filas .= $local_loop;
    };
  };

  return $filas;
};
# ---------------------------------------------------------------
sub formateaDirectorio {

  my $maxchars = 32;
  my ($dirformat, $level) = @_;
  my $textini;
  my $textfin;

  # Se obtiene el largo maximo
  my $largo = $maxchars - $level;
  if($largo < 11) {
    $largo = 11;
    $level = $maxchars - $largo;
  }

  # Se comprueba que haya más de un nivel restante
  if($dirformat =~ /^(\/[^\/]+?)(\/.+)$/) {
    $textini = $1;
    $textfin = $2;
    $textfin = &formateaDirectorio($textfin, $level + 1);

  } else {
    $textini = $dirformat;
    $textfin = '';
  }
  # Se crea el margen izquierdo
  my $margen = '';
  for(my $i = 0; $i <= $level; $i++) {
    $margen = $margen . '&nbsp;&nbsp;';
  }

  # Cuando sólo queda un nivel
  if(length($textini) > $largo) {
    $textini = substr($textini, 0, $largo) . '...';
  }
  # Se arma el string final
  my $textocompleto;
  if($textfin ne '') {
    $textocompleto = $textini . '<br/>' . $margen . $textfin;
  } else {
    $textocompleto = $textini;
  }
  return $textocompleto;
}


# -------------------------------END SCRIPT----------------------

