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
# Escribir a disco un buffer dado correspondiente a un archivo dado con path completo absoluto.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Al final via location a prontus_edit_file.exe para que se recargue el archivo actualizado.
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Via submit, boton guardar en la pagina de edicion del archivo <dir_publicador>/cpan/core/prontus_edit/prontus_edit_file.html
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ----------------------------
# NO
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
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

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

my (%FORM, $LOOP, %COOKIES);

main:{

  my ($plantilla, $pagina, $lista, $aux, $text_file, $prontus_abs_dir);

  &glib_cgi_04::new();

  $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');
  # Ajusta path_conf para completar path y/o cambiar \ por /
  $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

  # Carga variables de configuracion.
  &lib_prontus::load_config($FORM{'path_conf'});
  $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

  ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
  # Acceso permitido solo para admin
  if (($prontus_varglb::PRONTUS_EDITOR ne 'SI') or $prontus_varglb::USERS_PERFIL ne 'A') {
    &glib_html_02::print_json_result(0, "La funcionalidad requerida está disponible sólo para el administrador del sistema.", 'exit=1,ctype=1');
  };

  if ($prontus_varglb::IP_SERVER ne '') { # implica llamada desde ambiente web. # 1.23
    &lib_prontus::test_servers($ENV{'HTTP_REFERER'}); # Autentifica request.  con SERVER_PERM.
  };

  $FORM{'path_file'} = &glib_cgi_04::param('_path_file');
  $FORM{'curr_dir'} = &glib_cgi_04::param('_curr_dir');
  $FORM{'curr_dir'} =~ s/\/$//; # borra ultimo slash si es que viene.
  $FORM{'type_item'} = &glib_cgi_04::param('type_item');

  $FORM{'full_edit'} = &lib_edit::check_full_edit("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/extra.txt");

  # Seccion para borrar un determinado archivo
  if($FORM{'type_item'} eq 'file') {

    # Validaciones generales
    my $curr_dir_dummy = "$prontus_varglb::DIR_SERVER$FORM{'path_file'}";
    $curr_dir_dummy =~ s/^(.*?)\/[^\/]+$/\1/;
    my $msgdir = &lib_edit::valida_dirs($curr_dir_dummy, $FORM{'path_file'}, $FORM{'full_edit'});
    if($msgdir) {
      &glib_html_02::print_json_result(0, $msgdir, 'exit=1,ctype=1');
    }

    my $file2remove = "$prontus_varglb::DIR_SERVER$FORM{'path_file'}";
    if ( (!(-f $file2remove)) || ($file2remove =~ /\.\./) )  {
      &glib_html_02::print_json_result(0, "Archivo no válido.", 'exit=1,ctype=1');
    };
    print STDERR "Borrando file... $file2remove\n";
    unlink $file2remove;
    &lib_prontus::write_log('Borrar', 'Editor', 'Archivo: '.$FORM{'path_file'});
    &glib_html_02::print_json_result(1, "El archivo ha sido borrado", 'exit=1,ctype=1');

  # Seccion para borrar directorio
  } elsif($FORM{'type_item'} eq 'dir') {

    # Validaciones generales
    my $msgdir = &lib_edit::valida_dirs("$prontus_varglb::DIR_SERVER$FORM{'curr_dir'}", '', $FORM{'full_edit'});
    if($msgdir) {
      &glib_html_02::print_json_result(0, $msgdir, 'exit=1,ctype=1');
    }

    my $dir2remove = "$prontus_varglb::DIR_SERVER$FORM{'curr_dir'}";
    if ( (!(-d $dir2remove)) || ($dir2remove =~ /\.\./) )  {
      &glib_html_02::print_json_result(0, "Directorio no válido.", 'exit=1,ctype=1');
    }
    if(! &lib_edit::is_empty_dir($dir2remove)) {
      &glib_html_02::print_json_result(0, "Directorio indicado no se puede borrar, ya que no está vacío.", 'exit=1,ctype=1');
    }
    print STDERR "Borrando dir... $dir2remove\n";
    if(rmdir $dir2remove) {
      &lib_prontus::write_log('Borrar', 'Editor', 'Directorio: '.$FORM{'curr_dir'});
      &glib_html_02::print_json_result(1, "El directorio ha sido borrado", 'exit=1,ctype=1');
    } else {
      print STDERR "Hubo un error al borrar el directorio: $dir2remove\n$!";
      &glib_html_02::print_json_result(0, "Hubo un error al borrar el directorio", 'exit=1,ctype=1');
    }

  # En el caso que no se haya especificado un tipo
  } else {
    &glib_html_02::print_json_result(0, "Tipo de archivo no especificado", 'exit=1,ctype=1');
  }

};


# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
# No registra.
# -------------------------------END SCRIPT----------------------

