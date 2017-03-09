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
# 3.0.0 - 26/02/2017 - ALD - Adapta a version 2 de la API.
# ---------------------------------------------------------------
# 2do:
# - Mejorar el manejo de errores, para distinguir los errores irrecuperables de los transitorios.

package lib_dropbox;

use strict;
use LWP::UserAgent;
use HTTP::Request::Common;
use Digest::SHA;

our $DEBUG = 0; # 1 activa el debug.

# Token de la aplicacion en Dropbox.
# Para crear una app Dropbox ir aqui: https://www.dropbox.com/developers/apps
# escoger Dropbox API app, files and datastores, limitarla a su propio folder.
# Luego en settings apretar el boton "Generate" para generar un access token.
our $ATOKEN;

# URLs de Dropbox.
our $SPACEUSAGEURL   = 'https://api.dropboxapi.com/2/users/get_space_usage'; # 2.0.0
our $DIRLISTINGURL   = 'https://api.dropboxapi.com/2/files/list_folder'; # 2.0.0 'https://api.dropbox.com/1/metadata/auto';
our $DIRLISTCONTURL  = 'https://api.dropboxapi.com/2/files/list_folder/continue'; # 2.0.0
our $FILEUPLOADURL   = 'https://content.dropboxapi.com/2/files/upload'; # 2.0.0
our $FILEDOWNLOADURL = 'https://content.dropboxapi.com/2/files/download'; # 2.0.0
our $DELETEURL       = 'https://api.dropboxapi.com/2/files/delete'; # 2.0.0 'https://api.dropbox.com/1/fileops/delete';
our $UPLOADSTARTURL  = 'https://content.dropboxapi.com/2/files/upload_session/start';
our $UPLOADAPPENDURL = 'https://content.dropboxapi.com/2/files/upload_session/append_v2';
our $UPLOADFINISHURL = 'https://content.dropboxapi.com/2/files/upload_session/finish';

# Tamano maximo de un archivo para ser subido de una sola vez.
our $MAXFILESIZE = 100000000; # App 100 MB.

# User Agent.
our $UA;

# ------------------------------------------------------------------------#
# Inicializa la interfaz a Dropbox. Setea la token de acceso e inicializa el user-agent.
sub conectar {
    $lib_dropbox::UA = LWP::UserAgent->new();
    $lib_dropbox::UA->default_header('Authorization' => "Bearer $prontus_varglb::DROPBOX_ACCESS_TOKEN" );
    $lib_dropbox::UA->timeout(30);
}; # conectar.

# ------------------------------------------------------------------------#
# Inicializa la interfaz a Dropbox. Setea la token de acceso e inicializa el user-agent.
sub init {
    $lib_dropbox::ATOKEN = $_[0];
    &lib_dropbox::initUA();
}; # init.

# ------------------------------------------------------------------------#
# Inicializa el user agent.
sub initUA {
    $lib_dropbox::UA = LWP::UserAgent->new();
    $lib_dropbox::UA->default_header('Authorization' => "Bearer $lib_dropbox::ATOKEN" );
    $lib_dropbox::UA->timeout(30);
}; # initUA.

# ------------------------------------------------------------------------#
# 2.0.0 Obtiene y entrega el espacio utilizado.
# {"used": 284062049740, "allocation": {".tag": "individual", "allocated": 1101659111424}}
sub getSpaceUsage {
    my $data = &lib_dropbox::postHttp($lib_dropbox::SPACEUSAGEURL);
    if ($data =~ /"used":\s*(\d+)(,|})/s) {
        return $1;
    }else{
        return 0;
    };
}; # getSpaceUsage.

# ------------------------------------------------------------------------#
# Obtiene y entrega informacion sobre la cuenta del usuario.
# Por ahora solo la cuota es de interes.
# 2.0.0 Hace wrp a la funcion getSpaceUsage.
sub getInfo {
    return &getSpaceUsage();
}; # getInfo.

