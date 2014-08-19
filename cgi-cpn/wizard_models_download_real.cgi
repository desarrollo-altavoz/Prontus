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
# CGI encargada de obtener de hacer la descarga.
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 14/08/2014 - JOR - Primera Version.
#
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

use POSIX;

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200, 'wizard_error_log');

use glib_fildir_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_cgi_04;
use strict;
use lib_prontus;
use Digest::MD5 qw(md5_hex);

use wizard_lib;
# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%PRONTUS);
my ($INF_DIR) = "$prontus_varglb::DIR_SERVER/wizard_prontus/_data";
my ($INF_FILE) = "$INF_DIR/inf.txt";
my ($STATUS_FILE) = "$INF_DIR/progress.txt";

my ($TOTAL_DOWNLOADED, $PROGRESS, $REMOTE_FILE_SIZE) = 0;

main:{
    my $modelid = $ARGV[0];

    # En el caso que no exista el directorio de los modelos
    &glib_fildir_02::check_dir("$prontus_varglb::DIR_SERVER$wizard_lib::MODELS_DIR");

    # Se descarga el modelo
    my $mensaje = &descarga_modelo($modelid);

    if ($mensaje) {
        &glib_fildir_02::write_file($STATUS_FILE, $mensaje);
    }

    print STDERR "mensaje[$mensaje]\n";

};

# --------------------------------------------------------------------------------------------------
sub descarga_modelo {

    my $modelid = shift;
    my $dirmodel = "$prontus_varglb::DIR_SERVER$wizard_lib::MODELS_DIR/$modelid";

    # Descarga tgz
    my $url = $wizard_lib::URL_MODELS . '/' . $modelid . '/' . $modelid . '.tgz';

    $REMOTE_FILE_SIZE = &get_remote_file_size($url);

    print STDERR "REMOTE_FILE_SIZE[$REMOTE_FILE_SIZE]\n";

    if (!$REMOTE_FILE_SIZE) {
        return "Error al descargar modelo .tgz [$url]. El tamaño es 0.";
    };

    my ($tgz_content, $msg_err) = &get_url($url, 30);
    if ($msg_err) {
        if ($msg_err =~ /^404 /) {
            return "Error al descargar modelo .tgz, 404 - no se encuentra el archivo[$url]";
        } else {
            return "Error al descargar modelo .tgz [$url]: $msg_err";
        };

    } else {

        # Si ok el tgz, descarga md5
        my $url_md5 = $url . ".md5";
        my ($md5_remoto, $msg_err_md5) = &get_url($url_md5, 10);
        if ($msg_err_md5) {
            if ($msg_err_md5 =~ /^404 /) {
                return "Error al descargar modelo md5, 404 - no se encuentra el archivo[$url_md5]";
            } else {
                return "Error al descargar modelo md5 [$url_md5]: $msg_err_md5";
            };

        }
        if ($md5_remoto =~ /([a-z0-9]{32})/) {
            $md5_remoto = $1;
        } else {
            return "Error al descargar release md5 [$url_md5]: No contiene un string md5 valido, contiene[$md5_remoto]";
        };

        # Si descargo ok el md5, verificar el tgz con este
        my $md5_local = md5_hex($tgz_content);
        if ($md5_local ne $md5_remoto) {
            return "Error al descargar modelo [$url]: md5 no coincide\nlocal [$md5_local]\nremoto[$md5_remoto]\nEl archivo no se pudo descargar correctamente.";

        }

        # Si verificacion ok, guardar tgz y descomprimir en ubicacion de destino
        my $dirdownload = "$prontus_varglb::DIR_SERVER$wizard_lib::DOWNLOAD_DIR";
        return "No se pudo crear el directorio de descarga" if (! &glib_fildir_02::check_dir($dirdownload));
        my $path_local_tgz = "$dirdownload/download" . $modelid . '.tgz';
        &glib_fildir_02::write_file($path_local_tgz, $tgz_content);
        if (! (-s $path_local_tgz) || ! (-f $path_local_tgz)) {
            return "Error al descargar release .tgz [$url]: $msg_err";
        };
        # guardar el .md5 tb, por siaca
        &glib_fildir_02::write_file("$path_local_tgz.md5", $md5_remoto);

        # Creamos un directorio al azar
        my $ramdomdir = int(rand(1000000));
        $ramdomdir = &glib_str_02::format_n($ramdomdir, 6);
        return "No se pudo crear el directorio de descarga" if (! &glib_fildir_02::check_dir("$dirdownload/$ramdomdir"));

        # descomprimir en el mismo dir, el .tgz
        system("tar xzf $path_local_tgz -C $dirdownload/$ramdomdir");
        if ($? != 0) {
            &glib_fildir_02::borra_dir("$dirdownload/$ramdomdir");
            return "Error al descomprimir release .tgz[$path_local_tgz] en dir[$dirdownload/$ramdomdir]: Error[$!]";
        };
        print STDERR "Modelo descomprimido en: $dirdownload/$ramdomdir\n";

        # Se copia y se borra lo descargado
        my $dir_destino = "$prontus_varglb::DIR_SERVER$wizard_lib::MODELS_DIR";
        &glib_fildir_02::copy_tree($dirdownload, $ramdomdir, $dir_destino, $modelid);

        # Descarga el resto de los componentes
        my $resp = &wizard_lib::descarga_componente($modelid, "$modelid.cfg");
        return $resp if($resp);
        $resp = &wizard_lib::descarga_componente($modelid, "$modelid-thumb.png");
        return $resp if($resp);
        &wizard_lib::descarga_componente($modelid, "$modelid-big.png");
        return $resp if($resp);
        &wizard_lib::descarga_componente($modelid, "release_notes.txt");
        return $resp if($resp);

        &glib_fildir_02::borra_dir("$dirdownload/$ramdomdir");
        unlink("$path_local_tgz");
        unlink("$path_local_tgz.md5");

        #~ &glib_fildir_02::borra_dir("$dirdownload/$ramdomdir");
        # En este punto el modelo ya fue descargado y descomprimido

    };
    return '';

};

