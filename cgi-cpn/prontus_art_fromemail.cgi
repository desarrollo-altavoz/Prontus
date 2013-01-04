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
# Publicar un artículo desde fuera del administrador Prontus.
# El artículo puede quedar despublicado o bien publicado
# en alguna portada con algun area/orden, con y sin VoBo, todo
# lo anterior dependiendo de los parametros q vengan en el FID y en el archivo cd cfg.
# Implementa control de procesos iguales.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------


# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde cualquier form, vienen los campos como en cualquier fid prontus
# ademas:
# _NP = nombre del publicador, ejemplo "prontus_noticias", se asume q esta en la raiz del sitio
# _IDF = identificador alfanumerico del formulario (ej: "subetuscont")
# _CAPTCHA = captcha a validar
# _MODE = modo en el que correrá la cgi (por ahora sólo acepta modo 'batch'
#
# El resto de los param especiales necesarios se sacan del cfg:
# <nomprontus>-posting.cfg y se agrupan por cada IDF
# ---------


# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------

# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - ycc - 29/01/2007 - primera version
# 1.1 - YCC - 29/11/2007 - Impide que vengan por param el _VB y el _ALTA
# 1.2 - YCC - 01/2008 - Agrega control de captcha y bloqueo de ips
# 1.3 - CVI - 04/2008 - Para el modo Posting Batch
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    use FindBin '$Bin';
    unshift(@INC,$Bin); # Para dejar disponibles las librerias
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();

use glib_fildir_02;
use lib_prontus;
use File::Copy;
use DBI;
use lib_artic;
use Net::POP3;
use MIME::Parser;
use File::Path;
use File::Copy;
use lib_tax;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my ($ARTIC_OBJ);

&main();
exit;

# ---------------------------------------------------------------
sub main {

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
    $FORM{'prontus'} = $ARGV[0];
    $FORM{'_fid'} = $ARGV[1];
    $FORM{'_plt'} = $ARGV[2];
    $FORM{'casilla_popserver'} = $ARGV[3];
    $FORM{'casilla_user'} = $ARGV[4];
    $FORM{'casilla_pass'} = $ARGV[5];

    # &valida_param();

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus'});
    &lib_prontus::load_config("$prontus_varglb::DIR_SERVER$relpath_conf");

    my ($msg_pop, $pop3) = &conectar_pop($FORM{'casilla_popserver'}, $FORM{'casilla_user'}, $FORM{'casilla_pass'});
    die "Error al conectar pop[$msg_pop]\n" if ($msg_pop);

    # dir de salida para mime parser
    my $output_dir_mparser = "$Bin/prontus_temp/emailposting/$FORM{'prontus'}";
    die "check_dir error en [$output_dir_mparser]\n" if (!&glib_fildir_02::check_dir($output_dir_mparser));

    my $parser = new MIME::Parser;
    $parser->output_under($output_dir_mparser);
    $parser->decode_bodies(1);

# files: msg-58137-1.txt , msg-58137-2.html, logo_pucv-color.jpg
# leer todos los .txt y juntarlos,
# Si viene .html dar prio a ese porque viene lo del .txt pero en html
# detectar utf8

    my $messages = $pop3->list();
    foreach $msg_id (keys(%$messages)) {
        my $uid = $pop3->uidl($msg_id);
        # print "reading msg[$msg_id][$uid]\n";
        my $fh = $pop3->getfh($msg_id) || die "No se pudo obtener mensaje nro [$msg_id] $!\n";

        my $entity_obj = $parser->parse($fh);
        die "no se pudo decodificar email" if (!$entity_obj);


        # $entity->dump_skeleton; # debug
        my $head_obj = $entity_obj->head();
        $head_obj->decode();

        # print "Mime type: ", $head_obj->mime_type, "\n";
        # print "Output dir: ", $parser->output_dir, "\n"; # /sites/prontus_development/web/cgi-cpn/prontus_temp/emailposting/prontus_toolbox/msg-1308605806-88408-0
        my $tit = $head_obj->get('Subject',0);
        $tit = &transform_into_utf8($tit);
        $tit =~ s/(\n|\r\n|\r)+$//sg;
        $tit =~ s/^(\n|\r\n|\r)//sg;
        my $ruta_dir = $parser->output_dir;
        my $cuerpo = &get_body_html($ruta_dir);
        $cuerpo = &get_body_from_txt($ruta_dir) if ($cuerpo eq '');

        my ($path_fotoemail) = &get_path_foto_from_email($ruta_dir);
        if ($path_fotoemail) {
            my $nomfile;
            if ($path_fotoemail =~ /\/([^\/]+)$/) {
                $nomfile = $1;
            };
            &File::Copy::copy($path_fotoemail, "$prontus_varglb::DIR_SERVER/$FORM{'prontus'}/cpan/procs/imgedit/$nomfile");
            # print "path_fotoemail[$path_fotoemail] - nomfile[$nomfile]\n";
        };

        # print "tit[$tit]\n";

        # print "cuerpo[$cuerpo]\n--------------------\n";

        my $relpath_fotoemail = &lib_prontus::remove_front_string($path_fotoemail, $prontus_varglb::DIR_SERVER);

        # Crear objeto Artic
        $lib_artic::ARTIC_OBJ = &crear_objeto_artic($tit, $cuerpo, $relpath_fotoemail);

        # Salvar el articulo en base a los datos del objeto Artic
        my $is_new = 1;
        my $msg_err_save = &lib_artic::save_artic_with_object($is_new);
        die $msg_err_save if ($msg_err_save);

        &File::Path::rmtree($parser->output_dir) if (-d $ruta_dir);

        # Despues de examinar, lo borra.
        $pop3->delete($msg_id);

    };
    # Close the connection
    $pop3->quit();

};
# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