# ------------------------------------------------------------------------#
# 2.0.0 Obtiene el listado de un directorio.
# Entrega un arreglo de strings de la forma 
# <path>\t<es dir>\t<tamano en bytes>\t<client_modified timestamp>\t<hash>
sub getDir {
    my $dir = $_[0];
    my (@lines,$line,@entries);
    my ($path,$isdir,$bytes,$client_modified,$cursor,$content_hash);
    my $jsonData = '{"path": "'.$dir.'","recursive": false,"include_media_info": false,"include_deleted": false,"include_has_explicit_shared_members": false}';
    my $data = &lib_dropbox::postHttpJson($lib_dropbox::DIRLISTINGURL,$jsonData);

    do {
        # Hace un match para obtener el arreglo completo de entries.
        if ($data =~ /"entries": \[(.+)\]/s) {
            # @lines = split(/}/,$1);
            @lines = &lib_dropbox::getObjects($1);
            foreach $line (@lines) {
                ($path,$isdir,$bytes,$client_modified) = ();
                # ".tag": "folder", "name": "site", "path_lower": "/noticias/site", "path_display": "/noticias/site", "id": "id:tOyNRss-k0AAAAAAAAAABg"}
                # ".tag": "file", "name": "release_notes.txt", "path_lower": "/noticias/release_notes.txt", "path_display": "/noticias/release_notes.txt", "id": "id:tOyNRss-k0AAAAAAAAKNQw", "client_modified": "2015-08-01T07:19:14Z", "server_modified": "2015-08-01T07:19:14Z", "rev": "2eb8a33e4ef7a", "size": 852, "content_hash": "df3bdd100f896e415dcc24e653e92566eef9201051d9ee5492dbfe92693039f5"
                if ($line =~ /"path_display": "(.+?)"/s) {
                    $path = $1;
                };
                if ($line =~ /".tag": "([^,}"]+)"/s) {
                    $isdir = ($1 eq 'file') ? 0:1;
                };
                if ($line =~ /"size": ([^,}]+)/s) {
                    $bytes = $1;
                };
                if ($line =~ /"client_modified": "([^,}"]+)"/s) {
                    $client_modified = $1;
                };
                if ($line =~ /"content_hash": "([^,}"]+)"/s) {
                    $content_hash = $1;
                };
                if ($path ne '') { push @entries, "$path\t$isdir\t$bytes\t$client_modified\t$content_hash"; };
            };
        };
        if ($data =~ /"has_more": true/s) {
            # Hay que pedir mas datos.
            if ($data =~ /"cursor": "([^,}"]+)"/s) {
                $cursor = $1;
                $jsonData = '{"cursor": "'.$cursor.'"}';
                $data = &lib_dropbox::postHttpJson($lib_dropbox::DIRLISTCONTURL,$jsonData);
            }else{
                $data = '';
            };
        }else{
            $data = '';
        };
            
    }while ($data ne '');
    
    return @entries;
}; # getDir.

# ------------------------------------------------------------------------#
# 2.0.0 Obtiene el archivo especificado y lo escribe en el path indicado.
# Retorna 1 si tuvo exito y 0 si no. La metadata viene en el header 'Dropbox-Api-Result'.
sub getFile {
    my ($srcPath,$dstPath) = @_;
    my ($req,$jsonArg,$content);
    my $res = 0;
    
    $jsonArg = "{\"path\": \"$srcPath\"}";

    $req = HTTP::Request->new('POST',$lib_dropbox::FILEDOWNLOADURL);
    $req->header( 'Dropbox-API-Arg' => $jsonArg );
    my $response = $lib_dropbox::UA->request($req);

    if ($response->is_success) {
       &lib_dropbox::printDebug("getFile content: [" . $response->headers->as_string . "]\n");
       $content = $response->decoded_content;
    }else {
       &lib_dropbox::printDebug("getFile error: [" . $response->status_line . "][".length($content)."]\n");
       # if ($response->status_line =~ /400/) {
       #     $res = -2;
       # };
    };

    if ($content ne '') {
       &lib_dropbox::writeFile($dstPath,$content);
       $res = 1;
    };
    return $res
}; # getFile.

