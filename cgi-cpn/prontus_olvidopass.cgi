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
# Desplegar página "Olvide mi contrasena"
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# 2) Desde la pag. de ingreso al Sistema.
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# No registra.
# ---------------------------------------------------------------
# Prontus 10 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------

use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;

use lib_prontus;
use glib_fildir_02; # Prontus 6.0

use strict;
use File::Copy;



# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM);

main: {
    my ($lnk);

    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga var. globales con los datos del arch. conf.
    &lib_prontus::load_config($FORM{'_path_conf'});   # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    $FORM{'token'} = &glib_cgi_04::param('_token');
    $FORM{'usr'} = &glib_cgi_04::param('_usr');

    if (&lib_prontus::open_dbm_files() ne 'ok') { # Prontus 6.0
    print "Content-Type: text/html\n\n";
    &glib_html_02::print_pag_result("Error","No fue posible abrir archivos de usuarios.");
    exit;
    };

    if ($FORM{'token'} ne '' && $FORM{'usr'} ne '') {
        &validacion_token();
        &show_recordarpass_reset();
    } else {
        &show_recordarpass();
    };

};

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub show_recordarpass {
  my $perfil = $_[0];
  my $buf = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/prontus_olvidopass.html");
  # $buf =~ s/%%REL_PATH_PRONTUS%%/$prontus_varglb::RELDIR_BASE\/$prontus_varglb::PRONTUS_ID/isg;
  $buf =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
  $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;
  $buf =~ s/%%_PATH_CONF%%/$FORM{'_path_conf'}/isg;

  $buf =~ s/<!--olvidopass_reset-->.*?<!--\/olvidopass_reset-->//isg;

  print "Content-Type: text/html\n\n";
  print $buf;
};

sub show_recordarpass_reset {
    my $buf = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/prontus_olvidopass.html");
    
    $buf =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/isg;
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;
    $buf =~ s/%%_PATH_CONF%%/$FORM{'_path_conf'}/isg;
    $buf =~ s/%%_token%%/$FORM{'token'}/isg;
    $buf =~ s/%%_usr%%/$FORM{'usr'}/isg;

    $buf =~ s/<!--olvidopass-->.*?<!--\/olvidopass-->//isg;
    
    print "Content-Type: text/html\n\n";
    print $buf;
};

sub validacion_token {
    my $dirprocuser = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/procs/recordarpass/$FORM{'usr'}.txt";
    #~ print STDERR "dirprocuser[$dirprocuser]\n";
    if (!-f $dirprocuser) {
        print "Content-Type: text/html\n\n";
        &glib_html_02::print_pag_result("Error", "Token invalido o expirado.");
        exit;
    } else {
        my $token = &glib_fildir_02::read_file($dirprocuser);
        $token =~ s/\n//s;
        $token =~ s/\r//s;
        $token =~ s/\t//s;
        $token =~ s/ *//s;
        #~ print STDERR "token[$token]\n";
        if ($FORM{'token'} ne $token) {
            print "Content-Type: text/html\n\n";
            &glib_html_02::print_pag_result("Error", "Token invalido o expirado.");
            exit;
        };
        my $mtime = (stat($dirprocuser))[9];
        my $diffsecs = time - $mtime;
        if ($diffsecs > 3600) { # expiro.
            print "Content-Type: text/html\n\n";
            &glib_html_02::print_pag_result("Error", "Token invalido o expirado.");
            unlink $dirprocuser;
            exit;
        };
        # antiguedad.
    };
};


# -------------------------------END SCRIPT----------------------

