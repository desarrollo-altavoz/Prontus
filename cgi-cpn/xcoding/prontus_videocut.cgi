#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

#
# -----------------------COMENTARIO GLOBAL-----------------------
# ---------------------------------------------------------------
# PROPOSITO
# ---------
# Elimina el inicio o el final de un video.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
# Lee el video lo vuelve a escribir recortado.
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Como cgi, usando metodo GET o POST. Los parametros son:
# video  - Path relativo al video a recortar.
# cut - Tipo de corte: begin elimina el inicio; end elimina el final.
#
# Retorna 'OK' o 'Error: <mensaje de error>';
#
# Ejemplo:
#
# /cgi-cpn/prontus_videocut.cgi?video=prontus_proto/site/artic/20100531/mmedia/tele1.flv&t=60&cut=begin
#
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------
#  No usa plantillas.
#
# ---------------------------------------------------------------
# 1.0.0 - 31/05/2010 - Primera version.
# 1.0.1 - 03/10/2014 - EAG - Se agrega use utf8
# 1.1.0 - 03/06/2015 - EAG - Se agrega generacion de hls despues de cortar

# -------------------------------BEGIN SCRIPT--------------------
BEGIN {
    use FindBin '$Bin';
    my $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/xcoding$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ------------------------
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use lib_prontus;
use glib_cgi_04;
use strict;
use FindBin '$Bin';
use lib_xcoding;
use utf8;

my %FORM;        # Contenido del formulario de invocacion.
my $ARTIC_dirfecha;
my $ARTIC_ts_articulo;
my $ARTIC_path_xml;
my $ARTIC_filename;
my $ARTIC_extension;

main: {
    # Para facilitar el uso mediante AJAX.
    print "Content-type: text/plain\n\n";

    &glib_cgi_04::new();
    &glib_cgi_04::set_formvar('video', \%FORM);
    &glib_cgi_04::set_formvar('t1', \%FORM);
    &glib_cgi_04::set_formvar('t2', \%FORM);
    &glib_cgi_04::set_formvar('prontus_id', \%FORM);

    # Se valida el nombre del prontus
    if (! &lib_prontus::valida_prontus($FORM{'prontus_id'})) {
        print STDERR "Prontus ID inicado no es valido: $FORM{'prontus_id'}\n";
        die("Prontus ID inicado no es valido");
    }

    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        print "Sesion invalida";
        exit;
    };

    # Path conf y load config de prontus
    my $path_conf = "$prontus_varglb::DIR_SERVER/$FORM{'prontus_id'}/cpan/$FORM{'prontus_id'}.cfg";
    $path_conf = &lib_prontus::ajusta_pathconf($path_conf);
    &lib_prontus::load_config($path_conf);  # Prontus 6.0
    $path_conf =~ s/^$prontus_varglb::DIR_SERVER//;

    # se valida el nombre de archivo del video
    if ($FORM{'video'} =~ /(\/site\/\w+\/\d+\/mmedia\/multimedia_video\d+\d{14}\.\w+)$/i) {
        $FORM{'video'} = "/$prontus_varglb::PRONTUS_ID$1";
    } else {
        print "Error: Archivo de video no valido\n";
        exit;
    }

    $FORM{'video'} = "$prontus_varglb::DIR_SERVER$FORM{'video'}";

    $FORM{'t1'} =~ s/[^0-9\.]//g;
    $FORM{'t2'} =~ s/[^0-9\.]//g;

    if (!&load_artic_info()) {
        print STDERR "No se obtener la información del artículo asociado al video: $FORM{'video'}\n";
        return "No se obtener la información del artículo asociado al video.";
    };

    $FORM{'video'} =~ /\/mmedia\/(multimedia_video\d+)\d{14}\.(\w+)$/i;
    my $marca = $1;

    # print $tiempo ."\n";
    my $destino = $FORM{'video'};
    $destino =~ s/(.+)\.(\w+)/$1\.cut\.$2/;
    unlink $destino;

    my $res = &cortar_video($FORM{'video'}, $destino, $FORM{'t1'}, $FORM{'t2'});

    if ($res eq 'OK') {
        # Cortar los videos alternativos si es que existen ...
        my $subres = &cortar_versiones_video($marca, $FORM{'video'});
        $res = $subres if ($subres);
    };

    if ($prontus_varglb::GEN_HLS eq 'SI') {
        # regeneramos el hls para los videos cortados
        my $cmd = "$lib_xcoding::PATHNICE /usr/bin/perl $Bin/prontus_videoxcodehls.cgi $FORM{'video'} $FORM{'prontus_id'}";
        print STDERR "Generando HLS en background [$FORM{'video'}] [$cmd]\n";
        system("$cmd >/dev/null 2>&1 &");
    }

    print $res;
    exit;
};

