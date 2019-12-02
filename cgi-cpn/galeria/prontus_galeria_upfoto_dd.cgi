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
    $pathLibsProntus = $Bin;
    unshift(@INC, $pathLibsProntus);
    $pathLibsProntus =~ s/\/[^\/]+$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

use strict;
# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 512000);

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use lib_prontus;
use lib_thumb;
use glib_fildir_02;
use File::Copy;
use JSON;
use Data::Dumper;

my (%FORM);

main: {
    print "Cache-Control: no-cache, must-revalidate\r\n";
    print "Content-type: application/json\n\n";
    &glib_cgi_04::new();

    $FORM{'files'} = &glib_cgi_04::param('_galeria_fileInputDD');
    $FORM{'prontus_id'} = &glib_cgi_04::param('prontus_id');
    $FORM{'TS'} = &glib_cgi_04::param('ts');

    &valida_invocacion();

    # Path de cfg de prontus
    my $path_conf = "/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    # Carga variables de configuracion de prontus.
    &lib_prontus::load_config($path_conf);

    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=0');
    };

    my $nomfile;
    my $ext;

    if ($FORM{'files'} =~ /(\/|\\)?([^\/\\]+?)(\.\w+)$/) {
        $nomfile = lc $2;
        $ext = lc $3; # ext con punto
    }

    my $relpath = &glib_cgi_04::real_paths('_galeria_fileInputDD');

    # Compone path destino de la imagen y realiza garbage
    my $rel_dst_dir = "/$prontus_varglb::PRONTUS_ID/cpan/procs/galeria_prontus/$FORM{'TS'}";

    &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$rel_dst_dir");
    &garbage_collector("$prontus_varglb::DIR_SERVER$rel_dst_dir");

    my $rel_dst_path = "$rel_dst_dir/$relpath";
    my $dst_path = "$prontus_varglb::DIR_SERVER$rel_dst_path";
    &File::Copy::move($FORM{'files'}, $dst_path);

    my $idFoto = $nomfile . $relpath;
    $idFoto =~ s/[^a-zA-Z0-9]//g;

    my $img_type = &lib_prontus::get_img_type($relpath);

    my ($msg_size, $wfoto, $hfoto) = ('', 0, 0);
    if ($dst_path =~ /[^\/]+\.zip$/i) {
        $rel_dst_path = "/$prontus_varglb::PRONTUS_ID/cpan/core/imag/boto/noimg2.png";
    } else {
        ($msg_size, $wfoto, $hfoto) = &lib_prontus::dev_tam_img($dst_path);
        if ($msg_size) {
            print STDERR "No se pudo obtener las dimensiones de la imagen [$msg_size]\n";
            print '{"status": "0"}';
            exit;
        }

        if (&lib_prontus::can_edit_img($img_type)) {
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
        }
    }

    my %salida = ( 'status' => 1,
                    'data' => {
                        'idFoto' => $idFoto,
                        'wFoto' => $wfoto,
                        'hFoto' => $hfoto,
                        'relPath' => $rel_dst_path,
                        'nomFile' => $nomfile,
                        'realNomFile' => $relpath
                    }
                );
    print &generaJson(\%salida);
};
#---------------------------------------------------------------------------------------------------
sub valida_invocacion {
    if (! &lib_prontus::valida_prontus($FORM{'prontus_id'})) {
        print STDERR "prontus_id no valido\n";
        print '{"status": "0"}';
        exit;
    };

    if ($FORM{'files'} eq '') {
        print STDERR "files no valido\n";
        print '{"status": "0"}';
        exit;
    };
};
#---------------------------------------------------------------------------------------------------
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
#---------------------------------------------------------------------------------------------------
sub generaJson {
    my $hash = $_[0];
    if ($JSON::VERSION =~ /^1\./) {
        my $json = new JSON;
        return $json->objToJson($hash);
    } else {
        return &JSON::to_json($hash);
    }
}
