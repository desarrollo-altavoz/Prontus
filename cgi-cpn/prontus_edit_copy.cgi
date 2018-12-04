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

use glib_cgi_04;
use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_edit;
use lib_prontus;
use strict;

use File::Copy;

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
    };

    my $name = $FORM{'NOM_NEW_FILE'};
    my $dir = "$prontus_varglb::DIR_SERVER$FORM{'curr_dir'}";
    my $path_new_file = "$prontus_varglb::DIR_SERVER$FORM{'curr_dir'}/$FORM{'NOM_NEW_FILE'}";
    my $path_orig_file = "$prontus_varglb::DIR_SERVER$FORM{'path_file'}";

    # Si comienza con punto, no se puede crear
    if($FORM{'NOM_NEW_FILE'} =~ /^\./) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_start_restriction_name'), 'exit=1,ctype=1');
    }

    # Se revisa que el nombre sea valido
    if(!&lib_edit::is_editable($FORM{'NOM_NEW_FILE'})) {
        my $edit_permitidos = $lib_edit::EDIT_PERMITIDOS;
        $edit_permitidos =~ s/,/, /g;
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_invalid_extension').":<br/>$edit_permitidos", 'exit=1,ctype=1');
    }

    # Se chequea el nombre del nuevo archivo
    if (! &lib_edit::check_name($FORM{'NOM_NEW_FILE'})) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_invalid_name'), 'exit=1,ctype=1');
    }

    # Se chequea existencia del archivo
    if (-f $path_new_file) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_file_name_already_exist_enter_another'), 'exit=1,ctype=1');

    } elsif (-d $path_new_file) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_directory_name_already_exist_enter_another'), 'exit=1,ctype=1');
    }

    # Se chequea existencia del archivo de origen
    if(! -f $path_orig_file) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_source_file_no_exist'), 'exit=1,ctype=1');
    }
    
    # Se procede con la copia
    print STDERR "copiando $path_orig_file to $path_new_file";
    unless( copy($path_orig_file, $path_new_file)) {
        &glib_html_02::print_json_result(0, &lib_language::_msg_prontus('_failed_copy_file'), 'exit=1,ctype=1');
    }
    
    &lib_prontus::write_log('Copy', 'Editor', "$FORM{'curr_dir'}/$FORM{'NOM_NEW_FILE'} hacia $FORM{'path_file'}");
    
    # Si todo sale bien, se imprime respuesta
    &glib_html_02::print_json_result(1, &lib_language::_msg_prontus('_file_has_been_copied'), 'exit=1,ctype=1');

};

# ------------------------------------------------------------------------------
# SUB-RUTINAS.
# -------------
# No registra.
# -------------------------------END SCRIPT-------------------------------------

