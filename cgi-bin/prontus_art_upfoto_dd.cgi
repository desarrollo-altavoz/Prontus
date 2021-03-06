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
    use FindBin '$Bin';
    $pathLibs = $Bin;
    unshift(@INC, $pathLibs);
    do 'dir_cgi.pm';
    $pathLibs =~ s/\/[^\/]+$/\/$DIR_CGI_CPAN/;
    unshift(@INC,$pathLibs);
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

    $FORM{'files'} = &glib_cgi_04::param('fileInputDD');
    if (!$FORM{'files'}) {
        $FORM{'files'} = &glib_cgi_04::param('fileInputSelect');
    }
    $FORM{'prontus_id'} = &glib_cgi_04::param('prontus_id');
    # $FORM{'prontus_id'} =~ s/[^\w\-]//sg; No es necesario se valida dentro de valida_invocacion()

    &valida_invocacion();

    # Path de cfg de prontus
    my $path_conf = "/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);

    # Carga variables de configuracion de prontus.
    &lib_prontus::load_config($path_conf);

    &valida_sesion();

    my $nomfile;
    my $ext;

    if ($FORM{'files'} =~ /(\/|\\)?([^\/\\]+?)(\.\w+)$/) {
        $nomfile = lc $2;
        $ext = lc $3; # ext con punto
    }

    my $relpath = &glib_cgi_04::real_paths('fileInputDD');

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
    if($msg_size) {
        print STDERR "No se pudo obtener las dimensiones de la imagen [$msg_size]\n";
        print "Content-Type: text/html\n\n";
        print 0;
        exit;
    }
    # Redimensionar imagen si es que supera los limites configurados.
    if ($prontus_varglb::FOTO_MAX_PIXEL ne '') { # si está vacio se reduce calidad del jpg, si corresponde.
        my ($wmax, $hmax) = split("x", $prontus_varglb::FOTO_MAX_PIXEL);
        if ($wfoto > $wmax || $hfoto > $hmax) {
            my ($wnew, $hnew) = &lib_thumb::calcular_proporcion_img($wfoto, $hfoto, $wmax, $hmax);
            my ($binfoto, $wfoto, $hfoto) = &lib_thumb::make_resize($wnew, $hnew, $dst_path);
            $dst_path =~ s/\.gif$/\.png/i if($dst_path =~ /\.gif$/i);
            &lib_thumb::write_image($dst_path, $binfoto) if ($binfoto);
        };
    } else {
        my $tipo = &lib_thumb::get_imag_extension($dst_path);
        # Si es un JPEG, y está habilitada la reducción de calidad de las imágenes, lo guardamos con la calidad especificada en prontus_varglb::NIVEL_OPTIMIZACION_JPG.
        if ($tipo eq 'jpg' && $prontus_varglb::REDUCIR_CALIDAD_JPEGS eq 'SI') {
            #print STDERR "Reduciendo calidad a $prontus_varglb::NIVEL_OPTIMIZACION_JPG\n";
            my ($ancho, $alto, $ratio) = &lib_thumb::get_propiedades($dst_path);
            my ($binfoto, $wfoto, $hfoto) = &lib_thumb::make_resize($ancho, $alto, $dst_path);
            &lib_thumb::write_image($dst_path, $binfoto) if ($binfoto);
        }
    };

    print "Content-Type: text/html\n\n";
    print "$idFoto,$wfoto,$hfoto,$rel_dst_path,$nomfile,$relpath"; # se devuelve para presntarlo en la pagina y tb. para guardarlo en hiddens
    exit;
};


sub valida_invocacion {

    if (! &lib_prontus::valida_prontus($FORM{'prontus_id'})) {
        print STDERR "prontus_id no valido\n";
        print "Content-Type: text/html\n\n";
        print 0;
        exit;
    };

    if ($FORM{'files'} eq '') {
        print STDERR "fileInputDD no valido\n";
        print "Content-Type: text/html\n\n";
        print 0;
        exit;
    };
}

sub valida_sesion {
    my $sess_obj = Session->new(
                    'prontus_id'        => $prontus_varglb::PRONTUS_SSO_MANAGER_ID,
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