# ------------------------------------------------------------------------#
# 2.0.0 Sube el archivo especificado en el path indicado.
# El path de destino debe incluir el nombre del archivo de destino.
# Retorna 1 si tuvo exito, 0 si no, -1 si el archivo es rechazado localmente
# y -2 si se recibio un error 400. El error 400 indica que el nombre del
# archivo no le gusto a dropbox.
# Si el archivo excede el tamano $MAXFILESIZE, entonces es subido mediante
# la funcion putLargeFile.
sub putFile {
    my ($srcPath,$dstPath) = @_;
    my ($req,$jsonArg,$json,$content,$client_modified);
    my $res = 0;
    
    if ( -s $srcPath > $lib_dropbox::MAXFILESIZE) {
        # Si el archivo excede el tamano $MAXFILESIZE, entonces 
        # es subido mediante la funcion putLargeFile.
        $res = &lib_dropbox::putLargeFile($srcPath,$dstPath);
    }else{
        # No permite archivos con caracteres extranos. Asi nunca habra problemas con el parseo del JSON.
        if ($dstPath !~ /^[_ 0-9a-zA-Z\.\-\/]+$/) {
            return -1;
        };
        $content = &lib_dropbox::readFile($srcPath);
        $client_modified = &epochToIso8601(time);
        $jsonArg = "{\"path\": \"$dstPath\",\"mode\": \"overwrite\",\"autorename\": true,\"client_modified\": \"$client_modified\",\"mute\": false}";
        $req = HTTP::Request->new('POST',$lib_dropbox::FILEUPLOADURL);
        $req->content_type('application/octet-stream');
        $req->header( 'Dropbox-API-Arg' => $jsonArg );
        $req->content($content);
        my $response = $lib_dropbox::UA->request($req);
        if ($response->is_success) {
            &lib_dropbox::printDebug("putFile content: [" . $response->decoded_content . "]\n");
            # {"name": "avatar.jpg", "path_lower": "/noticias/avatar.jpg", "path_display": "/noticias/avatar.jpg", 
            #  "id": "id:tOyNRss-k0AAAAAAAApLzQ", "client_modified": "2017-02-25T21:59:43Z", 
            #  "server_modified": "2017-02-25T21:59:43Z", "rev": "e347c33e4ef7a", "size": 159552, 
            #  "content_hash": "89ce72c2460a60217b2e53da3979fa9c1ea119a40c3f0b0e4a12cae55f2dfc15"}
            $json = $response->decoded_content;
            if ($json =~ /"size": ([^,}]+)/) {
                if (length($content) == $1) {
                    $res = 1;
                };
            };
        }else {
            &lib_dropbox::printDebug("putFile error: [" . $response->status_line . "][".length($content)."]\n");
            # Codigos de error que no ameritan un reintento.
            if ($response->status_line =~ /400/) {
                $res = -2;
            };
        };
    };
    
    return $res
}; # putFile.

# ------------------------------------------------------------------------#
# 2.0.0 Sube el archivo especificado en el path indicado, en pedazos de a 100 MB.
# El path de destino debe incluir el nombre del archivo de destino.
# Retorna 1 si tuvo exito, 0 si no, -1 si el archivo es rechazado localmente
# y -2 si se recibio un error 400.
# Si el resultado es 0, se deberia reintentar hasta lograrlo.
sub putLargeFile {
    my ($srcPath,$dstPath) = @_;
    my ($req,$jsonArg,$json,$content,$index,$bytesRead,$response,$sessionId,$client_modified);
    my $chunkSize = $lib_dropbox::MAXFILESIZE;
    my $res = 0;
    # No permite archivos con caracteres extranos. Asi nunca habra problemas con el parseo del JSON.
    if ($dstPath !~ /^[_ 0-9a-zA-Z\.\-\/]+$/) {
        return -1;
    };
    
    # Abre el archivo y lo lee en trozos de a $chunkSize.
    open IN,"<$srcPath";
    $index = 0;
    $bytesRead = read(IN, $content, $chunkSize);
    if ($bytesRead > 0) {
        # Inicia la sesion de upload.
        $jsonArg = "{\"close\": false}";
        $req = HTTP::Request->new('POST',$lib_dropbox::UPLOADSTARTURL);
        $req->content_type('application/octet-stream');
        $req->header( 'Dropbox-API-Arg' => $jsonArg );
        $req->content($content);
        $response = $lib_dropbox::UA->request($req);
        if ($response->is_success) {
            $json = $response->decoded_content;
            &lib_dropbox::printDebug("putLargeFile content 1: [$json][$bytesRead][$index]\n");
            if ($json =~ /"session_id": "([^,}"]+)"/) {
                $sessionId = $1;
                # Con el id de sesion se continua la carga del archivo.
                do {
                    # $index += $chunkSize;
                    # Normalmente $bytesRead == $chunkSize, excepto al final.
                    $index += $bytesRead;
                    seek(IN, $index, 0);
                    $bytesRead = read(IN, $content, $chunkSize);
                    if ($bytesRead == $chunkSize) {
                        $jsonArg = "{\"cursor\": {\"session_id\": \"$sessionId\",\"offset\": $index},\"close\": false}";
                        $req = HTTP::Request->new('POST',$lib_dropbox::UPLOADAPPENDURL);
                        $req->content_type('application/octet-stream');
                        $req->header( 'Dropbox-API-Arg' => $jsonArg );
                        $req->content($content);
                        $response = $lib_dropbox::UA->request($req);
                        &lib_dropbox::printDebug("putLargeFile content 2: [" . $response->decoded_content . "][$bytesRead][$index][$sessionId]\n");
                        if (! $response->is_success) {
                            # Si el upload falla, sale indicando error -2 para no reintentar.
                            # (Falta un analisis mas exhaustivo del error aqui).
                            close IN;
                            return -2;
                        };
                    };
                }while ($bytesRead == $chunkSize);
                # Cierra la sesion de upload.
                $client_modified = &epochToIso8601(time);
                $jsonArg = "{\"cursor\": {\"session_id\": \"$sessionId\",\"offset\": $index},\"commit\": {\"path\": \"$dstPath\",\"mode\": \"overwrite\",\"autorename\": true,\"client_modified\": \"$client_modified\",\"mute\": false}}";
                $req = HTTP::Request->new('POST',$lib_dropbox::UPLOADFINISHURL);
                $req->content_type('application/octet-stream');
                $req->header( 'Dropbox-API-Arg' => $jsonArg );
                $req->content($content);
                $response = $lib_dropbox::UA->request($req);
                &lib_dropbox::printDebug("putLargeFile content 3: [" . $response->decoded_content . "][$bytesRead][$index][$sessionId]\n");
                if ($response->decoded_content =~ /"path_display": "$dstPath"/s) {
                    $res = 1;
                };
            };
        }else {
            # Codigos de error que no ameritan un reintento (resultado no es 1, pero tampoco es 0).
            if ($response->status_line =~ /400/) {
                $res = -2;
            };
        };
    };
    close IN;
    return $res
}; # putLargeFile.

