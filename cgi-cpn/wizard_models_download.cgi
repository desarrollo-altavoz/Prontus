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
# CGI encargada de descargar/actualizar un modelo Local
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 01 - 11/2005 - YCH - Primera Version.
#
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

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


main:{

    &glib_cgi_04::new();
    
    my $modelid = &glib_cgi_04::param('modelid');

    # Se chequea si existe el modelo online
    my $nodisponible = 0;
    my $urlCFG = "$wizard_lib::URL_MODELS/$modelid/$modelid.cfg";
    print STDERR "Chequeando el modelo online [$urlCFG]\n";
    my ($buffercfg, $msg_err) = &lib_prontus::get_url($urlCFG, 30);
    if($msg_err || $buffercfg eq '') {
        my $resp;
        $resp->{'error'} = 1;
        $resp->{'msg'} = "CFG de modelo no encontrado o invalido [$wizard_lib::URL_MODELS/$modelid/$modelid.cfg]\n";    
        print STDERR $resp->{'msg'};
        print "Content-Type: application/json\n\n";
        &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=0');
    };

    # Se respalda el modelo si es que existe.
    my $dirmodel = "$prontus_varglb::DIR_SERVER$wizard_lib::MODELS_DIR/$modelid";
    if(-d $dirmodel) {
        if (! &wizard_lib::backup_model($modelid)) {
            my $resp;
            $resp->{'error'} = 1;
            $resp->{'msg'} = "No se pudo respaldar el modelo antes de eliminar. El modelo no ha sido eliminado";
            print "Content-Type: application/json\n\n";
            &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=0');
        };
    };

    # Se descarga el modelo
    my $mensaje = &descarga_modelo($modelid);
    if($mensaje) {
        my $resp;
        $resp->{'error'} = 1;
        $resp->{'msg'} = $mensaje;
        print "Content-Type: application/json\n\n";
        &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=0');
    };
    
    my $resp;
    $resp->{'error'} = 0;
    $resp->{'msg'} = '';
    print "Content-Type: application/json\n\n";
    &glib_html_02::print_json_result_hash($resp, 'exit=1,ctype=0');
};

# --------------------------------------------------------------------------------------------------
sub descarga_modelo {
    
    my $modelid = shift;
    my $dirmodel = "$prontus_varglb::DIR_SERVER$wizard_lib::MODELS_DIR/$modelid";
    
    # Descarga tgz
    my $url = $wizard_lib::URL_MODELS . '/' . $modelid . '/' . $modelid . '.tgz';
    my ($tgz_content, $msg_err) = &lib_prontus::get_url($url, 30);
    if ($msg_err) {
        if ($msg_err =~ /^404 /) {
            return "Error al descargar release .tgz, 404 - no se encuentra el archivo[$url]";
        } else {
            return "Error al descargar release .tgz [$url]: $msg_err";
        };

    } else {
        
        # Si ok el tgz, descarga md5
        my $url_md5 = $url . ".md5";
        my ($md5_remoto, $msg_err_md5) = &lib_prontus::get_url($url_md5, 10);
        if ($msg_err_md5) {
            if ($msg_err_md5 =~ /^404 /) {
                return "Error al descargar release md5, 404 - no se encuentra el archivo[$url_md5]";
            } else {
                return "Error al descargar release md5 [$url_md5]: $msg_err_md5";
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
            return "Error al descargar release [$url]: md5 no coincide\nlocal [$md5_local]\nremoto[$md5_remoto]\nEl archivo no se pudo descargar correctamente.";
           
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
    
}
