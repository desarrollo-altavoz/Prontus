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
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_cgi_04;
use glib_fildir_02;
use glib_html_02;
use lib_edit;
use lib_prontus;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ------

my (%FORM, $LOOP, %COOKIES);

main:{



  my ($plantilla, $pagina, $lista, $aux, $text_file);

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
    &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_functionality_available_administrator'), 'exit=1,ctype=1');
  };

  if ($prontus_varglb::IP_SERVER ne '') { # implica llamada desde ambiente web. # 1.23
    &lib_prontus::test_servers($ENV{'HTTP_REFERER'}); # Autentifica request.  con SERVER_PERM.
  };

  $FORM{'path_file'} = &glib_cgi_04::param('_path_file');
  $FORM{'curr_dir'} = &glib_cgi_04::param('_curr_dir');
  $FORM{'curr_dir'} =~ s/\/$//; # borra ultimo slash si es que viene.

  $FORM{'file_upload'} = &glib_cgi_04::param('file_upload');
  $FORM{'real_file_upload'} = &glib_cgi_04::real_paths('file_upload');
  $FORM{'name_upload'} = &glib_cgi_04::param('name_upload');
  if($FORM{'file_upload'} eq '' || $FORM{'real_file_upload'} eq '') {
    &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_unable_recieved_file'), 'exit=1,ctype=1');
  }

  # Se valida contra el set básico de Prontus
  if(!&lib_edit::is_uploadable($FORM{'real_file_upload'})) {
    my $uploads_permitidos = $prontus_varglb::UPLOADS_PERMITIDOS_ORIG;
    $uploads_permitidos =~ s/,/, /g;
    &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_invalid_extension_review')." <a>".&lib_language::_msg_prontus('_allowed_extensions')."</a>", 'exit=1,ctype=1');
  }

  # Validaciones generales
  $FORM{'full_edit'} = &lib_edit::check_full_edit("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/extra.txt");
  my $full_curr_dir = "$prontus_varglb::DIR_SERVER$FORM{'curr_dir'}";
  my $msgdir = &lib_edit::valida_dirs($full_curr_dir, '', $FORM{'full_edit'});
  if($msgdir) {
    &glib_html_02::print_json_result(0, $msgdir, 'exit=1,ctype=1');
  }

#  print STDERR "file_upload: $FORM{'file_upload'}\n";
#  print STDERR "real_file_upload: $FORM{'real_file_upload'}\n";
#  print STDERR "name_upload: $FORM{'name_upload'}\n";

  # Se revisa si viene o no un nombre para el archivo
  my $name_final = &lib_edit::clearname($FORM{'real_file_upload'});
  if($FORM{'name_upload'} ne '') {

    # Se obtienen las extensiones de ambos archivos
    my $newext = &lib_prontus::get_file_extension($FORM{'real_file_upload'});
    my $ext2 = &lib_prontus::get_file_extension($FORM{'name_upload'});

    # El nombre no debe traer extension
    if($ext2 eq '') {
      $name_final = $FORM{'name_upload'} .'.'. $newext;

    # En el caso que el nombre si traiga la extension, debe ser igual a la extension original
    } elsif($newext eq $ext2) {
      $name_final = $FORM{'name_upload'};

    } else {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_unable_change_file_extension_enter_another_name'), 'exit=1,ctype=1');
    }
  }

  # Se chequea el nombre del archivo
  if(! &lib_edit::check_name($name_final)) {
    &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_name_entered_with_invalid_characters'), 'exit=1,ctype=1');
  }

  # Si comienza con punto, no se puede crear
  if($name_final =~ /^\./) {
    &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_start_restriction_name'), 'exit=1,ctype=1');
  }

  # Se chequea existencia de alguna carpeta
  if (-d $full_curr_dir.$name_final) {
    &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_directory_name_already_exist_enter_another'), 'exit=1,ctype=1');
  };


  # Se mueve el archivo al destino final
  print STDERR "Moviendo $FORM{'file_upload'} a $full_curr_dir/$name_final";
  if(&File::Copy::move($FORM{'file_upload'}, "$full_curr_dir/$name_final")) {
    &lib_prontus::write_log('Upload', 'Editor', "$full_curr_dir/$name_final");
    &glib_html_02::print_json_result(1, &lib_language::_msg_prontus('_file_uploaded_sussessfully_final_name').": $name_final", 'exit=1,ctype=1');
  } else {
    print STDERR "Error al renombrar el archivo: $FORM{'file_upload'}\nEn el destino: $full_curr_dir/$name_final\nDetalles: $!\n";
    &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_failed_to_rename'), 'exit=1,ctype=1');
  }


};


# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
# No registra.
# -------------------------------END SCRIPT----------------------