# ------------------------------------------------------------------------#
# 2.0.0 Elimina el archivo o directorio especificado en el path indicado.
# Retorna 1 si tuvo exito y 0 si no.
# Ojo que Dropbox en realidad nunca elimina los archivos; los deja en el trash.
# Para borrar en forma permanente hay que hacerlo en la GUI web.
sub deletePath {
    my $path = $_[0];
    my $res = 0;
    my $jsonData = "{\"path\": \"$path\"}";
    my $response = &lib_dropbox::postHttpJson($lib_dropbox::DELETEURL,$jsonData);
    if ($response =~ /"path_display": "$path"/s) {
        $res = 1;
    };
    return $res;
}; # deletePath.

# ------------------------------------------------------------------------#
# Hace un POST sin parametros.
# Retorna la respuesta si tuvo exito y '' si no.
sub postHttp {
    my ($url) = $_[0];
    my $req = HTTP::Request->new( 'POST', $url );
    my $response = $lib_dropbox::UA->request( $req );
    if ($response->is_success) {
       &lib_dropbox::printDebug("postHttp content: [" . $response->decoded_content . "]\n");
       return $response->decoded_content;  # or whatever
    }else {
       &lib_dropbox::printDebug("postHttp error: [" . $response->status_line . "]\n");
       return '';
    };
}; # postHttp.

# ------------------------------------------------------------------------#
# Hace un POST. Los parametros son el URL y \%formulario.
# Retorna la respuesta si tuvo exito y '' si no.
sub postHttpForm {
    my ($url,$form) = @_;
    my $response = $lib_dropbox::UA->post($url,$form);
    if ($response->is_success) {
       &lib_dropbox::printDebug("postHttp content: [" . $response->decoded_content . "]\n");
       return $response->decoded_content;  # or whatever
    }else {
       &lib_dropbox::printDebug("postHttp error: [" . $response->status_line . "]\n");
       return '';
    };
}; # postHttpForm.

# ------------------------------------------------------------------------#
# Hace un POST de json.
# Retorna la respuesta si tuvo exito y '' si no.
sub postHttpJson {
    my ($url,$json) = @_;
    my $req = HTTP::Request->new('POST',$url);
    $req->content_type('application/json');
    $req->content($json);
    my $response = $lib_dropbox::UA->request($req);
    if ($response->is_success) {
       &lib_dropbox::printDebug("postHttpContent content: [" . $response->decoded_content . "]\n");
       return $response->decoded_content;  # or whatever
    }else {
       &lib_dropbox::printDebug("postHttpContent error: [" . $response->status_line . "]\n");
       return '';
    };
}; # postHttpJson.

