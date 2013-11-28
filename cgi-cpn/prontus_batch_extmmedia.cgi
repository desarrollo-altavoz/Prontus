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
# Procesar los artículos de un determinado Prontus, moviendo la multimedia
# a la nueva ubicación, si es que detecta que el CFG de External Media
# está habilitado.
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# ./prontus_batch_change_mmedia.cgi <prontus_id>
#
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 23/08/2013 - CVI - Primera Version.
#

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;
#~ use glib_cgi_04;
#~ use glib_hrfec_02;
#~ use lib_tax;
#~ use lib_waitlock; # Bloqueos tipo espera.

use Artic;
use strict;
#~ use lib_artic;
#~ use lib_quota;

my %FORM;

# ---------------------------------------------------------------
# MAIN.
# -------------
main: {

    $FORM{'_prontus_id'} = $ARGV[0];

    if($FORM{'_prontus_id'} eq '') {
        print STDOUT "[error] Debe indicar en nombre del Prontus\n";
        exit;
    };

    # Carga variables de configuracion de prontus.
    my $relpath_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'_prontus_id'});
    my $pathconf = &lib_prontus::ajusta_pathconf($relpath_conf);
    &lib_prontus::load_config($pathconf);  # Prontus 6.0

    if($prontus_varglb::EXTERNAL_MMEDIA != 1) {
        print STDOUT "[error] No se pueden mover los archivos, porque este Prontus no esta configurado para usar Multimedia Externa\n";
        exit;
    };

    my $dirprontus = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_ARTIC";
    if(! -d $dirprontus) {
        print STDOUT "[error] Directorio no valido: dirprontus[$dirprontus]\n";
        exit;
    };

    my $dirprontusmm = $dirprontus;
    if($dirprontusmm =~ s|/site/artic|/site$prontus_varglb::DIR_EXMEDIA|) {
        &glib_fildir_02::check_dir($dirprontusmm);
    } else {
        print "[error] No se pudo crear la nueva carpeta dirprontusmm[$dirprontusmm]\n";
        exit;
    };

    # Primero se procesan los dias
    my @DIRFECHAS = &glib_fildir_02::lee_dir($dirprontus);

    print "[info] Comienza el procesamiento de las carpetas <fechac>\n";

    # Se mezclan los dias y se usan
    foreach my $dir (sort {$b cmp $a} @DIRFECHAS) {
        next if($dir eq '.' || $dir eq '..' || $dir !~ /^\d{8}$/);

        if(-d "$dirprontus/$dir") {
            &procesa_carpeta("$dirprontus/$dir");
        };
    };

    my $cgi_port = "$prontus_varglb::DIR_SERVER/$prontus_varglb::DIR_CGI_CPAN/prontus_port_regen_real.cgi";
    #~ print "[info] Regenerando Portadas: $cgi_port $pathconf\n";
    system("$cgi_port $pathconf");

    print "[info] Las Portadas del sitio fueron regeneradas pero sin tocar los Post Procesos\n";
    print "[info] Ademas recuerde que las Portadas Taxonomicas NO fueron regeneradas\n";

    print "[info] El proceso ha terminado completamente\n";
};

# --------------------------------------------------------------------------------------------------
sub procesa_carpeta {

    my $carpeta = shift;
    my $carpetamm = $carpeta;
    $carpetamm =~ s|/site/artic|/site$prontus_varglb::DIR_EXMEDIA|;

    #~ print STDOUT "\tcarpetamm[$carpetamm]\n";
    &glib_fildir_02::check_dir($carpetamm);

    &glib_fildir_02::copy_tree($carpeta, 'mmedia', $carpetamm, 'mmedia');
    &glib_fildir_02::borra_dir("$carpeta/mmedia");

    # Se procesan los XML de esta carpeta
    my @XMLS = &glib_fildir_02::lee_dir("$carpeta/xml");
    foreach my $xml (sort {$b cmp $a} @XMLS) {
        next if($xml eq '.' || $xml eq '..' || $xml !~ /^\d{14}\.xml$/);
        &procesa_xml($carpeta, $xml);
    };

};
# --------------------------------------------------------------------------------------------------
sub procesa_xml {

    my $carpeta = shift;
    my $xml = shift;
    my $ts_artic = substr($xml, 0, 14);

    my $buffer = &glib_fildir_02::read_file("$carpeta/xml/$xml");

    no warnings 'syntax'; # para evitar el msg "\1 better written as $1"
    if($buffer =~ s|/site/artic/(\d{8})/mmedia/|/site$prontus_varglb::DIR_EXMEDIA/\1/mmedia/|g) {
        &glib_fildir_02::write_file("$carpeta/xml/$xml", $buffer);
        my $artic_obj = Artic->new(
                'prontus_id'=> $prontus_varglb::PRONTUS_ID,
                'public_server_name'=>$prontus_varglb::PUBLIC_SERVER_NAME,
                'cpan_server_name'=>$prontus_varglb::IP_SERVER,
                'document_root'=>$prontus_varglb::DIR_SERVER,
                'ts'=>$ts_artic, # si no va, asigna uno nuevo
                'campos'=>{}) || die "Error inicializando objeto articulo: $Artic::ERR\n";
        my %campos_xml = $artic_obj->get_xml_content();

        # Finalmente el articulo se escribe a disco
        $artic_obj->generar_vista_art('', '', $prontus_varglb::PRONTUS_KEY) || die("[$ts_artic] ERROR!!! $Artic::ERR");

        foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
            $artic_obj->generar_vista_art($mv, '', $prontus_varglb::PRONTUS_KEY) || die("[$ts_artic] ERROR!!! $Artic::ERR");
        };
    };
};
