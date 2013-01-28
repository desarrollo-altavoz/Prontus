#!/usr/bin/perl

# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

use glib_cgi_04;
use glib_fildir_02;
use glib_hrfec_02;
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use lib_prontus;
use lib_dd;
use lib_multiediting;

use strict;

my (%FORM);

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();
    $FORM{'path_conf'} = &glib_cgi_04::param('_path_conf');
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    $FORM{'port'} = &glib_cgi_04::param('_port'); # portada principal, la que se está editando.
    $FORM{'port'} =~ s/[\/]//s;

    $FORM{'edic'} = &glib_cgi_04::param('_edic');
    $FORM{'area_mod'} = &glib_cgi_04::param('_area_mod');
    $FORM{'port_mod'} = &glib_cgi_04::param('_port_mod');
    $FORM{'from_area_mod'} = &glib_cgi_04::param('_from_area_mod');
    $FORM{'from_port_mod'} = &glib_cgi_04::param('_from_port_mod');
    $FORM{'accion'} = &glib_cgi_04::param('_accion');
    $FORM{'port_levels'} = &glib_cgi_04::param('_port_levels');
    
    # Deduce path conf del referer, en caso de no ser suministrado.
    $FORM{'path_conf'} = &get_path_conf() if ($FORM{'path_conf'} eq '');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'path_conf'});
    $FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);

    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };

    &cargar_parametros();

    if ($FORM{'port_levels'} ne '') {
        my $hashref = &JSON::jsonToObj($FORM{'port_levels'});
        %lib_dd::PORTLEVELS = %{$hashref};
    }

    &glib_fildir_02::check_dir($prontus_varglb::DIR_SERVER . "/" . $prontus_varglb::PRONTUS_ID . "/cpan/procs/dd/port");
    
    my $DST_SEC = $prontus_varglb::DIR_SERVER . "/" . $prontus_varglb::PRONTUS_ID . "/site/edic/$FORM{'edic'}/port/dd_$FORM{'port'}";
    my $DST_TSEC = $prontus_varglb::DIR_SERVER . "/" . $prontus_varglb::PRONTUS_ID . "/cpan/procs/dd/port/$FORM{'port'}";
    my $path_port = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_TEMP . "/edic/nroedic/port/$FORM{'port'}";
    
    # Verificar si la plantilla es compatible con Drag & Drop. Solo la vista principal.
    my $chk_portada = &lib_dd::check_portada($path_port, $DST_SEC);
    if ($chk_portada ne '') {
        &glib_html_02::print_pag_result('Error', $chk_portada, 1, 'exit=1,ctype=1');
    };

    $FORM{'port'} =~ /(.*?)\.(.*?)$/i;
    my $portname = $1;

    # Para cuando se actualiza un area. Solo retorna el html del area específica.
    if ($FORM{'accion'} eq 'update' && $FORM{'area_mod'} ne '') {
        my $buffer = &actualizar_area_port($FORM{'port_mod'}, $FORM{'area_mod'});
        my $resp;
    
        $resp->{'status'} = '2';
        $resp->{'html'} = $buffer;
        $resp->{'area'} = $FORM{'area_mod'}; # area modificada.
        $FORM{'port_mod'} =~ /(.*?)\.(.*?)/is;
        $resp->{'portname'} = $1;

        if ($FORM{'from_port_mod'} && $FORM{'from_area_mod'}) {
            my $buffer2 = &actualizar_area_port($FORM{'from_port_mod'}, $FORM{'from_area_mod'});
            $resp->{'html_from'} = $buffer2;
            $resp->{'area_from'} = $FORM{'from_area_mod'};
            $FORM{'from_port_mod'} =~ /(.*?)\.(.*?)/is;
            $resp->{'portname_from'} = $1;
        };
        
        &print_json_result_hash($resp, "ctype=1,exit=1");
        exit;
    } else {
        my $nom_recurso = "$FORM{'edic'}-$portname";

        my $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/port_dd/prontus_port_dd.html";
        my $plantilla_head = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/port_dd/plt_head.html";
        my $plantilla_beg_body = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/port_dd/plt_beg_body.html";
        my $plantilla_end_body = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/port_dd/plt_end_body.html";
        my $plantilla_item_area = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/port_dd/plt_item_area.html";
        
        my $pagina = &glib_fildir_02::read_file($plantilla);
        $pagina = &lib_prontus::set_coreplt_ppal($pagina);
        $pagina = &lib_dd::parse_common_vars($pagina); # Se parsean variables comunes

        # Verificar que exista plantilla de portada.
        if (!-f $path_port) {
            &glib_html_02::print_pag_result('Error', 'La portada no existe.', 1, 'exit=1,ctype=1');
        };

        my $plt_port_buffer = &glib_fildir_02::read_file($path_port);
        my $plt_port_dd = $plt_port_buffer;

        # HEAD.
        my $buffer_head = &glib_fildir_02::read_file($plantilla_head);
        $buffer_head = &lib_dd::parse_common_vars($buffer_head);
        $plt_port_dd =~ s/<\/head>/\n$buffer_head\n<\/head>/s;

        # BODY BEGIN.
        my $buffer_beg_body = &glib_fildir_02::read_file($plantilla_beg_body);
        $buffer_beg_body = &lib_dd::parse_common_vars($buffer_beg_body);
        $plt_port_dd =~ s/<body>/$buffer_beg_body/s;

        # BODY END.
        my $buffer_end_body = &glib_fildir_02::read_file($plantilla_end_body);
        $buffer_end_body = &lib_dd::parse_common_vars($buffer_end_body);
        $plt_port_dd =~ s/<\/body>/$buffer_end_body/s;

        # Cargar plantilla para items dentro del loop.
        my $buffer_item_area = &glib_fildir_02::read_file($plantilla_item_area);
            
        # deducir nombre del xml en base al nombre de la plantilla.
        $FORM{'port'} =~ /(.*?)\.(.*?)$/i;
        my $port_xml_filename = "$1.xml";
        
        # Encerrar loops y items en divs
        my ($newbuffer)  = &lib_dd::prepara_loops($plt_port_buffer, $plt_port_dd);
        $newbuffer = &lib_dd::parse_common_vars($newbuffer);
        $plt_port_dd = $newbuffer;

        $plt_port_dd =~ s/%%listnopub%%/$pagina/;

        # Escribir la plantilla DD en disco.
        my $dir_procs_visualadmin = $prontus_varglb::DIR_SERVER . "/" . $prontus_varglb::PRONTUS_ID . "/cpan/procs/dd/port";
        &glib_fildir_02::check_dir($dir_procs_visualadmin);
        my $work_plt_path = $dir_procs_visualadmin . "/$FORM{'port'}";
        &glib_fildir_02::write_file($work_plt_path, $plt_port_dd);

        my $port_xml_path = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_EDIC . "/$FORM{'edic'}/xml/$port_xml_filename";
        &lib_dd::cargar_areas($port_xml_path, '', $FORM{'port'});
        &lib_prontus::make_portada($DST_SEC, $DST_TSEC, $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
            $FORM{'_vista'}, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
            $FORM{'_edic'}, '1', $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
            '', $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $prontus_varglb::USERS_PERFIL);
    };

    my $portada_buffer = &glib_fildir_02::read_file($DST_SEC);

    # encontrar ord en xml de portada y reemplazarlo en portada parseada.
    $portada_buffer = &lib_dd::parse_ord_vb($portada_buffer);
    # Encuentra includes en la portada y los resuelve. comentado por el momento.
    #~ $portada_buffer = &lib_dd::encuentra_includes($portada_buffer, $FORM{'edic'});

    &glib_fildir_02::write_file($DST_SEC, $portada_buffer);

    # Volver a leer el archivo generado en el site, pero desde http y no filesystem, para que los php y ssi se ejecuten.
    my $http_host = $ENV{'HTTP_HOST'};

    if ($http_host eq '') {
        &glib_html_02::print_pag_result('Error', "No se pudo determinar el HTTP_HOST del sitio.", 1, 'exit=1,ctype=1');
    };
    
    my $url_port_site = "http://$http_host/$prontus_varglb::PRONTUS_ID/site/edic/$FORM{'edic'}/port/dd_$FORM{'port'}";
    my ($http_content, $http_line) = &lib_prontus::get_url($url_port_site);

    if ($http_line ne '') {
        print STDERR "Error al obtener la url [$url_port_site]: $http_line\n";
        my $msg = "Ocurri&oacute; un error al tratar de procesar la portada con interfaz drag & drop. <br/><br/>$http_line";
        &glib_html_02::print_pag_result('Error', $msg, 1, 'exit=1,ctype=1');
    };

    if ($FORM{'accion'} eq 'update') {
        #~ sleep 10;
        # Solo entregar contenido del div id portada.
        $http_content =~ /<!--prontusportddportada-->(.*?)<!--\/prontusportddportada-->/gs;
        my $resp;
        $resp->{'status'} = '1';
        $resp->{'html'} = $1;
        &print_json_result_hash($resp, "ctype=1,exit=1");
    } else {
        print "Content-Type: text/html\n\n";
        print $http_content;
    };
    
};