# ------------------------------------------------------------------------#
# Obtiene datos via GET.
# Retorna la respuesta si tuvo exito y '' si no.
sub getHttp {
    my $url = $_[0];
    my $response = $lib_dropbox::UA->get($url);
    if ($response->is_success) {
       &lib_dropbox::printDebug("getHttp $url content: [" . $response->decoded_content . "]\n");
       return $response->decoded_content;  # or whatever
    }else {
       &lib_dropbox::printDebug("getHttp $url error: [" . $response->status_line . "]\n");
       return '';
    };
}; # getHttp.

# -------------------------------------------------------------------------#
# Lee un archivo por completo. Si el archivo no existe retorna ''.
sub readFile {
    my($archivo) = $_[0];
    my($buffer) = '';
    if (-e $archivo) {
        open (ARCHIVO,"<$archivo");
        binmode ARCHIVO;
        read ARCHIVO,$buffer,-s $archivo;
        close ARCHIVO;
    };
    return $buffer;
}; # readFile

# ------------------------------------------------------------------------#
# Escribe un archivo. Si no puede retorna un mensaje de error.
sub writeFile {
    my($archivo,$buffer) = ($_[0],$_[1]);
    my($dir);
    if (open (ARCHIVO,">$archivo") ) {
        binmode ARCHIVO;
        print ARCHIVO $buffer; # Escribe buffer completo
        close ARCHIVO;
        return '';
    }else{
        return "Fail writing file $archivo $!";
    };
}; # writeFile

# ------------------------------------------------------------------------#
# Obtiene los objetos de primer nivel de un arreglo json.
# Para eso matches los cierres de } y corta el string en ellos.
sub getObjects() {
    my $json = $_[0];
    my $i = 0;
    my $largo = length $json;
    my @entries;
    my ($car,$depth,$lastIndex);
    $depth = 0;
    $lastIndex = 0;
    while ($i < $largo) {
        $car = substr($json, $i, 1);
        if ($car eq '{') {
            $depth++;
            if ($depth == 1) { $lastIndex = $i };
        }elsif ($car eq '}') {
            $depth--;
        };
        if (($car eq '}') && ($depth == 0)) {
            # Agrega el trozo de string como elemento del arreglo.
            push @entries, substr($json,$lastIndex,($i - $lastIndex + 1));
        };
        $i++;
    };
    return @entries;
}; # getObjects

# ----------------------------------------------------------------------------- #
# Transforma un epoch al formato ISO 8601, UTC: "%Y-%m-%dT%H:%M:%SZ"
sub epochToIso8601 {
    my $epoch = $_[0];
    my @utc = gmtime($epoch);
    my $fechahora = sprintf('%04d-%02d-%02dT%02d:%02d:%02dZ',(1900 + $utc[5]),(1 + $utc[4]),$utc[3],$utc[2],$utc[1],$utc[0]);
}; # epochToIso8601

# ----------------------------------------------------------------------------- #
# Calcula un hash de contenido al estilo Dropbox.
sub computeContentHash {
    my $file = $_[0];
    my $chunkSize = 4194304;
    my ($i,$index,$bytesRead,$computedHash,$content);
    my ($hexHash);
    open IN, "<$file";
    $index = 0;
    $bytesRead = read(IN, $content, $chunkSize);
    while ($bytesRead > 0) {
        $computedHash .= Digest::SHA::sha256($content);
        $index += $bytesRead;
        seek(IN, $index, 0);
        $bytesRead = read(IN, $content, $chunkSize);
    };
    $computedHash = Digest::SHA::sha256($computedHash);
    for ($i=0;$i<length($computedHash);$i++) {
        # $hexHash .= sprintf('%X ',substr($computedHash,$i,1));
        $hexHash .= unpack('H2',substr($computedHash,$i,1));
    };
    return $hexHash;
}; # computeContentHash

# ------------------------------------------------------------------------#
# Hace print siempre que el flag debug este activo.
sub printDebug {
    if ($lib_dropbox::DEBUG) { print $_[0]; };
}; # printDebug.

return 1;
