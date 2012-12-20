#!/usr/bin/perl

# Funciones utilizadas por el editor de archivos Prontus

package lib_edit;
#use strict;
use Digest::MD5 qw(md5_hex);
use lib_cookies;
use glib_fildir_02;
use glib_str_02;
use glib_hrfec_02;

use lib_prontus;

# Variables globales del modulo
$REL_TMPL_EDIT_TEXT = "/prontus_edit/prontus_edit_file_text.html";
$REL_TMPL_EDIT_IMG = "/prontus_edit/prontus_edit_file_img.html";
$REL_TMPL_EDIT_BIN = "/prontus_edit/prontus_edit_file_bin.html";
$REL_TMPL_EDIT_EMPTY = "/prontus_edit/prontus_edit_file_empty.html";

$REL_TMPL_ARBOL = "/prontus_edit/prontus_edit_arbol.html";
$REL_TMPL_MAIN = "/prontus_edit/prontus_edit_main.html";

$EDIT_PERMITIDOS = 'xsl,xml,htm,html,css,csv,cfg,txt,php,asp,jsp,js';
$IMAG_PERMITIDOS = 'jpg,jpeg,jpe,gif,png,bmp';

#---------------------------------------------------------------#
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub check_full_edit {
  my ($extra_path) = $_[0];
  if (! -f $extra_path) {
    # Escribe archivo extras (para edit)
    &glib_fildir_02::write_file($extra_path, &glib_str_02::random_string(8));
    return 0;
  };
  my ($data) = &glib_fildir_02::read_file($extra_path);
  my (%cookies) = &lib_cookies::get_cookies();
  return 1 if (Digest::MD5::md5_hex($data) eq $cookies{'extra'});
  return 0;
};