sub crear_objeto_artic {
# Crea objeto Artic, para lo cual es basico cargar el hash de datos a partir
# de los datos submitidos.
    my ($titular, $cuerpo, $relpath_fotoemail) = @_;
    my %hash_datos;

    $hash_datos{'_fotoeditada'} = $relpath_fotoemail;
    $hash_datos{'_txt_titular'} = $titular;
    $hash_datos{'vtxt_cuerpo'} = $cuerpo;

    # Campos variables
    $hash_datos{'_fid'} = $FORM{'_fid'};
    $hash_datos{'_plt'} = $FORM{'_plt'};
    # Si no hay control de alta, todos quedan con alta=1.
    $hash_datos{'_alta'} = '1' if ($prontus_varglb::CONTROLAR_ALTA_ARTICULOS ne 'SI');

    # Campos fijos
    $hash_datos{'_seccion1'} = '';
    $hash_datos{'_tema1'} = '0';
    $hash_datos{'_subtema1'} = '0';
    $hash_datos{'_users_id'} = '1';

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
  my $pop3 = Net::POP3->new($popserver);
  return "No es posible conectar con el servidor pop especificado para la casilla de rebotes server[$popserver], user[$user], pass[$pass]\n" unless $pop3;
  my $num_messages = $pop3->login($user, $pass);
  return "Falla login al servidor pop especificado para la casilla de rebotes server[$popserver], user[$user], pass[$pass]\n" unless defined($num_messages);
  # my ($num, $size) = $pop3->popstat();
  # print STDERR "num_messages[$num_messages]\n";
  return ('',$pop3);
};
# ---------------------------------------------------------------
sub valida_param {

    if ( (! -d "$prontus_varglb::DIR_SERVER/$FORM{'prontus'}") || ($FORM{'prontus'} eq '')  || ($FORM{'prontus'} =~ /^\//) )  {
        print STDERR "\nError: Directorio del publicador no es válido.";
        print STDERR "\nDebe indicar el nombre del Prontus a procesar (ej: prontus_noticias), como parametro de esta CGI\n";
        exit;
    };


    $FORM{'_fid'} =~ s/[^\w\-]//sg;
    if (! -f "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/fid/$FORM{'_fid'}.html") {
        print STDERR "\nFID indicado no es valido. Aborta ejecucion.\n";
        exit;
    };

    $FORM{'_plt'} =~ s/[^\w\-\.]//sg;
    if (! -f "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP/artic/fecha/pags/$FORM{'_plt'}") {
        print STDERR "\nPlantilla indicada no es valida. Aborta ejecucion.\n";
        exit;
    };

    if ($FORM{'casilla_popserver'} !~ /^[\.\w\-]+$/s) {
        print STDERR "\nPOP server indicado no es valido. Aborta ejecucion.\n";
        exit;
    };


    if ($FORM{'casilla_user'} !~ /^[\.\w\-\@]+$/s) {
        print STDERR "\nUser de POP server no es valido. Aborta ejecucion.\n";
        exit;
    };

    if ($FORM{'casilla_pass'} !~ /^[\x21-\x7e\x80\x82-\x9c\x9e-\xff]+$/s) {
        print STDERR "\nPassword de POP server no es valida. Aborta ejecucion.\n";
        exit;
    };

};

# ---------------------------------------------------------------
sub get_body_html {
    my $ruta_dir = shift;
    my (@lisdir) = &glib_fildir_02::lee_dir($ruta_dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    my $body_html;
    foreach my $part (@lisdir) {
        next if (! -f "$ruta_dir/$part");
        next if ($part !~ /\.html$/);
        $body_html = &glib_fildir_02::read_file("$ruta_dir/$part");
        if ($body_html =~ /<body.*?>(.+?)<\/body>/is) {
            $body_html = $1;
            return $body_html;
        };
    };
    return '';
};

# ---------------------------------------------------------------
sub get_path_foto_from_email {
    my $ruta_dir = shift;
    my $path_foto;
    my (@lisdir) = &glib_fildir_02::lee_dir($ruta_dir);
    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    my $path_foto;
    foreach my $part (@lisdir) {
        next if (! -f "$ruta_dir/$part");
        next if ($part !~ /\.jpg$/i);
        $path_foto = "$ruta_dir/$part";
        last;
    };
    return $path_foto;
};
# ---------------------------------------------------------------
sub get_body_from_txt {
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

# -------------------------------END SCRIPT----------------------

#        my $body = $entity_obj->bodyhandle;
#        my $cuerpo;
#        my $con_cuerpo = eval { $body->as_string; };
#        $cuerpo = $body->as_string if ($con_cuerpo);
#        print "tit: $tit\n";
#        print "cuerpo: $cuerpo\n----------------\n\n";
