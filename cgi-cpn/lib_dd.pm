# --------------------------------------------------------------
# Prontus CMS
# http://www.prontus.cl
# by Altavoz.net
#
# licensed under LGPL license.
# http://www.prontus.cl/license.html
# --------------------------------------------------------------

package lib_dd;

use glib_fildir_02;

%FORM = ();
$INCLUCONT = 0;
$MAXLEVEL = 3;
%PORTLEVELS = ();

# ---------------------------------------------------------------
# Verifica si una portada es compatible con la interfaz drag & drop.
sub check_portada {
    my $path_plt = $_[0];
    my $path_site = $_[0];
    
    if (-f $path_plt) {
        if ($path_plt =~ /\/port\/_(.*?)$/is) {
            print STDERR "Esta interfaz no está disponible para las portadas que comienzan con _ (underscore).\n";
            return "Esta interfaz no est&aacute; disponible para las portadas que comienzan con _ (underscore).\n";
        };

        $path_plt =~ /\/port\/(.*?\..*?)$/;
        my $port = $1;
        if (!$prontus_varglb::PORT_DRAGANDROP{$port}) {
            print STDERR "La plantilla tiene deshabilitada la interfaz drag & drop via CFG.\n";
            return "La plantilla no tiene habilitada la interfaz drag & drop en la configuraci&oacute;n.";
        };
        
        my $buffer_plt = &glib_fildir_02::read_file($path_plt);

        if ($buffer_plt =~ /<!--cfg_dd=no-->/isg) {
            print STDERR "La plantilla tiene deshabilitada la interfaz drag & drop.\n";
            return "La plantilla tiene deshabilitada la interfaz drag & drop.";
        }
        
        my %loops = &_get_loops($buffer_plt);
        my $loop_count = keys(%loops);
        # Revisar que la plantilla tenga al menos 1 loop.
        if ($loop_count > 0) {
            # Revisar que no existan loops repetidos.
            if (!&_check_loops_repet(\%loops)) {
                if ($buffer_plt =~ /<html.*?>(.*?)<\/html>/isg) {
                    my $html = $1;
                    if ($html !~ /<head>.*?<\/head>/isg) {
                        print STDERR "La plantilla esta incompleta, no contiene la etiqueta &lt;head&gt;&lt;/head&gt;.\n";
                        return "La plantilla est&aacute; incompleta, no contiene la etiqueta &lt;head&gt;&lt;/head&gt;.\n";
                    };
                    if ($html !~ /<body.*?>.*?<\/body>/isg) {
                        print STDERR "La plantilla esta incompleto, no contiene la etiqueta &lt;body&gt;&lt;/body&gt;.\n";
                        return "La plantilla est&aacute; incompleta, no contiene la etiqueta &lt;body&gt;&lt;/body&gt;.\n";
                    };
                } else {
                    print STDERR "La plantilla esta incompleta, no contiene la etiqueta &lt;html&gt;&lt;/html&gt;.\n";
                    return "La plantilla est&aacute; incompleta, no contiene la etiqueta &lt;html&gt;&lt;/html&gt;.\n";
                };
                return '';
            } else {
                print STDERR "check_portada: la plantilla tiene loops repetidos.\n";
                return "La plantilla tiene loops repetidos, por lo tanto no podr&aacute; ser usada la interfaz drag & drop.";
            };
        } else {
            print STDERR "check_portada: la plantilla debe tener al menos 1 loop.\n";
            return "La plantilla debe tener al menos 1 loop para poder utilizarla en la interfaz drag & drop.";
        };
    } else {
        print STDERR "check_portada: la plantilla [$path_plt] no existe.\n";
        return "La plantilla no existe.";
    };
};

sub _get_loops {
    my $buffer_plt = $_[0];
    my %loops;
    while ($buffer_plt =~ /%%LOOP(\d+)(\([^)]+?\))?%%(.*?)%%\/LOOP%%/isg) {
        $loops{$1} = $loops{$1} + 1;
    };

    return %loops;
};

