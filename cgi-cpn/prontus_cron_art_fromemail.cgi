#!/usr/bin/perl

# ---------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# PROPOSITO
# ---------------------------------------------------------------
# Publicar un artículo desde una casilla de e-mail.
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ---------------------------------------------------------------
# La casilla de e-mail es leida en cada invocacion.
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# EJEMPLO DE ARCHIVO DE CONFIGURACION.
# ---------------------------------------------------------------
# FROMEMAIL_FID = 'fid_noticia'
# FROMEMAIL_PLT = 'noticia.html'
# FROMEMAIL_POP_SERVER = ''
# FROMEMAIL_POP_USER = ''
# FROMEMAIL_POP_PASS = ''
# FROMEMAIL_POP_SSL = '0'
# FROMEMAIL_ACCESS_TOKEN = 'aaabbbccc'
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# EJEMPLO DEL CORREO
# ---------------------------------------------------------------
# [key ACCESSTOKEN]
# [titular Este es el titular]
# [bajada Bajada del articulo]
# [autor Autor]
# [cuerpo Cuerpo del mensaje
# Este es el cuerpo
# ]
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------------------------------------------
# 1.0 - ycc - 29/01/2007 - primera version
# 1.1 - YCC - 29/11/2007 - Impide que vengan por param el _VB y el _ALTA
# 1.2 - YCC - 01/2008 - Agrega control de captcha y bloqueo de ips
# 1.3 - CVI - 04/2008 - Para el modo Posting Batch
# 2.0 - ALD - 2018-10-08 - Agrega accessToken.
#                        - Fuerza SSL en la conexion (para que funcione).
# 3.0 - JOR - 20/10/2018 - El body del correo trae los datos del articulo: titular, cuerpo, bajada, autor, key.
#                        - Todas las fotos adjuntas se agregan al banco de imagenes.
#                        - Audio y video se agregan al articulo.
# 3.1 - JOR - 23/10/2018 - Lee archivo de configuracion ubicado en cpan/<prontus_id>-fromemail.cfg
# ---------------------------------------------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);

    eval {"require MIME::Parser; 1;";}
            or die("Se necesita el módulo MIME::Parser; para ejecutar este Script");
};

use utf8; # p12.
use strict;

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();

use glib_fildir_02;
use glib_hrfec_02;
use lib_prontus;
use File::Copy;
use DBI;
use lib_artic;
use Net::POP3;
use MIME::Parser;

use File::Path;
use File::Copy;
use lib_tax;
use lib_maxrunning;


# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my $DEBUG = 0;
my %CONFIG;

