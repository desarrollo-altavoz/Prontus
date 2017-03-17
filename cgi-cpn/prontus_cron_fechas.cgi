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
# Cambia el estado de publicacion de los articulos segun sus fechas de
# publicacion y expiración, también actualiza las portadas en las que se
# encuentran publicados
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------


# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------

# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------

# ---------------------------------------------------------------
# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.1 - 16/05/2001 - Modificaciones para parametrizacion del protocolo (http o https) a traves del arch. de conf.
# 1.2 - 16/05/2001 - Revision general de detalles de forma.

# Prontus 6.0 - 29/10/2001 - Revision/modificaciones para Prontus 6.0
# Prontus 8.0 - 03/06/2002 - YCH. Ver Extensiones y correcciones en /release_prontus80.txt
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt
# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {
    use FindBin '$Bin';
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
};

use strict;
# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_fildir_02;
use lib_prontus;
use glib_cgi_04;
use DBI;

use Data::Dumper;
# ---------------------------------------------------------------
# DECLARACIONES GLOBALES.
# ---------------------------------------------------------------
my $AMBIENTE_WEB;
my $EDIC;
my $DST_SEC;
my $DST_TSEC;
my $DST_PAG;
my $DST_IMG;
my $DST_SWF;
my $DST_WMEDIA;
my $DST_ASOCFILE;
my %FORM;
my $DB;
my %TAX_REG = ();
my %LIST_REG = ();
my %TAGS_REG = ();
# ---------------------------------------------------------------
# MAIN.
# -------------
main : {
    if ($ENV{'SERVER_NAME'} ne '') { # ambiente web
        &glib_cgi_04::new();
        $FORM{'prontus'} = &glib_cgi_04::param('prontus');
        $FORM{'ports'} = &glib_cgi_04::param('ports'); # port1/port2/port3 (OPTATIVO, portadas a procesar, si viene, se procesan solo estas ports en vez de todas)
        print "Content-Type: text/html\r\n\r\n";
        $| = 1;
        $AMBIENTE_WEB = 1;
    } else {
        $FORM{'prontus'} = $ARGV[0];
        $prontus_varglb::IP_SERVER = $ARGV[1];
        $FORM{'ports'} = $ARGV[2];
    };

    &valida_param();

    my $msg_err_bd;
    ($DB, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($DB)) {
        die "ERROR: $msg_err_bd\n";
        exit;
    };

    &check_prontus();

    $DB->disconnect;
    # print STDERR Dumper(\%TAX_REG);
    # print STDERR Dumper(\%LIST_REG);
    # print STDERR Dumper(\%TAGS_REG);

    my $pathnice = &lib_prontus::get_path_nice();
    $pathnice = "$pathnice -n19 " if($pathnice);
    my $path_cgicpn = $prontus_varglb::DIR_SERVER. '/'. $prontus_varglb::DIR_CGI_CPAN;
    my ($cmd, $regen);

    # regeneramos portadas taxonomicas
    foreach $regen (keys %TAX_REG) {
        $cmd = "$pathnice $path_cgicpn/prontus_cron_taxport.cgi $prontus_varglb::PRONTUS_ID $regen >/dev/null 2>&1 &";
        print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
        system $cmd;
    }

    # regeneramos portadas lista
    if ($prontus_varglb::LIST_PROCESO_INTERNO eq 'SI') {
        foreach $regen (keys %LIST_REG) {
            $cmd = "$pathnice $path_cgicpn/prontus_cron_list.cgi $prontus_varglb::PRONTUS_ID $regen >/dev/null 2>&1 &";
            print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
            system $cmd;
        }
    }

    # regeneramos portadas tagonomicas
    foreach $regen (keys %TAGS_REG) {
        $cmd = "$pathnice $path_cgicpn/prontus_tags_ports.cgi $prontus_varglb::PRONTUS_ID $regen >/dev/null 2>&1 &";
        print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
        system $cmd;
    }

    print "<br><br>Proceso terminado." if ($AMBIENTE_WEB);
}; # main
# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------
sub valida_param {
    if ( (! -d "$prontus_varglb::DIR_SERVER/$FORM{'prontus'}") || ($FORM{'prontus'} eq '') || ($FORM{'prontus'} =~ /^\//) )  {
        print "\nError: Directorio del publicador no es válido.";
        if ($AMBIENTE_WEB) {
            print "<br>Debe indicar el nombre del Prontus a procesar, ejemplo: prontus=prontus_noticias";
        } else {
            print "\nDebe indicar el nombre del Prontus a procesar (ej: prontus_noticias), como primer parametro de esta CGI\n";
        };
        exit;
    };

    if (!$AMBIENTE_WEB) {
        if ($prontus_varglb::IP_SERVER eq '') {
            print "\nDebe indicar el nombre del servidor (ej: www.altavoz.net), como segundo parametro de esta CGI\n";
            exit;
        };
    };

    # Carga variables de configuracion.
    my $path_conf = &lib_prontus::get_relpathconf_by_prontus_id($FORM{'prontus'});
    &lib_prontus::load_config( &lib_prontus::ajusta_pathconf($path_conf) );
};

# ---------------------------------------------------------------
sub check_prontus {
    if ($prontus_varglb::CONTROL_FECHA ne 'SI') {
        print "\n Error : El Prontus indicado no corresponde a uno con Control de Fechas. \n";
        exit;
    };

    # Chequea ediciones.
    # procesa edicion vigente, la ultima y la base.
    my (@ediciones) = &lib_prontus::get_edics4update();
    foreach my $entry (@ediciones) {
        $EDIC = $entry;
        &get_main_data();
        &check_portadas();
    };
    # Borra cache de listas de articulos del cpan
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");
};

# --------------------------------------------------------------------#
# Obtiene datos principales del formulario.
sub get_main_data {
# print "Content-Type: text/html\n\n"; # debug
    my $DDIR = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . '/%%DIR_FECHA%%';
    my $DIRMMEDIA = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_EXMEDIA . '/%%DIR_FECHA%%';

    # Directorio de Secciones existentes
    $DST_SEC = $prontus_varglb::DIR_SERVER .
             $prontus_varglb::DIR_CONTENIDO .
             $prontus_varglb::DIR_EDIC .
             "/$EDIC" .
             $prontus_varglb::DIR_SECC;

    # Path absoluto al dir. donde residen los templates de portadas.
    $DST_TSEC = $prontus_varglb::DIR_SERVER .
                $prontus_varglb::DIR_TEMP .
                $prontus_varglb::DIR_EDIC .
                $prontus_varglb::DIR_NROEDIC .
                $prontus_varglb::DIR_SECC;

    $DST_PAG = $prontus_varglb::DIR_SERVER . $DDIR . $prontus_varglb::DIR_PAG;

    # Path absoluto a Directorio destino de las imagenes.
    $DST_IMG = $prontus_varglb::DIR_SERVER . $DDIR . $prontus_varglb::DIR_IMAG;

    # Path absoluto a Directorio destino de las swf. # 8.0
    $DST_SWF = $prontus_varglb::DIR_SERVER . $DDIR . $prontus_varglb::DIR_SWF;

    # Path absoluto a Directorio destino de los archivos windowsmedia. # 8.1
    $DST_WMEDIA = $prontus_varglb::DIR_SERVER . $DIRMMEDIA . $prontus_varglb::DIR_MMEDIA;

    # Path absoluto a Directorio destino de los archivos genericos asociados. # 1.2
    $DST_ASOCFILE = $prontus_varglb::DIR_SERVER . $DDIR . $prontus_varglb::DIR_ASOCFILE;
};
# --------------------------------------------------------------------#
sub is_base_port {
    my ($port) = $_[0];
    foreach my $bport (@prontus_varglb::BASE_PORTS) {
        if ($port eq $bport) {
            return 1;
        };
    };
    return 0;
};
# --------------------------------------------------------------------#
# Regenera todas las portadas publicadas.
sub check_portadas {
    my (@entries, $entry, $arch_seccion, $text_seccion);

    my @ports = split(/\//, $FORM{'ports'});

    my $dir_plt_tax = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_TEMP
                    . $prontus_varglb::DIR_PTEMA . '/';

    # Deduce del path completo de la portada, el del xml.
    my $pathdir_seccs_xml = $DST_SEC;
    $pathdir_seccs_xml =~ s/\/port$/\/xml/;

    @entries = &glib_fildir_02::lee_dir($pathdir_seccs_xml);
    #~ print "pathdir_seccs_xml[$pathdir_seccs_xml]\n";
    # Recorre las secciones publicadas
    foreach $entry (@entries) {
        if (($entry !~ /^\./g) and ($entry !~ /^preview/ig)) {
            my $procesar_port = 1; # por omision las procesa todas
            # si esta el param correspondiente, procesa solo las portadas especificadas

            if ($#ports >= 0) {
                $procesar_port = 0;
                foreach my $specific_port (@ports) {
                    if ($entry eq "$specific_port.xml") {
                        $procesar_port = 1;
                        last;
                    };
                };
            };
            next if (!$procesar_port);

            $arch_seccion = "$pathdir_seccs_xml/$entry";

            if ((-s $arch_seccion) and (! -d $arch_seccion)) {
                $text_seccion = &glib_fildir_02::read_file($arch_seccion);
                # Rescatar la info de c/artic de la seccion correspondiente
                my $totartics = 0;
                while ($text_seccion =~ /<rowartic>[ \n]*?<dir>(\d+?)<\/dir>[ \n]*?<file>(.*?)<\/file>[ \n]*?<area>(\d*?)<\/area>[ \n]*?<ord>(\d*?)<\/ord>[ \n]*?(<vb>(\w*?)<\/vb>)?[ \n]*?<?i?n?>?([\w\/\-]*?)<?\/?i?n?>?[ \n]*?<?o?u?t?>?([\w\/\-]*?)<?\/?o?u?t?>?[ \n]*?<?p?u?b?>?(\d?)<?\/?p?u?b?>?[ \n]*?<\/rowartic>/isg) {
                    my ($dirfecha,$art,$area,$prio,$pub,$ext_art,$vb) = '';
                    ($dirfecha,$art,$area,$prio,$vb,$pub) = ($1,$2,$3,$4,$6,$9);

                    # si cambio el estado de publicacion debemos realizar operaciones de actualización
                    my $art_pub_status = &lib_prontus::get_status_pub($art, $prontus_varglb::CONTROL_FECHA, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $DB);
                    if ($pub ne $art_pub_status) {
                        my $xml_data = &lib_prontus::get_xml_data("$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/site/artic/".substr($art, 0,8)."/xml/$art.xml");
                        my %campos_xml = &lib_prontus::getCamposXml($xml_data);

                        my $filtro_fid = '';
                        if (-e $dir_plt_tax . $campos_xml{'_fid'}) {
                                $filtro_fid = $campos_xml{'_fid'};
                        }

                        # chequeamos la taxonomia a regenerar
                        for (my $i = 1; $i < 4; $i++) {
                            if ($campos_xml{"_seccion$i"} ne '') {
                                $campos_xml{"_seccion$i"} = 0 if ($campos_xml{"_seccion$i"} eq '');
                                $campos_xml{"_tema$i"} = 0 if ($campos_xml{"_tema$i"} eq '');
                                $campos_xml{"_subtema$i"} = 0 if ($campos_xml{"_subtema$i"} eq '');

                                $TAX_REG{$filtro_fid.'/'.$campos_xml{"_seccion$i"}.'/'.$campos_xml{"_tema$i"}.'/'.$campos_xml{"_subtema$i"}} = 1;
                                $LIST_REG{$campos_xml{'_fid'}.'/'.$campos_xml{"_seccion$i"}.'/'.$campos_xml{"_tema$i"}.'/'.$campos_xml{"_subtema$i"}} = 1;
                            }
                        }

                        # si hay tags agregamos las tagonomicas a regenerar
                        if ($campos_xml{'_tags'} ne '') {
                            $campos_xml{'_tags'} =~ s/\,/\//g;
                            $TAGS_REG{$campos_xml{'_tags'}." $filtro_fid"} = 1;
                        }

                        # agregamos las listas a regenerar por taxonomia
                        if (!($campos_xml{'_seccion1'} || $campos_xml{'_seccion2'} || $campos_xml{'_seccion3'})) {
                            $LIST_REG{$campos_xml{'_fid'} . '///'} = 1;
                        }
                    }

                    $lib_prontus::AREA{$art} = $area;      # Asocia area al articulo.
                    $lib_prontus::PRIO{$art} = $prio;      # Asocia prioridad correspondiente.
                    if ($vb eq '') { $vb = 1; };
                    $lib_prontus::VB{$art} = $vb;      # Asocia VoBo correspondiente.
                    $lib_prontus::DIR_FECHA{$art} = $dirfecha;

                    $totartics++ if($lib_prontus::AREA{$art});
                };# while

                $entry = &get_nom_port($entry); # obtener nombre de la portada a re-escribir

                next;

                if ($prontus_varglb::MULTI_EDICION eq 'SI') {
                # solo para multi-edicion: si la edicion es la base, actualiza solo las portadas declaradas como BASE_PORTS
                    if (($EDIC eq 'base') && (! &is_base_port($entry))) {
                        %lib_prontus::AREA = ();
                        %lib_prontus::PRIO = ();
                        %lib_prontus::VB = ();
                        %lib_prontus::DIR_FECHA = ();
                        next;
                    }
                };

                if ($entry) {
                    print "<br>Actualizando Portada [$entry]" if ($AMBIENTE_WEB);

                    # Primero para la vista por defecto (o sea, sin vista)
                    my $mv = '';
                    my $sin_regen_xml = 0;
                    my $ts_preview = '';
                    my $users_perfil = 'A';
                    &lib_prontus::make_portada("$DST_SEC/$entry", $DST_TSEC . "/$entry", $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
                                       $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
                                       $EDIC, $sin_regen_xml, $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
                                       $ts_preview, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $users_perfil);


                    # Ahora proceso multivistas
                    $sin_regen_xml = 1; # para no reescribir el xml
                    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
                        &lib_prontus::make_portada("$DST_SEC/$entry", $DST_TSEC . "/$entry", $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
                                         $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
                                         $EDIC, $sin_regen_xml, $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
                                         $ts_preview, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $users_perfil);
                    };

                    &lib_prontus::write_log('Actualizar', 'Portada', "$DST_SEC/$entry (Articulos: $totartics)", 'Control Fecha');
                } else {
                    print STDERR "2 arch_seccion $arch_seccion\n";
                    if($arch_seccion =~ /^(.*?)\/([^\/]+)$/) {
                        my $dirxml = $1;
                        my $namexml = $2;
                        &glib_fildir_02::check_dir("$dirxml/bak/cron_fechas");
                        File::Copy::move($arch_seccion, "$dirxml/bak/cron_fechas/$namexml");
                        print "\n Warning: se mueve xml sin portada [$arch_seccion] a bak/cron_fechas\n";
                        print "<br>" if ($AMBIENTE_WEB);
                    } else {
                        print "\n Warning: no existe portada para [$arch_seccion]\n";
                        print "<br>" if ($AMBIENTE_WEB);
                    };
                };

                %lib_prontus::AREA = ();
                %lib_prontus::PRIO = ();
                %lib_prontus::VB = ();
                %lib_prontus::DIR_FECHA = ();
            };# if
        };# if
    };# foreach
};

# ---------------------------------------------------------------
# Obtiene de la lista de tpls. de portadas la primera cuyo nombre sin extension coincida con el q viene por param.
sub get_nom_port {
    my $port_xml = $_[0];

    $port_xml =~ s/\.\w+$//;
    my $entry;
    foreach $entry (keys %prontus_varglb::PORT_PLTS) {
        if ((-s "$DST_TSEC/$entry") and (! -d "$DST_TSEC/$entry")) {
        # print STDERR "entry[$entry] - port_xml[$port_xml]\n";
            if ($entry =~ /^$port_xml\.\w+$/) {
                return $entry;
            };
        };
    };

    return '';
};
# -------------------------------END SCRIPT----------------------
