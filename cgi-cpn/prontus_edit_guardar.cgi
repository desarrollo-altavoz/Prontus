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
    &glib_html_02::print_json_result(0, "La funcionalidad requerida está disponible sólo para el administrador del sistema.", 'exit=1,ctype=1');
  };

  if ($prontus_varglb::IP_SERVER ne '') { # implica llamada desde ambiente web. # 1.23
    &lib_prontus::test_servers($ENV{'HTTP_REFERER'}); # Autentifica request.  con SERVER_PERM.
  };

  $FORM{'path_file'} = &glib_cgi_04::param('_path_file');
  $FORM{'curr_dir'} = &glib_cgi_04::param('_curr_dir');
  $FORM{'curr_dir'} =~ s/\/$//; # borra ultimo slash si es que viene.

  $FORM{'Sbm_ACCION'} = &glib_cgi_04::param('sbm_accion');
  $FORM{'NOM_NEW_FILE'} = &glib_cgi_04::param('nom_new_file');

  $FORM{'formato_retcarro'} = &glib_cgi_04::param('formato_retcarro');
  $FORM{'formato_retcarro'} =~ s/[^\w]//; # sanitiza # dos | unix

  $FORM{'charset_encoding'} = &glib_cgi_04::param('charset_encoding');
  $FORM{'charset_encoding'} =~ s/[^\w]//; # sanitiza # dos | unix

  # Validaciones generales
  $FORM{'full_edit'} = &lib_edit::check_full_edit("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_DBM/extra.txt");
  my $path_file = $FORM{'NOM_NEW_FILE'};
  $path_file = $FORM{'path_file'} if ($FORM{'Sbm_ACCION'} eq 'Guardar');
  my $msgdir = &lib_edit::valida_dirs("$prontus_varglb::DIR_SERVER$FORM{'curr_dir'}", "$FORM{'curr_dir'}/$path_file", $FORM{'full_edit'});
  if($msgdir) {
    &glib_html_02::print_json_result(0, $msgdir, 'exit=1,ctype=1');
  }

  # Para el caso de guardar archivo existente
  if ($FORM{'Sbm_ACCION'} eq 'Guardar') {
    if ( (!(-f "$prontus_varglb::DIR_SERVER$FORM{'path_file'}")) || ($FORM{'path_file'} =~ /\.\./) )  {
      &glib_html_02::print_json_result(0, "Archivo no válido.", 'exit=1,ctype=1');
    };

    $FORM{'TEXT_FILE'} = &glib_cgi_04::param('text_file'); # viene siempre en formato dos
    if ($FORM{'formato_retcarro'} eq 'unix') {
      $FORM{'TEXT_FILE'} = &lib_prontus::ajusta_crlf($FORM{'TEXT_FILE'});
    };
    if ($FORM{'charset_encoding'} eq 'ansi') {
      utf8::decode($FORM{'TEXT_FILE'});
    };

    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$FORM{'path_file'}", $FORM{'TEXT_FILE'});    
    &lib_prontus::write_log('Guardar', 'Editor', "$prontus_varglb::DIR_SERVER$FORM{'path_file'}");
    
    #my $loc = 'Location: prontus_edit_file.' . $prontus_varglb::EXTENSION_CGI . "?path_conf=$FORM{'path_conf'}&path_file=$FORM{'path_file'}&save_alert=1&curr_dir=$FORM{'curr_dir'}\n\n";
    &glib_html_02::print_json_result(1, "El archivo ha sido guardado", 'exit=1,ctype=1');

  # Para el caso de crear un nuevo archivo
  } elsif ($FORM{'Sbm_ACCION'} eq 'Nuevo') {

    my $name = $FORM{'NOM_NEW_FILE'};
    my $dir = "$prontus_varglb::DIR_SERVER$FORM{'curr_dir'}";
    my $path_new_file = "$dir/$name";

    # Si comienza con punto, no se puede crear
    if($FORM{'NOM_NEW_FILE'} =~ /^\./) {
      &glib_html_02::print_json_result(0, "El nombre no puede comenzar con punto", 'exit=1,ctype=1');
    }

    # Se revisa que el nombre sea valido
    if(!&lib_edit::is_editable($FORM{'NOM_NEW_FILE'})) {
      my $edit_permitidos = $lib_edit::EDIT_PERMITIDOS;
      $edit_permitidos =~ s/,/, /g;
      &glib_html_02::print_json_result(0, "Extensión no válida, sólo se permiten las siguientes extensiones:<br/>$edit_permitidos", 'exit=1,ctype=1');
    }

    # Se chequea el nombre del nuevo archivo
    if (! &lib_edit::check_name($FORM{'NOM_NEW_FILE'})) {
      &glib_html_02::print_json_result(0, "El nombre no es válido", 'exit=1,ctype=1');
    }

    # Se chequea existencia del archivo
    $path_new_file = "$prontus_varglb::DIR_SERVER$FORM{'curr_dir'}/$FORM{'NOM_NEW_FILE'}";
    if (-f $path_new_file) {
      &glib_html_02::print_json_result(0, "El nombre indicado corresponde a un archivo existente, especifique uno distinto por favor.", 'exit=1,ctype=1');

    } elsif (-d $path_new_file) {
      &glib_html_02::print_json_result(0, "El nombre indicado corresponde a un directorio existente, especifique uno distinto por favor.", 'exit=1,ctype=1');
    }

    $path_new_file = "$prontus_varglb::DIR_SERVER$FORM{'curr_dir'}/$FORM{'NOM_NEW_FILE'}";
    &glib_fildir_02::write_file($path_new_file, 'Ingrese el texto del archivo.');

    #$path_new_file =~ s/$prontus_varglb::DIR_SERVER//;
    #my $loc = 'Location: prontus_edit_file.' . $prontus_varglb::EXTENSION_CGI . "?path_conf=$FORM{'path_conf'}&path_file=$path_new_file&refresh_arbol=1&curr_dir=$FORM{'curr_dir'}\n\n";
    &lib_prontus::write_log('Nuevo', 'Editor', $path_new_file);
    &glib_html_02::print_json_result(1, "El archivo ha sido creado", 'exit=1,ctype=1');

  # Para el caso de crear un nuevo directorio
  } elsif ($FORM{'Sbm_ACCION'} eq 'CrearDir') {

    # Se chequea el nombre del nuevo archivo
    if (! &lib_edit::check_name($FORM{'NOM_NEW_FILE'})) {
      &glib_html_02::print_json_result(0, "El nombre no es válido", 'exit=1,ctype=1');
    }

    # Se chequea existencia del archivo
    my $path_new_dir = "$prontus_varglb::DIR_SERVER$FORM{'curr_dir'}/$FORM{'NOM_NEW_FILE'}";
    if (-f $path_new_dir) {
      &glib_html_02::print_json_result(0, "El nombre indicado corresponde a un archivo existente, especifique uno distinto por favor.", 'exit=1,ctype=1');

    } elsif (-d $path_new_dir) {
      &glib_html_02::print_json_result(0, "El nombre indicado corresponde a un directorio existente, especifique uno distinto por favor.", 'exit=1,ctype=1');
    }

    &glib_fildir_02::check_dir($path_new_dir);
    &lib_prontus::write_log('NewDir', 'Editor', $path_new_dir);
    &glib_html_02::print_json_result(1, "El directorio ha sido creado", 'exit=1,ctype=1');

  } else {
    &glib_html_02::print_json_result(0, "Acción no válida: [".$FORM{'Sbm_ACCION'}."]", 'exit=1,ctype=1');
  };
};

# ------------------------------------------------------------------------------
# SUB-RUTINAS.
# -------------
# No registra.
# -------------------------------END SCRIPT-------------------------------------