# ---------------------------------------------------------------
main: {

# To-do:
# - soportar otros tipos de archivos
# - Autenticacion
# - soportar varias fotos --> cambio estructural (o add-on) a prontus para que en vez de leer de un dir un solo archivo, pueda leer varios.
# Ojo: se agrega MIME/Parser a los requisitos y probablemente Net::POP3

    # Soporta un maximo de n copias corriendo.
    if (&lib_maxrunning::maxExcedido(1)) {
        die('Maximo de copias alcanzado');
    };

    use FindBin '$Bin';

    # Nombre del prontus
    my $prontus_id = $ARGV[0];

    # Carga de configuracion p11
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($prontus_id);
    &lib_prontus::load_config( &lib_prontus::ajusta_pathconf($relpath_conf) );

    # Carga la configuracion.
    &loadConfig();

    my ($msg_pop, $pop3) = &conectar_pop($CONFIG{'FROMEMAIL_POP_SERVER'}, $CONFIG{'FROMEMAIL_POP_USER'}, $CONFIG{'FROMEMAIL_POP_PASS'});

    if ($msg_pop) {
        print "ERROR con POP: $msg_pop\n";
        exit;
    }

    # dir de salida para mime parser
    my $output_dir_mparser = "$Bin/prontus_temp/emailposting/$prontus_varglb::PRONTUS_ID";
    die "check_dir error en [$output_dir_mparser]\n" if (!&glib_fildir_02::check_dir($output_dir_mparser));

    my $parser = new MIME::Parser;
    $parser->output_under($output_dir_mparser);
    $parser->decode_bodies(1);

    # files: msg-58137-1.txt , msg-58137-2.html, logo_pucv-color.jpg
    # leer todos los .txt y juntarlos,
    # Si viene .html dar prio a ese porque viene lo del .txt pero en html
    # detectar utf8

    my $messages = $pop3->list();
    foreach my $msg_id (keys(%$messages)) {
        my $uid = $pop3->uidl($msg_id);
        # print "reading msg[$msg_id][$uid]\n";
        my $fh = $pop3->getfh($msg_id) || die "No se pudo obtener mensaje nro [$msg_id] $!\n";

        my $entity_obj = $parser->parse($fh);
        die "no se pudo decodificar email" if (!$entity_obj);

        # $entity->dump_skeleton; # debug
        my $head_obj = $entity_obj->head();
        $head_obj->decode();

        my $subject = $head_obj->get('Subject',0);
        my $ruta_dir = $parser->output_dir;
        my $cuerpo = &get_body_html($ruta_dir);

        $subject =~ s/(\n|\r)//sg;

        &logError("Procesando correo [$subject]\n");

        $cuerpo = &get_body_from_txt($ruta_dir) if ($cuerpo eq '');

        # Verifica que el body del correo tenga el access token... si no ignora el correo.
        if (&hasAccessToken($cuerpo)) {
            my $dataRef = &getDataFromBody($cuerpo, $ruta_dir);

            # Valida el access token y que el body del correo tenga todo lo necesario para crear el articulo.
            if (&validateDataFromBody($dataRef)) {
                &addArticToProntus($dataRef);
            } else {
                &logError("ERROR: Los datos del correo son insuficientes [$subject].");
            }
        }

        # Elimina correo localmente y del servidor.
        &File::Path::rmtree($parser->output_dir) if (-d $ruta_dir);
        $pop3->delete($msg_id);
    }

    # Close the connection
    $pop3->quit();
};
# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub addArticToProntus {
    my $dataRef = $_[0];
    my %data = %{$dataRef};

    $lib_artic::ARTIC_OBJ = &crear_objeto_artic($dataRef);

    # Salvar el articulo en base a los datos del objeto Artic
    my $is_new = 1;
    my $msg_err_save = &lib_artic::save_artic_with_object($is_new);
    my $flushXml = 0;

    if ($msg_err_save) {
        &logError("ERROR: No se pudo crear el artitulo [$data{'titular'}].\n");
    } else {
        my @fotos = @{$data{'fotos'}};
        my $buff_xml_data   = &lib_prontus::get_xml_data($lib_artic::ARTIC_OBJ->{fullpath_xml});
        my %campos_xml = &lib_prontus::getCamposXml($buff_xml_data);

        &logError("Articulo creado. ts[$lib_artic::ARTIC_OBJ->{ts}]");

        # Si hay fotos agregarlas al articulo.
        if (scalar @fotos > 0) {
            $lib_artic::ARTIC_OBJ->{xml_data} = &glib_fildir_02::read_file($lib_artic::ARTIC_OBJ->{fullpath_xml});
            my %filename2nomfoto;

            foreach my $foto (@fotos) {
                my $relpath = $foto;
                $relpath =~ s/$prontus_varglb::DIR_SERVER//sg;
                my @parts = split /\//, $relpath;
                my $filename = $parts[$#parts];
                my $nomfoto = $lib_artic::ARTIC_OBJ->_add_foto_filesystem($relpath, $filename);

                $filename2nomfoto{$filename} = $nomfoto;
            }

            # Arreglar fotos en el VTXT. Se debe cambiar el src del tag img por la nueva ruta hacia la foto guardada en el articulo.
            my $new_cuerpo = $data{'cuerpo'};
            my @imgs = $new_cuerpo =~ /(<img [^>]+)/;

            foreach my $img (@imgs) {
                my $newimg = "$img>";

                foreach my $dato (keys %filename2nomfoto) {
                    if ($img =~ /alt=["|']$dato["|']/) {
                        my $relpathnewfoto = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . "/$campos_xml{'_fechap'}" . $prontus_varglb::DIR_IMAG . "/" . $filename2nomfoto{$dato};

                        $newimg =~ s/src=["|'].*?["|']/src="$relpathnewfoto"/sg;
                        $new_cuerpo =~ s/$img/$newimg/sg;
                    }
                }
            }

            $lib_artic::ARTIC_OBJ->{xml_data} = &lib_prontus::replace_in_xml($lib_artic::ARTIC_OBJ->{xml_data}, 'vtxt_cuerpo', $new_cuerpo, 1);

            $flushXml = 1;
        }

        # TODO: Si hay audio o video agregar a que marca ??
        # Luego gatillar transcodificación de ambos.

        if ($data{'video'} ne '') {
            # print "Video!\n";
            my $relpath = $data{'video'};
            $relpath =~ s/$prontus_varglb::DIR_SERVER//sg;
            my $nom_campo = 'multimedia_video1';
            my $dst_dir = $lib_artic::ARTIC_OBJ->{'dst_multimedia'};
            my $nom_arch = $lib_artic::ARTIC_OBJ->_get_newnom_arch('multimedia',  $nom_campo, $relpath);
            my $dst_file = "$dst_dir/$nom_arch";

            &File::Copy::copy($data{'video'}, $dst_file);

            $lib_artic::ARTIC_OBJ->{xml_data} = &lib_prontus::replace_in_xml($lib_artic::ARTIC_OBJ->{xml_data}, $nom_campo, $nom_arch, 0);

            $flushXml = 1;
        }

        if ($data{'audio'} ne '') {
            # print "Audio!\n";
            my $relpath = $data{'audio'};
            $relpath =~ s/$prontus_varglb::DIR_SERVER//sg;
            my $nom_campo = 'multimedia_audio1';
            my $dst_dir = $lib_artic::ARTIC_OBJ->{'dst_multimedia'};
            my $nom_arch = $lib_artic::ARTIC_OBJ->_get_newnom_arch('multimedia',  $nom_campo, $relpath);
            my $dst_file = "$dst_dir/$nom_arch";

            &File::Copy::copy($data{'audio'}, $dst_file);

            $lib_artic::ARTIC_OBJ->{xml_data} = &lib_prontus::replace_in_xml($lib_artic::ARTIC_OBJ->{xml_data}, $nom_campo, $nom_arch, 0);

            $flushXml = 1;
        }

        # Gatillar transcodificacion de video y audio.
        # Como hacerlo con la transcodificacion ?

        $lib_artic::ARTIC_OBJ->_flush_xml() if ($flushXml);

        # &logError("Articulo creado!");
    }
};

sub crear_objeto_artic {
    my %data = %{$_[0]};
    my %hash_datos;

    # $hash_datos{'_fotoeditada'} = $relpath_fotoemail;
    $hash_datos{'_txt_titular'} = $data{'titular'};
    $hash_datos{'vtxt_cuerpo'} = $data{'cuerpo'};

    # print "cuerpo[$data{'cuerpo'}]\n";

    $hash_datos{'_txt_bajada'} = $data{'bajada'} if ($data{'bajada'} ne '');
    $hash_datos{'_autor'} = $data{'autor'} if ($data{'autor'} ne '');

    # Campos variables
    $hash_datos{'_fid'} = $CONFIG{'FROMEMAIL_FID'};
    $hash_datos{'_plt'} = $CONFIG{'FROMEMAIL_PLT'};
    $hash_datos{'_alta'} = '0';
    $hash_datos{'_users_id'} = '1';

    # Asignar fecha de publicación.
    my $fecha = &glib_hrfec_02::get_dtime_pack4();
    $fecha =~ /^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})/;
    $hash_datos{'_fechap'} = "$1$2$3";
    $hash_datos{'_horap'} = "$4:$5";

    my $artic_obj = Artic->new(
                    'prontus_id'        =>$prontus_varglb::PRONTUS_ID,
                    'document_root'     =>$prontus_varglb::DIR_SERVER,
                    'public_server_name'=>$prontus_varglb::PUBLIC_SERVER_NAME,
                    'cpan_server_name'  =>$prontus_varglb::PUBLIC_SERVER_NAME,
                    'ts'                =>'', # si no va, asigna uno nuevo
                    'campos'            =>\%hash_datos)
                    || die "Error inicializando objeto articulo: $Artic::ERR\n";

    return $artic_obj;
};
# ---------------------------------------------------------------
sub conectar_pop {
  my ($popserver, $user, $pass) = @_;
  my $pop3 = Net::POP3->new($popserver, SSL => $CONFIG{'FROMEMAIL_POP_SSL'}); # 2.0
  return "No es posible conectar con el servidor pop especificado para la casilla de rebotes server[$popserver], user[$user], pass[$pass]\n" unless $pop3;
  my $num_messages = $pop3->login($user, $pass);
  return "Falla login al servidor pop especificado para la casilla de rebotes server[$popserver], user[$user], pass[$pass]\n" unless defined($num_messages);
  # my ($num, $size) = $pop3->popstat();
  # print STDERR "num_messages[$num_messages]\n";
  return ('',$pop3);
};