# ---------------------------------------------------------------
sub valida_dirs {
# $curr_dir: Debe ser ruta absoluta incluyendo el document root
# $path_file: Debe ser sólo la ruta del archivo (desde la raiz del server)
  my ($curr_dir, $path_file, $full_edit) = @_;
  
  my $dir_prontus_full = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID";
  if($curr_dir !~ /^$prontus_varglb::DIR_SERVER/) {
      $curr_dir = "$prontus_varglb::DIR_SERVER$curr_dir";
  };
  if($path_file && ($path_file !~ /^$prontus_varglb::DIR_SERVER/)) {
      $path_file = "$prontus_varglb::DIR_SERVER$path_file";
  };
  
  if (($curr_dir =~ /\.\./) || (! -d $curr_dir)) {
    print STDERR "[1] curr_dir: $curr_dir\n";
    return "Directorio no v&aacute;lido.";
  };
  print STDERR "valida_dirs: $curr_dir\n";
  if (!$full_edit) {
    if ($curr_dir !~ /^\//) {
      print STDERR "[2] curr_dir: $curr_dir\n";
      return "Directorio no v&aacute;lido.";
    };

    if (($curr_dir =~ /^$dir_prontus_full\/cpan\/core/) || ($curr_dir =~ /^$dir_prontus_full\/cpan\/data/)) {
      print STDERR "[3] curr_dir: $curr_dir\n";
      return "Directorio no es v&aacute;lido.";
    };
    # debe estar dentro de del prontus_dir
    if($curr_dir !~ /^$dir_prontus_full/) {
        print STDERR "[4] curr_dir: $curr_dir -> $dir_prontus_full\n";
        return "El directorio no es v&aacute;lido";
    }
    
    if ($path_file && ($path_file !~ /^$dir_prontus_full/)) {
        print STDERR "[1] path_file: $path_file\n";
        return "Archivo no es v&aacute;lido.";
    }

    if (($path_file =~ /^$dir_prontus_full\/cpan\/core/) || ($path_file =~ /^$dir_prontus_full\/cpan\/data/)) {
      print STDERR "[2] path_file: $path_file\n";
      return "Archivo no es v&aacute;lido.";
    };
  };
  return '';
};
# ---------------------------------------------------------------
sub get_datos_archivo {

  my $file = $_[0];
#  print STDERR "get_datos_archivo: $file\n";
  my ($size, $lastmod, $wimg, $himg, $msg, $dim);

  my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$sizeb, $atime,$mtime,$ctime,$blksize,$blocks) = stat($file);
  $size = &lib_prontus::bytes2kb($sizeb);
  $lastmod = ucfirst(&glib_hrfec_02::get_date_time(0,1,1,1,1,0,$mtime));

  if(&lib_edit::is_image($file)) {
    if($file =~ /\.bmp$/i) {
      ($msg, $wimg, $himg) = &lib_prontus::ancho_alto_bmp($file);
    } else {
      ($msg, $wimg, $himg) = &lib_prontus::dev_tam_img($file);
    }
    if($msg || $wimg == 0 || $himg == 0) {
      print STDERR "Error al leer las dimensiones de la imagen: $msg\n";
      $dim = 'Desconocido';
      $wimg = 'width="100"';
      $himg = '';
    } else {
      $dim = "$wimg x $himg px";
      if($wimg > 100) {
        $wimg = 'width="100"';
        $himg = '';
      } else {
        $wimg = 'width="'.$wimg.'"';
        $himg = '';
      }
    }
  } else {
    $dim = 'Desconocido';
    $wimg = '';
    $himg = '';
  }
  return ($size, $lastmod, $wimg, $himg, $dim);
}
# ---------------------------------------------------------------
sub carga_snippets {

  my $pagina = $_[0];

  # Carga snippets
  my $snippDir = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/plantillas/snippets";
  &glib_fildir_02::check_dir($snippDir);
  my @lisdir = &glib_fildir_02::lee_dir($snippDir);
  @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
  my $snippets_vars;
  my %snippetsNom;
  my %cont;

  foreach my $fileSnipp (@lisdir) {
    if (-f "$snippDir/$fileSnipp") {
      # encode single quotes as "\x27" and double quotes as "\x22",
      my $code = &glib_fildir_02::read_file("$snippDir/$fileSnipp");
      $code = &lib_prontus::ajusta_crlf($code);
      # evita que el codigo cargado interfiera al ponerlo dentro de comillas simples y asignarlo
      # a una variable JS.
      $code =~ s/\n/\\n/sg;
      $code =~ s/'/\\x27/sg;
      $code =~ s/"/\\x22/sg;
      $code =~ s/</\\x3c/sg;
      $code =~ s/>/\\x3e/sg;
      $code = '\n' . $code . '\n';
      $fileSnipp =~ s/\..*$//;
      $fileSnipp =~ s/[^\w]/_/g; # sanitiza
      # evita que al sacar la extension se repitan los snippets por llamarse igual y tener
      # distinta extension: solo considera el primero
      if (exists $snippetsNom{$fileSnipp}) {
        $cont{$fileSnipp}++; # contadores individuales para c/archivo
        $fileSnipp .= $cont{$fileSnipp};
      };
      $snippetsNom{$fileSnipp} = 1;

      $snippets_vars .= "var $fileSnipp = '$code';\n";
    };
  };
  # Si por casualidad en text_file viniera la cadena %%snippets_vars%% no se reemplazara, ya que se
  # reemplaza solo la primera ocurrencia y esa sera siempre la que esta al comienzo en la seccion javascript.
  $pagina =~ s/%%snippets_vars%%/$snippets_vars/is;

  my $snippets_options;
  foreach my $snippetNom (keys %snippetsNom) {
    $snippets_options .= "<option value=\"$snippetNom\">$snippetNom</option>\n";
  };
  $snippets_options .= "<option value=\"\" style=\"color:red;\">Sin Snippets</option>\n" if (!$snippets_options);
  $pagina =~ s/%%snippets_options%%/$snippets_options/is;

  return $pagina;
}
# ---------------------------------------------------------------
sub is_uploadable {
  # Se chequea si el archivo se deja subir o no
  my ($file) = @_;
  return &lib_prontus::check_extension($file, $prontus_varglb::UPLOADS_PERMITIDOS);
}

# ---------------------------------------------------------------
sub is_editable {
# Se chequea si el archivo es editable o no
  my ($file) = @_;
  return &lib_prontus::check_extension($file, $lib_edit::EDIT_PERMITIDOS);
};
# ---------------------------------------------------------------
sub is_image {
# Se chequea si el archivo es una imagen o no
  my ($file) = @_;
  return &lib_prontus::check_extension($file, $lib_edit::IMAG_PERMITIDOS);
};

# ---------------------------------------------------------------
sub clearname {
  my ($name) = @_;
  $name =~ s/[^a-zA-Z0-9_\-\.\(\)]//sig;
  return $name;
}

# ---------------------------------------------------------------
sub check_name {
  my ($name) = @_;
  return 0 unless($name ne '');
  return 0 if($name =~ /[^a-zA-Z0-9_\-\.\(\)]/sig);
  return 1;
}

# ---------------------------------------------------------------
sub is_empty_dir {

  my ($dir2remove) = @_;
  if(! -d $dir2remove) {
    return 0;
  }

  my @content = &glib_fildir_02::lee_dir($dir2remove);
  my $flag = 1;
  foreach my $item (@content) {
    next if($item eq '..' || $item eq '.');
    $flag = 0;
    last;
  }
  return $flag;
}

# ---------------------------------------------------------------
sub short_name {

  my ($name) = @_;
  my $newname = $name;
  my $largo = length($name);
  if($largo > 25) {
    my $first = substr($name, 0, 11);
    my $last = substr($name, $largo - 11, 11);
    $newname = "$first...$last";
  } 
  return $newname;
}
# ---------------------------------------------------------------
return 1;
# -------------------------------END LIBRERIA--------------------
