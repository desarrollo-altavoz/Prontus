#!/usr/bin/perl
# --------------------------------------------------------------
# Libreria Dropbox.
# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0.0 - 11/10/2014 - ALD - Primera version.
# 1.0.1 - 31/10/2014 - ALD - Corrige algunos bugs.
# 2.0.0 - 11/11/2014 - JOR - Se integra como librería a Prontus.
# ---------------------------------------------------------------

package lib_dropbox;

use strict;
use LWP::UserAgent;
use HTTP::Request::Common;

our $DEBUG = 0; # 1 activa el debug.

# Token de la aplicacion en Dropbox.
# Para crear una app Dropbox ir aqui: https://www.dropbox.com/developers/apps
# escoger Dropbox API app, files and datastores, limitarla a su propio folder.
# Luego en settings apretar el boton "Generate" para generar un access token.
our $ATOKEN;

# URLs de Dropbox.
our $ACCOUNTINFOURL = 'https://api.dropbox.com/1/account/info';
our $DIRLISTINGURL  = 'https://api.dropbox.com/1/metadata/auto';
our $FILEPUTURL     = 'https://api-content.dropbox.com/1/files_put/auto';
our $FILEGETURL     = 'https://api-content.dropbox.com/1/files/auto';
our $DELETEURL      = 'https://api.dropbox.com/1/fileops/delete';

# User Agent.
our $UA;

# ------------------------------------------------------------------------#
# Inicializa la interfaz a Dropbox. Setea la token de acceso e inicializa el user-agent.
sub conectar {
    $lib_dropbox::UA = LWP::UserAgent->new();
    $lib_dropbox::UA->default_header('Authorization' => "Bearer $prontus_varglb::DROPBOX_ACCESS_TOKEN" );
    $lib_dropbox::UA->timeout(30);
}; # init.


# ------------------------------------------------------------------------#
# Obtiene y entrega informacion sobre la cuenta del usuario.
# Por ahora solo la cuota es de interes.
sub get_info {
    my $data = &lib_dropbox::get_http($lib_dropbox::ACCOUNTINFOURL);
    if ($data =~ /"quota": (\d+)(,|})/s) {
        return $1;
    }else{
        return 0;
    };
}; # get_info.

# ------------------------------------------------------------------------#
# Obtiene el listado de un directorio.
# Entrega un arreglo con string de la forma <path>\t<es dir>\t<tamano en bytes>
sub get_dir_filelist {
    my (@lines, $line, @entries);
    my ($path, $isdir, $bytes);
    my $dir = $_[0];
    my $data = &lib_dropbox::get_http("$lib_dropbox::DIRLISTINGURL$dir");
    if ($data =~ /"contents": \[(.+)\]/s) {
        @lines = split(/}/, $1);
        foreach $line (@lines) {
            ($path, $isdir, $bytes) = ();

            if ($line =~ /"path": "(.+?)"/s) {
                $path = $1;
            };

            if ($line =~ /"is_dir": ([^,}]+)/s) {
                $isdir = ($1 eq 'false') ? 0 : 1;
            };

            if ($line =~ /"bytes": ([^,}]+)/s) {
                $bytes = $1;
            };

            if ($path ne '') { push @entries, "$path\t$isdir\t$bytes"; };
        };
    };

    return @entries;
}; # getDir.

# ------------------------------------------------------------------------#
# Obtiene el archivo especificado y lo escribe en el path indicado.
# Retorna 1 si tuvo exito y 0 si no.
sub get_file {
    my ($srcPath,$dstPath) = @_;
    my $json;
    my $res = 0;
    my $content = &lib_dropbox::get_http("$lib_dropbox::FILEGETURL$srcPath");
    if ($content ne '') {
       &glib_fildir_02::write_file($dstPath, $content);
       $res = 1;
    };
    return $res
}; # get_file.

# ------------------------------------------------------------------------#
# Sube el archivo especificado en el path indicado.
# El path de destino debe incluir el nombre del archivo de destino.
# Retorna 1 si tuvo exito y 0 si no.
sub upload_file {
    my ($srcPath,$dstPath) = @_;
    my $json;
    my $res = 0;
    my $content = &glib_fildir_02::read_file($srcPath);
    # No permite archivos con caracteres extranos. Asi nunca habra problemas con el parseo del JSON.
    if ($dstPath !~ /^[_ 0-9a-zA-Z\.\-\/]+$/) {
        return 0;
    };

    my $response = $lib_dropbox::UA->request(PUT "$lib_dropbox::FILEPUTURL$dstPath",Content => $content);
    if ($response->is_success) {
       &lib_dropbox::print_debug("putFile content: [" . $response->decoded_content . "]\n");
       $json = $response->decoded_content;
       if ($json =~ /"bytes": ([^,}]+)/) {
           if (length($content) == $1) {
               $res = 1;
           };
       };
    }else {
       &lib_dropbox::print_debug("putFile error: [" . $response->status_line . "]\n");
    };
    return ($res, $response->status_line);
}; # putFile.

# ------------------------------------------------------------------------#
# Elimina el archivo o directorio especificado en el path indicado.
# Retorna 1 si tuvo exito y 0 si no.
sub delete_path {
    my ($path) = $_[0];
    my (%form,$response);
    my $res = 0;
    $form{'root'} = 'auto';
    $form{'path'} = $path;
    $response = &lib_dropbox::post_http($lib_dropbox::DELETEURL,\%form);
    if ($response =~ /"is_deleted": true/s) {
        $res = 1;
    };
    return $res;
}; # delete_path.

# ------------------------------------------------------------------------#
# Hace un POST. Los parametros son el URL y \%formulario.
# Retorna la respuesta si tuvo exito y '' si no.
sub post_http {
    my ($url,$form) = @_;
    my $response = $lib_dropbox::UA->post($url,$form);
    if ($response->is_success) {
       &lib_dropbox::print_debug("postHttp content: [" . $response->decoded_content . "]\n");
       return $response->decoded_content;  # or whatever
    }else {
       &lib_dropbox::print_debug("postHttp error: [" . $response->status_line . "]\n");
       return '';
    };
}; # post_http.


# ------------------------------------------------------------------------#
# Obtiene datos via GET.
# Retorna la respuesta si tuvo exito y '' si no.
sub get_http {
    my $url = $_[0];
    my $response = $lib_dropbox::UA->get($url);
    if ($response->is_success) {
       &lib_dropbox::print_debug("getHttp $url content: [" . $response->decoded_content . "]\n");
       return $response->decoded_content;  # or whatever
    }else {
       &lib_dropbox::print_debug("getHttp $url error: [" . $response->status_line . "]\n");
       return '';
    };
}; # get_http.

# ------------------------------------------------------------------------#
# Hace print siempre que el flag debug este activo.
sub print_debug {
    if ($lib_dropbox::DEBUG) { print STDERR $_[0]; };
}; # print_debug.


return 1;