# ---------------------------------------------------------------
sub get_body_html {
    # print "get_body_html\n";
    my $ruta_dir = shift;
    my (@lisdir) = &glib_fildir_02::lee_dir($ruta_dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    my $body_html;
    foreach my $part (@lisdir) {
        next if (! -f "$ruta_dir/$part");
        next if ($part !~ /\.html$/);
        $body_html = &glib_fildir_02::read_file("$ruta_dir/$part");
        # if ($body_html =~ /<body.*?>(.+?)<\/body>/is) {
            # $body_html = $1;
        return $body_html;
        # };
    };
    return '';
};

sub get_path_audio_from_email {
    my $ruta_dir = shift;
    my $path;
    my (@lisdir) = &glib_fildir_02::lee_dir($ruta_dir);

    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

    foreach my $part (@lisdir) {
        next if (! -f "$ruta_dir/$part");
        next if ($part !~ /\.(wav|mp3)$/i);
        $path = "$ruta_dir/$part";
        last;
    }

    return $path;
};

sub get_path_video_from_email {
    my $ruta_dir = shift;
    my $path;
    my (@lisdir) = &glib_fildir_02::lee_dir($ruta_dir);

    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..

    foreach my $part (@lisdir) {
        next if (! -f "$ruta_dir/$part");
        next if ($part !~ /\.(mp4|flv)$/i);
        $path = "$ruta_dir/$part";
        last;
    }

    return $path;
};


# ---------------------------------------------------------------
sub get_body_from_txt {
    # print "get_body_from_txt\n";
    my $ruta_dir = shift;
    my (@lisdir) = &glib_fildir_02::lee_dir($ruta_dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    my $body_txt;
    foreach my $part (@lisdir) {
        next if (! -f "$ruta_dir/$part");
        next if ($part !~ /\.txt$/);
        $body_txt .= &glib_fildir_02::read_file("$ruta_dir/$part");
    };
    $body_txt = &transform_into_utf8($body_txt);
    $body_txt =~ s/(\n|\r\n|\r)+/\n/sg;
    $body_txt =~ s/\n/<br \/>\n/sg;
    return $body_txt;
};

# ---------------------------------------------------------------
sub transform_into_utf8 {
    my $text = shift;
    if ($text ne '') {
        my $tester = $text;
        my $es_utf8 = utf8::decode($tester);
        if(!$es_utf8) {
            utf8::encode($text);
        };
    };
    return $text;
};

sub getDataFromBody {
    # print "getDataFromBody\n";
    my $body = $_[0];
    my $ruta_dir = $_[1];
    my %data;

    if ($body =~ /\[key ([^\]]+)/is) {
        $data{'key'} = $1;
        $data{'key'} =~ s/ //sg;
        $data{'key'} =~ s/(\n|\r\n|\r|\t)//sg;
    }

    if ($body =~ /\[titular ([^\]]+)/is) {
        $data{'titular'} = $1;
        $data{'titular'} =~ s/^(\n|\r\n|\r|\t)//sg;
        $data{'titular'} =~ s/(\n|\r\n|\r|\t)+$//sg;
    }

    if ($body =~ /\[bajada ([^\]]+)/is) {
        $data{'bajada'} = $1;
        $data{'bajada'} =~ s/^(\n|\r\n|\r|\t)//sg;
        $data{'bajada'} =~ s/^(\n|\r\n|\r|\t)+$//sg;
    }

    if ($body =~ /\[autor ([^\]]+)/is) {
        $data{'autor'} = $1;
        $data{'autor'} =~ s/^(\n|\r\n|\r|\t)//sg;
        $data{'autor'} =~ s/(\n|\r\n|\r|\t)+$//sg;
    }

    if ($body =~ /\[cuerpo ([^\]]+)/is) {
        $data{'cuerpo'} = $1;
        $data{'cuerpo'} =~ s/^(\n|\r\n|\r|\t)//sg;
        $data{'cuerpo'} =~ s/(\n|\r\n|\r|\t)+$//sg;

        # TODO: Convertir salto d linea en br ?

        # Se dejan solo los tags permitidos.
        $data{'cuerpo'} =~ s/<(?!\/?(p|a|b|i|u|br|strong|table|tr|td|tbody|thead|ul|li|ol|em|img)(?=>|\s?.*>))\/?.*?>//sg;
    }

    # Si hay fotos agregarlas.
    my @listdir = &glib_fildir_02::lee_dir($ruta_dir);
    my @fotos;

    @listdir = grep !/^\./, @listdir; # Elimina directorios . y ..

    foreach my $file (@listdir) {
        next if (! -f "$ruta_dir/$file");
        next if ($file !~ /\.(jpg|jpeg|png|gif)$/i);

        # print "foto: $file\n";

        push @fotos, "$ruta_dir/$file";
    }

    # Si no hay fotos agrega igual el arreglo pero vacio.
    $data{'fotos'} = \@fotos;

    $data{'audio'} = &get_path_audio_from_email($ruta_dir);
    $data{'video'} = &get_path_video_from_email($ruta_dir);

    return \%data;
};

sub hasAccessToken {
    my $body = $_[0];

    if ($body =~ /\[key ([^\]]+)/is) {
        return 1;
    }

    return 0;
};


sub validateDataFromBody {
    # print "validateDataFromBody\n";
    my %data = %{$_[0]};

    # Obligatorios.
    if ($data{'titular'} eq '') {
        &logError("ERROR: Falta el titular.");

        return 0;
    }

    if ($data{'cuerpo'} eq '') {
        &logError("ERROR: Falta el cuerpo.");

        return 0;
    }

    if ($data{'key'} ne $CONFIG{'FROMEMAIL_ACCESS_TOKEN'}) {
        &logError("ERROR: El access token es invalido.");

        return 0;
    }

    # TODO: otras validaciones.

    return 1;
};

sub logError {
    my $msg = $_[0];
    my $exit = $_[1];

    print STDERR "$msg\n";
    print "$msg\n" if ($DEBUG);

    exit if ($exit);
};

sub loadConfig {
    my $path = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/cpan/$prontus_varglb::PRONTUS_ID-fromemail.cfg";

    if (!-f $path) {
        &logError("No existe el archivo de configuracion", 1);
    }

    my $buffervarcfg = &glib_fildir_02::read_file($path);

    if ($buffervarcfg =~ m/\s*FROMEMAIL_FID\s*=\s*["'](.*?)["']/) {
        $CONFIG{'FROMEMAIL_FID'} = $1;
    }

    if ($CONFIG{'FROMEMAIL_FID'} eq '') {
        &logError("Error en la configuracion: Falta FROMEMAIL_FID", 1);
    } else {
        $CONFIG{'FROMEMAIL_FID'} =~ s/[^\w\-]//sg;
        if (! -f "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/fid/$CONFIG{'FROMEMAIL_FID'}.html") {
            &logError("FID indicado no es valido. Aborta ejecucion", 1);
        }
    }

    if ($buffervarcfg =~ m/\s*FROMEMAIL_PLT\s*=\s*["'](.*?)["']/) {
        $CONFIG{'FROMEMAIL_PLT'} = $1;
    }

    if ($CONFIG{'FROMEMAIL_PLT'} eq '') {
        &logError("Error en la configuracion: Falta FROMEMAIL_PLT", 1);
    } else {
        $CONFIG{'FROMEMAIL_PLT'} =~ s/[^\w\-\.]//sg;
        if (! -f "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP/artic/fecha/pags/$CONFIG{'FROMEMAIL_PLT'}") {
            &logError("Plantilla indicada no es valida. Aborta ejecucion.", 1);
        }
    }

    if ($buffervarcfg =~ m/\s*FROMEMAIL_POP_SERVER\s*=\s*["'](.*?)["']/) {
        $CONFIG{'FROMEMAIL_POP_SERVER'} = $1;
    }

    if ($CONFIG{'FROMEMAIL_POP_SERVER'} eq '') {
        &logError("Error en la configuracion: Falta FROMEMAIL_POP_SERVER", 1);
    }

    if ($buffervarcfg =~ m/\s*FROMEMAIL_POP_USER\s*=\s*["'](.*?)["']/) {
        $CONFIG{'FROMEMAIL_POP_USER'} = $1;
    }

    if ($CONFIG{'FROMEMAIL_POP_USER'} eq '') {
        &logError("Error en la configuracion: Falta FROMEMAIL_POP_USER", 1);
    }

    if ($buffervarcfg =~ m/\s*FROMEMAIL_POP_PASS\s*=\s*["'](.*?)["']/) {
        $CONFIG{'FROMEMAIL_POP_PASS'} = $1;
    }

    if ($CONFIG{'FROMEMAIL_POP_PASS'} eq '') {
        &logError("Error en la configuracion: Falta FROMEMAIL_POP_PASS", 1);
    }

    $CONFIG{'FROMEMAIL_POP_SSL'} = 1;
    if ($buffervarcfg =~ m/\s*FROMEMAIL_POP_SSL\s*=\s*["'](.*?)["']/) {
        $CONFIG{'FROMEMAIL_POP_SSL'} = $1;
    }

    if ($buffervarcfg =~ m/\s*FROMEMAIL_ACCESS_TOKEN\s*=\s*["'](.*?)["']/) {
        $CONFIG{'FROMEMAIL_ACCESS_TOKEN'} = $1;
    }

    if ($CONFIG{'FROMEMAIL_ACCESS_TOKEN'} eq '') {
        &logError("Error en la configuracion: Falta FROMEMAIL_ACCESS_TOKEN", 1);
    }

};