sub _check_loops_repet {
    my $hashref = $_[0];
    foreach my $key (%{$hashref}) {
        if ($hashref->{$key} > 1) {
            return 1;
        };
    };
    return 0;
};


# 1. Traducir los require_once, y genera sus respectivas plantillas dd.

sub encuentra_includes {
    my $buffer = $_[0];
    my $edic = $_[1];
    my $newbuff = $buffer;

    #~ print STDERR "INCLUCONT[$INCLUCONT]\n";
    
    $INCLUCONT++;

    #~ my $tmpfiledir = $prontus_varglb::DIR_SERVER . "/" . $prontus_varglb::PRONTUS_ID . "/site/tmp";
    #~ &glib_fildir_02::check_dir($tmpfiledir);

    # PHP.
    while ($buffer =~ /<\?php(.*?)\?>/sig) {
        my $phpcode = $1;
        #~ print STDERR "phpcode[$phpcode]\n";
        while ($phpcode =~ /require_once\s*?[\(]?(.*?)[\)]?;/isg) {
            my $require = $1;
            #~ print STDERR "require[$require]\n";
            if ($require =~ /\/port\/(.*?)['|"|;]?$/is) {
                my $port = $1;
                my $path_plt_port = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_TEMP . "/edic/nroedic/port/$port";
                # Verificar que exista la plantilla para la portada.
                if (-f $path_plt_port && $path_plt_port =~ /\/port\/[_m_|_p_].*?$/is) {
                    # Generar vista para poder editar esa area.
                    if (&genera_vista_include($path_plt_port, $port, $edic)) {
                        $newbuff =~ s/$port/dd_$port/isg;
                    };
                };
            };            
        };
    };

    # SSI.
    while ($buffer =~ /<!--#include file="(.*?)" -->/sig) {
        my $path = $1;
        if ($path =~ /\/port\/(.*?)$/is) {
            my $port = $1;
            my $path_plt_port = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_TEMP . "/edic/nroedic/port/$port";
            if (-f $path_plt_port && $path_plt_port =~ /\/port\/[_m_|_p_].*?$/is) {
                # Generar vista para poder editar esa area.
                if (&genera_vista_include($path_plt_port, $port, $edic)) {
                    $newbuff =~ s/$port/dd_$port/isg;
                };
            };
        };
        
    };

    return $newbuff;
};

sub genera_vista_include {
    my $filepath = $_[0];
    my $port = $_[1];
    my $edic = $_[2];

    my $level = $PORTLEVELS{$port};

    $port =~ /(.*?)\.(.*?)$/i;
    my $port_xml_filename = "$1.xml";
    my $portname = $1;
    
    my $dstsitefile = $prontus_varglb::DIR_SERVER . "/" . $prontus_varglb::PRONTUS_ID . "/site/edic/$edic/port/dd_$port";
    my $dstpltfile = $prontus_varglb::DIR_SERVER . "/" . $prontus_varglb::PRONTUS_ID . "/cpan/procs/dd/port/$port";
    my $port_xml_path = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_EDIC . "/$edic/xml/$port_xml_filename";
    my $buffer_include = &glib_fildir_02::read_file($filepath);
    my $buffer_copy = $buffer_include;

    if ($buffer_include =~ /<!--cfg_dd=no-->/isg) {
        return '';
    }

    my ($buffer_include) = &prepara_loops($buffer_include, $buffer_include, $level);

    $buffer_include =~ s/%%_port%%/$port/isg;
    $buffer_include =~ s/%%_portname%%/$portname/isg;
    $buffer_include =~ s/%%_edic%%/$edic/isg;
    $buffer_include = &parse_common_vars($buffer_include);
    

    # parsear portada.
    #~ print STDERR "genera_vista_include: port[$port]\n";
    &cargar_areas($port_xml_path, '', $port);
    &glib_fildir_02::write_file($dstpltfile, $buffer_include);
    
    &lib_prontus::make_portada($dstsitefile, $dstpltfile, $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
        '', $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
        $edic, '1', $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
        '', $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $prontus_varglb::USERS_PERFIL);

    # Reemplazar marcas de vob y ord.
    my $buffer = &glib_fildir_02::read_file($dstsitefile);
    $buffer = &parse_ord_vb($buffer);
    #~ if ($INCLUCONT < $MAXLEVEL) {
        #~ $buffer = &encuentra_includes($buffer, $edic);
    #~ };
    
    &glib_fildir_02::write_file($dstsitefile, $buffer);

};

sub prepara_loops {
    my $buffer = $_[0];
    my $port_dd = $_[1];
    my $level = $_[2];
    #~ my $is_include = $_[2];
    my $newbuffer = $buffer;

    my $tpl = 'plt_item_area.html';

    if ($level eq '') { # Si no viene el nivel, lo busca segun las prioridades.
        if ($INCLUCONT > 0) {
            $tpl = "plt_item_area_lv$INCLUCONT.html";
        };
    } else {
        $tpl = "plt_item_area.html" if ($level == 0);
        $tpl = "plt_item_area_lv1.html" if ($level == 1);
        $tpl = "plt_item_area_lv2.html" if ($level == 2);
    };

    #~ print STDERR "level[$level], tpl[$tpl]\n";
    
    my $plantilla_item_area = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/port_dd/$tpl";
    my $buffer_item_area = &glib_fildir_02::read_file($plantilla_item_area);
    
    while ($buffer =~ /(%%LOOP(\d+)(\([^)]+?\))?%%(.*?)%%\/LOOP%%)/isg) {
        my $loop = $1;
        my $loop_num = $2;
        my $loop_nom = $3;
        my $inside_loop = $4;
        my $new_item_loop = $buffer_item_area;

        $new_item_loop =~ s/%%loop_num%%/$loop_num/isg;
        $new_item_loop =~ s/%%loop_nom%%/$loop_nom/is;
        $new_item_loop =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/is;

        my $url_editar = 'prontus_art_ficha.cgi?_file=%%_ts%%.html&_fid=%%_fid%%&_path_conf=%%_path_conf%%&fotosvtxt=/1/2/3/4';
        $new_item_loop =~ s/%%url_editar%%/$url_editar/is;
        $new_item_loop =~ s/%%item_loop%%/$inside_loop/is;
        
        $port_dd =~ s/%%LOOP$loop_num(\([^)]+?\))?%%(.*?)%%\/LOOP%%/$new_item_loop/is;

        $new_item_loop =~ s/%%LOOP(.*?)%%//isg;
        $new_item_loop =~ s/%%\/LOOP%%//isg;

        $new_item_loop =~ /^<div id="area_$loop_num\_.*?" class=".*?">(.*?)<\/div>$/is;
    };

    return ($port_dd);
};