sub print_json_result_hash {
    # Imprime ajax con reporte de resultado.
    my ($hash) = $_[0];  # 0 | 1
    my ($options) = $_[1]; # exit=1|0, ctype=1|0

    my ($exit, $ctype);
    $exit = 1 if ($options =~ /(^|,) *exit *= *1 *(,|$)/);
    $ctype = 1 if ($options =~ /(^|,) *ctype *= *1 *(,|$)/);

    #~ binmode(STDOUT, ":utf8");
       
    print "Content-Type: text/html\n\n" if ($ctype);
    my $json = new JSON;
    # print $json->to_json($resp);
    print &JSON::to_json($hash);
    exit if ($exit);
};


sub cargar_parametros {
    my @campos = &glib_cgi_04::param();
    foreach my $cod (@campos) {
        $lib_dd::FORM{$cod} = &glib_cgi_04::param($cod);
    };
};

sub actualizar_area_port {
    my $port_mod = $_[0];
    my $area_mod = $_[1];
    my ($dir_macros) = $prontus_varglb::DIR_SERVER . "/" . $prontus_varglb::PRONTUS_ID . "/plantillas/edic/nroedic/macros";

    # cargar articulos publicados en cada area de la portada.
    &lib_dd::cargar_areas('', '', $port_mod);
    # Retornar solo el area modificada.

    my $buffer = &lib_dd::get_loop_portada($port_mod, $area_mod);
    $buffer = &lib_dd::parse_common_vars($buffer);
    $buffer = &lib_prontus::add_macros($buffer, $dir_macros, '', '');
    $buffer = &lib_prontus::parser_area($area_mod,$buffer, $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
                                      $prontus_varglb::CONTROL_FECHA, $prontus_varglb::STAMP_DEMO,
                                      $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $prontus_varglb::USERS_PERFIL);

    #~ print STDERR "buffer[$buffer]\n";

    $buffer = &lib_dd::parse_ord_vb($buffer);

    #~ $buffer = &lib_dd::encuentra_includes($buffer, $FORM{'edic'}); # encuetra y reemplaza includes (php/ssi)

    # Se debe escribir el buffer en un html temporal, para llamarlo por http para que se ejecuten los php y sii.
    my $tmpfiledir = $prontus_varglb::DIR_SERVER . "/" . $prontus_varglb::PRONTUS_ID . "/site/tmp";
    &glib_fildir_02::check_dir($tmpfiledir);
    $port_mod =~ /(.*?)\.(.*?)$/i;
    my $tmpfilename = "area_$FORM{'area_mod'}_$FORM{'port_mod'}";
    &glib_fildir_02::write_file("$tmpfiledir/$tmpfilename", $buffer);

    # En caso que falle esto, se usará el buffer obtenido desde filesystem.
    my $url_port_site = "http://$prontus_varglb::PUBLIC_SERVER_NAME/$prontus_varglb::PRONTUS_ID/site/tmp/$tmpfilename";
    my ($http_content, $http_line) = &lib_prontus::get_url($url_port_site);

    if ($http_line eq '') {
        $buffer = $http_content;
    } else {
        print STDERR "Error al obtener la url [$url_port_site]: $http_line\n";
    };

    unlink "$tmpfiledir/$tmpfilename";

    return $buffer;
};