sub get_url {
    use LWP::UserAgent;
    use HTTP::Response;

    my ($url) = $_[0];
    my ($espera_segs) = $_[1];
    my ($type) = $_[2];

    $espera_segs = 30 if ($espera_segs eq '');
    $type = 'GET' if ($type eq '');

    return '' if (($url eq '') or ($url !~ /^https?/i));
    my ($ua) = new LWP::UserAgent;
    $ua->timeout($espera_segs); # segs # default es 180
    $ua->agent('Mozilla/5.0 (Windows; U; Windows NT 5.1; es-ES; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'); # default es "libwww-perl/#.##"
    $ua->add_handler('response_data' => \&callback);

    my ($request) = new HTTP::Request($type, $url) || return ('', $!);
    my ($response) = $ua->request($request) || return ('', $!);

    if ($response->is_success) {
        return ($response->content, '');
    } else {
        return ('', $response->status_line);
    };

};

sub callback {
    my ($response, $ua, $h, $data) = @_;
    $TOTAL_DOWNLOADED += length $data;
    #print STDERR "TOTAL_DOWNLOADED[$TOTAL_DOWNLOADED]\n";

    $PROGRESS = ($TOTAL_DOWNLOADED * 100) / $REMOTE_FILE_SIZE;
    $PROGRESS = ceil($PROGRESS);
    $PROGRESS = 100 if ($PROGRESS > 100);

    #print STDERR "PROGRESS[$PROGRESS]\n";

    &glib_fildir_02::write_file($STATUS_FILE, $PROGRESS);

    return 1;
};

sub get_remote_file_size {
    my $url = shift;
    my $ua = new LWP::UserAgent;
    $ua->agent("Mozilla/5.0");
    my $req = new HTTP::Request 'HEAD' => $url;
    $req->header('Accept' => 'text/html');
    my $res = $ua->request($req);

    if ($res->is_success) {
        my $headers = $res->headers;
        my $length = $headers->content_length;
        return $length;
    } else {
        return 0;
    }

};
