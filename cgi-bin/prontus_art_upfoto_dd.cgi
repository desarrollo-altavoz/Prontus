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
# Variante de la cgi prontus_art_upfoto.cgi para ser utilizada en
# la funcionalidad drag & drop.
#
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# - Desde un FID, via AJAX
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
# No registra.
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------


BEGIN {
    require 'dir_cgi.pm';
    my ($ROOTDIR) = $ENV{'DOCUMENT_ROOT'};  # desde el web
    $ROOTDIR .= '/' . $DIR_CGI_CPAN;
    unshift(@INC,$ROOTDIR); # Para dejar disponibles las librerias

};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use lib_prontus;
use lib_thumb;
use glib_fildir_02;
use strict;
use File::Copy;
use Session;

my (%FORM);

main: {
    &glib_cgi_04::new();
    
    $FORM{'files'} = &glib_cgi_04::param('fileInput');
    $FORM{'prontus_id'} = &glib_cgi_04::param('prontus_id');
    
    $FORM{'prontus_id'} =~ s/[^\w\-]//sg;
    
    &valida_invocacion();

    # Path de cfg de prontus
    my $path_conf = "/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);

    # Carga variables de configuracion de prontus.
    &lib_prontus::load_config($path_conf);
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;
    
    my $nomfile;
    my $ext;
    
    if ($FORM{'files'} =~ /(\/|\\)?([^\/\\]+?)(\.\w+)$/) {
        $nomfile = lc $2;
        $ext = lc $3; # ext con punto
    }
    
    my $relpath = &glib_cgi_04::real_paths('fileInput');

    # Compone path destino de la imagen y realiza garbage
    my $rel_dst_dir = "/$FORM{'prontus_id'}/cpan/procs/uploadify";
    &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$rel_dst_dir");
    &garbage_collector("$prontus_varglb::DIR_SERVER$rel_dst_dir");
    
    my $rel_dst_path = "$rel_dst_dir/$nomfile$ext";
    my $dst_path = "$prontus_varglb::DIR_SERVER$rel_dst_path";
    
    &File::Copy::move($FORM{'files'}, $dst_path);

    my $idFoto = $nomfile . $relpath;
    $idFoto =~ s/[^a-zA-Z0-9]//g;
    my ($msg_size, $wfoto, $hfoto) = &lib_prontus::dev_tam_img($dst_path);

    # Redimencionar imagen si es que supera los limites configurados.
    if ($prontus_varglb::FOTO_MAX_PIXEL ne '') { # si está vacio no se hace nada.
        my ($wmax, $hmax) = split("x", $prontus_varglb::FOTO_MAX_PIXEL);
        if ($wfoto > $wmax || $hfoto > $hmax) {
            my ($wnew, $hnew) = &lib_thumb::calcular_proporcion_img($wfoto, $hfoto, $wmax, $hmax);
            my ($binfoto, $wfoto, $hfoto) = &lib_thumb::make_resize($wnew, $hnew, $dst_path);
            $dst_path =~ s/\.gif$/\.png/i if($dst_path =~ /\.gif$/i);
            &glib_fildir_02::write_file($dst_path, $binfoto) if ($binfoto);
        };
    };
                         
    print "Content-Type: text/html\n\n";
    print "$idFoto,$wfoto,$hfoto,$rel_dst_path,$nomfile,$relpath"; # se devuelve para presntarlo en la pagina y tb. para guardarlo en hiddens
    exit;
};

sub valida_invocacion {
    if ($FORM{'prontus_id'} !~ /^[\w\-]+$/) {
        print STDERR "prontus_id no valido\n";
        print "Content-Type: text/html\n\n";
        print 0;
        exit;
    };
    
    if ($FORM{'files'} eq '') {
        print STDERR "fileInput no valido\n";
        print "Content-Type: text/html\n\n";
        print 0;
        exit;
    };
    
    my $sess_obj = Session->new(
                    'prontus_id'        => $FORM{'prontus_id'},
                    'document_root'     => $prontus_varglb::DIR_SERVER)
                    || die("Error inicializando objeto Session: $Session::ERR\n");
                    
    if ($sess_obj->{id_session} eq '') {
        print STDERR "user no valido[$prontus_varglb::USERS_PERFIL] - prontus_id[$FORM{'prontus_id'}]\n";
        print "Content-Type: text/html\n\n";
        print 0;
        exit;
    };
    
};

sub garbage_collector {
  my $dir = $_[0];
  my(@entries,@stats,$entry);
  # Lee el contenido del directorio.
  if (opendir(DIR, $dir)) {
    @entries = readdir(DIR);
    closedir DIR;
  };
  # Borra cualquier archivo con mas de 2 horas de antiguedad.
  # print $$ . 'time = ' . time . ' ';
  foreach $entry (@entries) {
    if (-f "$dir/$entry") {
      @stats = stat "$dir/$entry";
      # print $stats[10] . ' ';
      if ($stats[10] < (time - 7200)) { # 2 horas.
        unlink "$dir/$entry";
      };
    };
  };
}; # garbage_collector