sub cortar_video  {
    my $origen = $_[0];
    my $destino = $_[1];
    my $t1 = $_[2];
    my $t2 = $_[3];
    my $source = $_[4];
    my $duracion = $t2 - $t1;
    my ($cmd, $res);

    if ($source) {
        $origen = $source;
    };

    $cmd = "$prontus_varglb::DIR_FFMPEG/ffmpeg -ss $t1 -t $duracion -i $origen -y -vcodec copy -acodec copy $destino";
    print STDERR "Cortando video cmd[$cmd]...\n";
    $res = qx/$cmd 2>&1/;
    print STDERR "cmd result: [$res][$?][$!]\n";
    return "Falló corte de video." if ($? != 0);

    $cmd = "$Bin/qtfaststart.cgi $destino";
    print STDERR "Ajustando video cmd[$cmd]...\n";
    $res = qx/$cmd 2>&1/;
    print STDERR ("Falló Ajuste de Mp4 [$!][$res].") if ($? != 0);
    return "Falló Ajuste de Mp4" if ($? != 0);
    # Elimina el archivo de origen si es que el destino se genero ok

    if (-s $destino > 0) {
        unlink $origen;
        rename $destino ,$origen;
        return 'OK';
    } else {
        my $msg_err_usr = 'Error al realizar corte del video, el archivo resultante no pudo ser generado. Los detalles fueron agregados al error log interno de Prontus.';
        print STDERR "$msg_err_usr\nError: el archivo resultante [$destino] no pudo ser generado por ffmpeg\n";
        return $msg_err_usr;
    };
};

# ---------------------------------------------------------------
sub cortar_versiones_video {
    my $marca = $_[0];
    my $origen = $_[1];
    my %formatos;

    print STDERR "Creando versiones [$marca]...\n";
    if ($prontus_varglb::ADVANCED_XCODING eq 'NO') { # transcodificacion basica
        %formatos = &lib_xcoding::get_formatos_v1($marca);
    } elsif ($prontus_varglb::ADVANCED_XCODING eq 'SI') { # transcodificacion avanzada
        %formatos = &lib_xcoding::get_formatos($marca);
    }
    foreach my $key (keys(%formatos)) {
        # print STDERR "key[$key] formato[$formatos{$key}]\n";
        my $flags = $formatos{$key};
        $key =~ /(.*?)\.(.*?)$/i;
        my $code = lc $2;
        $key =~ s/\./$ARTIC_ts_articulo/sg;
        $key = lc $key;
        print STDERR "version[$key]\n";
        my $new_origen = $origen;
        $new_origen =~ s/\/multimedia_video\d+\d{14}\.(\w+)$/\/$key\.mp4/is;
        next if (!-f $new_origen);
        my $new_destino = $origen;
        $new_destino =~ s/(.+)\.(\w+)/$1\.$code\.cut\.$2/;
        # print STDERR "new_destino[$new_destino]\n";

        if (-f $new_destino) {
            unlink $new_destino;
        };

        my $ret = &cortar_video($new_origen, $new_destino, $FORM{'t1'}, $FORM{'t2'});
        if ($ret ne 'OK') {
          # si hay error, hasta aqui nomas llegamos.
          return $ret;
        };
    };
};

sub load_artic_info {
    # Deduce ubicacion del xml del articulo.
    if ($FORM{'video'} =~ /(.+)\/(\d{8})\/mmedia\/(multimedia_video.+?(\d{6}))\.(\w+)$/) {
        $ARTIC_dirfecha = $2;
        $ARTIC_ts_articulo = $2 . $4;
        $ARTIC_path_xml = $1 .'/'. $2 .'/xml/'. $ARTIC_ts_articulo . '.xml';
        $ARTIC_filename = $3;
        $ARTIC_extension = $5;
        return 1;
    } else {
        return 0;
    };
};