sub escape_for_regex {
    my $str = $_[0];
    $str =~ s/\./\\./sig;
    $str =~ s/\//\\\//isg;
    $str =~ s/\$/\\\$/isg;
    $str =~ s/\(/\\\(/isg;
    $str =~ s/\)/\\\)/isg;
    $str =~ s/\]/\\\]/isg;
    $str =~ s/\[/\\\[/isg;
    return $str;
};


sub cargar_areas {
    my $xml_path = $_[0];
    my $from_xml = $_[1];
    my $port = $_[2];

    # Reset
    %lib_prontus::AREA = ();
    %lib_prontus::PRIO = ();
    %lib_prontus::VB = ();

    my @campos = keys(%FORM);
    
    if (!$from_xml && $FORM{'_accion'} eq 'update') {
        #~ print STDERR "Carga1\n";
        # La informacion del orden y articulos viene por post.
        if ($port ne '') {
            # Carga los artículos según la portada.
            my $areaportcont = 0;
            foreach my $key (keys(%FORM)) {
                #~ print STDERR "key[$key], value[$FORM{$key}]\n";
                if ($key =~ /_port_(\d{14})/ && $FORM{$key} eq $port) {
                    my $ts = $1;
                    #~ print STDERR "$port => ts[$ts], area = " . $FORM{"_area_$ts"} . "\n";
                    $lib_prontus::AREA{$ts} = $FORM{"_area_$ts"};
                    $lib_prontus::PRIO{$ts} = $FORM{"_orden_$ts"};
                    $lib_prontus::VB{$ts} = $FORM{"_vb_$ts"};
                    my $is_corrupt = $FORM{"_corrupt_$ts"}; # '1' | ''
                    
                    # Si no se especifica area o prioridad, los articulos no se publican en la portada
                    if (($lib_prontus::PRIO{$ts} eq '') || ($lib_prontus::PRIO{$ts} eq '0') || ($lib_prontus::AREA{$ts} eq '') || ($lib_prontus::AREA{$ts} eq '0') || ($is_corrupt == 1)) {
                        $lib_prontus::AREA{$ts} = '';
                        $lib_prontus::PRIO{$ts} = '';
                        $lib_prontus::VB{$ts} = '';
                    };
                    # Validar que para areas y prioridades se especifiquen solo digitos.
                    if (($lib_prontus::AREA{$ts} !~ /^[0-9]+$/) || ($lib_prontus::PRIO{$ts} !~ /^[0-9]+$/)) {
                        $lib_prontus::AREA{$ts} = '';
                        $lib_prontus::PRIO{$ts} = '';
                    };
                    #~ print STDERR "AREA: $lib_prontus::AREA{$ts}\n";
                    #~ print STDERR "PRIO: $lib_prontus::PRIO{$ts}\n";
                    #~ print STDERR "VB: $lib_prontus::VB{$ts}\n";
                    $areaportcont++;
                };
            };
            #~ print STDERR "areaportcont[$areaportcont]\n";
            if ($areaportcont == 0) {
                #~ print STDERR "carga_areas: loaded from xml\n";
                &_carga_areas_from_xml($xml_path);
                print STDERR "no hay areas en post\n";
            }
        } else {
            #~ print STDERR "Carga3\n";
            foreach my $cod (@campos) {
                if ($cod =~ m/^_area_(\d{14})/) {
                    my $ts = $1;
                    $lib_prontus::AREA{$ts} = $FORM{$cod};      # Asocia area a id del articulo.
                    $lib_prontus::PRIO{$ts} = $FORM{"_orden_$ts"}; # Asocia prioridad correspondiente.
                    $lib_prontus::VB{$ts} = $FORM{"_vb_$ts"};
                    my $is_corrupt = $FORM{"_corrupt_$ts"}; # '1' | ''

                    # Si no se especifica area o prioridad, los articulos no se publican en la portada
                    if (($lib_prontus::PRIO{$ts} eq '') || ($lib_prontus::PRIO{$ts} eq '0') || ($lib_prontus::AREA{$ts} eq '') || ($lib_prontus::AREA{$ts} eq '0') || ($is_corrupt == 1)) {
                        $lib_prontus::AREA{$ts} = '';
                        $lib_prontus::PRIO{$ts} = '';
                        $lib_prontus::VB{$ts} = '';
                    };
                    # Validar que para areas y prioridades se especifiquen solo digitos.
                    if (($lib_prontus::AREA{$ts} !~ /^[0-9]+$/) || ($lib_prontus::PRIO{$ts} !~ /^[0-9]+$/)) {
                        $lib_prontus::AREA{$ts} = '';
                        $lib_prontus::PRIO{$ts} = '';
                    };
                };
            };
        };
    } else {
        #~ print STDERR "Carga2\n";
        &_carga_areas_from_xml($xml_path);
    };
    
};

sub _carga_areas_from_xml {
    my $xml_path = $_[0];
    my $buffer = &glib_fildir_02::read_file($xml_path);
    while ($buffer =~ /<rowartic>(.*?)<\/rowartic>/isg) {
        my $rowartic = $1;
        $rowartic =~ /<file>(\d+)<\/file>/;
        my $ts = $1;
        $rowartic =~ /<area>(\d+)<\/area>/;
        my $area = $1;
        $rowartic =~ /<ord>(\d+)<\/ord>/;
        my $ord = $1;
        $rowartic =~ /<vb>(\d+)<\/vb>/;
        my $vb = $1;

        $lib_prontus::AREA{$ts} = $area;
        $lib_prontus::PRIO{$ts} = $ord;
        $lib_prontus::VB{$ts} = $vb;
    };
};

sub parse_ord_vb {
    my $buffer = $_[0];
    while ($buffer =~ /<div class="item-area" rel="(\d+)" title=".*?">.*?<\/div>/isg) {
        my $ts = $1;
        my $find = "<input type=\"hidden\" name=\"_orden_$ts\" value=\"\" />";
        my $replace = "<input type=\"hidden\" name=\"_orden_$ts\" value=\"$lib_prontus::PRIO{$ts}\" />";
        $buffer =~ s/$find/$replace/isg;
        
        $find = "<input type=\"hidden\" name=\"_vb_$ts\" value=\"\" />";
        $replace = "<input type=\"hidden\" name=\"_vb_$ts\" value=\"$lib_prontus::VB{$ts}\" />";
        $buffer =~ s/$find/$replace/isg;
    };
    return $buffer;
};

sub parse_common_vars {
    my $buffer = $_[0];

    $FORM{'port'} =~ /^(.*?)\.(.*?)$/is;
    my $portname = $1;
    my $nom_recurso = "$FORM{'_edic'}-$portname";
    
    $buffer =~ s/%%nom_recurso%%/$nom_recurso/sig;
    $buffer =~ s/%%_path_conf%%/$FORM{'_path_conf'}/sig;
    $buffer =~ s/%%_prontus_id%%/$prontus_varglb::PRONTUS_ID/sig;
    $buffer =~ s/%%_port%%/$FORM{'_port'}/sig;
    $buffer =~ s/%%_portname%%/$portname/sig;
    $buffer =~ s/%%_edic%%/$FORM{'_edic'}/sig;
    $buffer =~ s/%%_dir_cgi_cpn%%/$prontus_varglb::DIR_CGI_CPAN/sig;

    return $buffer;
};

sub get_loop_portada {
    my $port = $_[0];
    my $area = $_[1];
    $port =~ /(.*?)\.(.*?)/is;
    my $portname = $1;
    my $path_plt_port = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_TEMP . "/edic/nroedic/port/$port";
    my $buffer = &glib_fildir_02::read_file($path_plt_port);
    my $buffer_loop = '';

    my $level = $PORTLEVELS{$port};
    #~ print STDERR "get_loop_portada: level[$level], port[$port], area[$area]\n";
    
    while ($buffer =~ /(%%LOOP(\d+)(\([^)]+?\))?%%(.*?)%%\/LOOP%%)/isg) {
        if ($2 eq $area) {
            $buffer_loop = $1;
            last;
        };
    };

    
    $buffer_loop = &prepara_loops($buffer_loop, $buffer_loop, $level);
    
    $buffer_loop =~ /%%LOOP(\d+)(\([^)]+?\))?%%(.*?)%%\/LOOP%%/is;
    $buffer_loop = $3;
    $buffer_loop =~ s/%%_port%%/$port/isg;
    $buffer_loop = &parse_common_vars($buffer_loop);
    #~ print STDERR "buffer_loop[$buffer_loop]\n";

    return $buffer_loop;
};

return 1;
