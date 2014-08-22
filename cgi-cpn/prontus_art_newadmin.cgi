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
# SCRIPT.
# -----------
#

# ---------------------------------------------------------------
# UBICACION.
# -----------
# /cgi-cpn/.

# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Carga el head del adm. de artículos y los divs contenedores (pero vacios) de los art publ y no publ
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# desde el menu de prontus
# prontus_art_newadmin.cgi?_path_conf=/prontus_toolbox/cpan/prontus_toolbox.cfg
# ---------------------------------------------------------------
# INVOCACIONES REALIZADAS.
# ------------------------
# desde la plantilla, en doc. ready invoca a lista de pub y lista de no pub
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# plantilla prontus_art_newadmin.html
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# no registra
# ---------------------------------------------------------------
# Tablas.
# ------------------------
# ART

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
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

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

use prontus_varglb; &prontus_varglb::init();

use glib_html_02;
use glib_fildir_02;
use lib_prontus;
use lib_search;

use glib_cgi_04;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my (%FORM);
main: {
    # Recibe parametros.
    &glib_cgi_04::new();

    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');

    # Deduce path conf del referer, en caso de no ser suministrado.
    $FORM{'_path_conf'} = &get_path_conf() if ($FORM{'_path_conf'} eq '');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    $FORM{'_port'} = &glib_cgi_04::param('_port');

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    &lib_prontus::test_servers($ENV{'HTTP_REFERER'}) if ($prontus_varglb::IP_SERVER);

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user(1);
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_pag_result('Ha ocurrido un error', $prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
    };


    # Cargar Ediciones
    my $dir_edics = $prontus_varglb::DIR_SERVER .
                    $prontus_varglb::DIR_CONTENIDO .
                    $prontus_varglb::DIR_EDIC;
    my $newer_edic;
    ($FORM{'_edic'}, $newer_edic) = &get_edic($dir_edics);
    my $html_ediciones = &get_html_ediciones($dir_edics);

    # Cargar Portadas
    my $dir_tpl_port = $prontus_varglb::DIR_SERVER .
                       $prontus_varglb::DIR_TEMP .
                       $prontus_varglb::DIR_EDIC .
                       $prontus_varglb::DIR_NROEDIC .
                       $prontus_varglb::DIR_SECC;
    my $html_port;
    ($FORM{'_port'}, $html_port) = &get_port($FORM{'_port'}, $newer_edic, $dir_tpl_port);


    my $buffer = &glib_fildir_02::read_file("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CORE/prontus_art_newadmin.html");
    $buffer = &lib_prontus::set_coreplt_ppal($buffer);


    my %vars2replace;
    $vars2replace{'_port'} = $html_port;
    $vars2replace{'_path_conf'} = $FORM{'_path_conf'};
    $vars2replace{'_edic'} = $html_ediciones;
    $vars2replace{'_js_spare'} = &generar_js_spare($dir_tpl_port);
    $vars2replace{'_js_base_ports'} = &generar_js_base_ports();
    $vars2replace{'_prontus_id'} = $prontus_varglb::PRONTUS_ID;
    $vars2replace{'_multi_edicion'} = $prontus_varglb::MULTI_EDICION;

    my $port_nom = $FORM{'_port'};
    $port_nom =~ s/\.\w+$//;
    $vars2replace{'_port_nom'} = $port_nom;

    # CVI - 16/06/2011
    my $open_fid_in_pop = 'open_normally';
    if($prontus_varglb::ABRIR_FIDS_EN_POP eq 'SI') {
        $open_fid_in_pop = 'open_in_pop';
    }
    $buffer =~ s/%%_class_open_fid%%/$open_fid_in_pop/ig;

#    $vars2replace{'_prontus_version'} = $prontus_varglb::VERSION_PRONTUS;
#    $vars2replace{'_prontus_user_name'} = $prontus_varglb::USERS_USR;
#    $vars2replace{'_prontus_user_perfil'} = &get_perfil_glosa($prontus_varglb::USERS_PERFIL);

    $buffer = &lib_prontus::replace_hash_fields($buffer, \%vars2replace, 1);

    $buffer = &set_ctrl_fecha($buffer);
    $buffer = &set_multi_vista($buffer);
    $buffer = &set_rayo($buffer); # a partir de 11.2.19 el rayo va incorporado al guardar portada
    $buffer = &set_admin_port($buffer);

    #~ Se parsean la seccion de Mis Busquedas
    $buffer = &lib_search::parsea_mis_busquedas($buffer, $prontus_varglb::USERS_ID);

    #~ Parsea un par de variables del CFG
    $buffer =~ s/%%_edicbase_ini_selected%%/$prontus_varglb::EDICBASE_INI_SELECTED/ig;

    print "Content-type: text/html\n\n";
    print $buffer;
}; # main


# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------


# ---------------------------------------------------------------
sub get_path_conf {
  # Deduce path conf del referer.
  $ENV{'HTTP_REFERER'} =~ /https?\:\/\/[^\/]+(\/.+\/cpan).+$/;
  my $path_conf = $1 . '/' . &get_id_prontus . '.cfg';
  return $path_conf;

};
# ---------------------------------------------------------------
sub get_default_port {
# Obtiene primera portada (nombre de archivo con extension y sin path), en orden alfabetico, de la lista de tpls. de portadas.
    my $newer_edic = shift;
    my $dir_tpl_port = shift;

    my ($entry, $first_entry, $i);
    my $nombase = $prontus_varglb::DIR_UNICAEDIC;
    $nombase =~ s/^\///;
    foreach $entry (sort {$a cmp $b} keys %prontus_varglb::PORT_PLTS) {
        if ((-s "$dir_tpl_port/$entry") and (! -d "$dir_tpl_port/$entry")) {

            # Si la portada actual no esta dentro de las base ports, entonces no se considera.
            # Pues la primera edicion que se carga es la base.
            if (($FORM{'_edic'} eq $nombase) && ($prontus_varglb::MULTI_EDICION eq 'SI') && ($newer_edic)) {
                my $bport;
                my $found;

                foreach $bport (@prontus_varglb::BASE_PORTS) {
                    if ($entry eq $bport) {
                        $found = 1;
                    };
                };
                if (! $found) {
                    next;
                };
            };

            # Considerar solo las portadas permitidos al usuario conectado.
            if ( ($prontus_varglb::USERS_PERFIL eq 'P') || ($prontus_varglb::USERS_PERFIL eq 'E') ) { # Periodista o Editor
                if (&port_asoc($entry) ne 'S') {
                    next;
                };
            };

            $i++;
            if ($i == 1) {
                $first_entry = $entry;
            };

            if ($prontus_varglb::PORT_INI_SELECTED eq $entry) {
                return $entry;
            };
        } else {
            $dir_tpl_port = $prontus_varglb::DIR_TEMP .
                               $prontus_varglb::DIR_EDIC .
                               $prontus_varglb::DIR_NROEDIC .
                               $prontus_varglb::DIR_SECC;
            print "Content-Type: text/html\n\n";
            my $msg = "El archivo plantilla de portada <b>$dir_tpl_port/$entry</b> no existe."
                    . " Debes crearlo o cambiar la configuraci&oacute;n manualmente"
                    . " <a href=\"/$prontus_varglb::DIR_CGI_CPAN/prontus_edit_main.cgi"
                    . "?_path_conf=/$prontus_varglb::PRONTUS_ID/cpan/$prontus_varglb::PRONTUS_ID.cfg"
                    . "&_dir=/$prontus_varglb::PRONTUS_ID/cpan&_file=$prontus_varglb::PRONTUS_ID-port.cfg\">"
                    . "editando</a>"
                    . " el archivo <b>/$prontus_varglb::PRONTUS_ID/cpan/$prontus_varglb::PRONTUS_ID-port.cfg</b>.";

            &glib_html_02::print_pag_result("Ha ocurrido un problema", $msg);
            print STDERR "Error: Archivo plantilla de portada no existe: $dir_tpl_port/$entry\n";
            exit;
        };
    };

    return $first_entry;
};

# ---------------------------------------------------------------
sub get_id_prontus {
  # Deduce prontus_id del referer.
  $ENV{'HTTP_REFERER'} =~ /\/([^\/]+?)\/cpan.+$/;
  my $prontus_id = $1;
  return $prontus_id;
};

# ---------------------------------------------------------------
sub get_html_port {
    # <select name="_port" id="_port" onchange="Listartic.cambiaPortada()">
    my($name_obj) = 'cmb_port';
    my($valor_clave) = shift;
    my($dir_tpl_port) = shift;
    my($items_visibles) = '1';
    my($ind_multiple) = '';
    my($javascript) =  'onchange="Listartic.cambiaPortada()"';

    my($lista) = '';
    my($val_display, $key, $clave);

    my $nombase = $prontus_varglb::DIR_UNICAEDIC;
    $nombase =~ s/^\///;

    # Generar la lista de seleccion en html
    $lista = q{<select id="} . $name_obj . q{" name="} . $name_obj . q{" size="} . $items_visibles . q{" } . $ind_multiple . ' ' . $javascript . q{>} . "\n";


    # Ordenar alfabeticamente. y si la portada no tiene nombre (o port == nombre), queda al ultimo.

    my %PORTS_TO_ORDER;
    foreach my $key (sort {$a cmp $b} keys %prontus_varglb::PORT_PLTS) {
        my $name = $key;
        $name =  $prontus_varglb::PORT_PLTS_NOM{$key} if ($prontus_varglb::PORT_PLTS_NOM{$key} ne '');
        $name =~ s/^\s+//;
        $name =~ s/\s+$//;
        if ($name =~ /(.*?)\.(.*?)$/i) {
            $name =~ s/\.$2//ig;
        };

        $PORTS_TO_ORDER{$key} = $name;
    };


    foreach $key (sort {lc($PORTS_TO_ORDER{$a}) cmp lc($PORTS_TO_ORDER{$b})} keys %PORTS_TO_ORDER) {
        my $val_display = $prontus_varglb::PORT_PLTS_NOM{$key};
        $val_display =~ s/^\s+//;
        $val_display =~ s/\s+$//;
        my $value = $key;
        my $seleccionado;


        my $incluir_item = 'S';

        #~ print STDERR "  \value[$value]\n";
        if ( ($prontus_varglb::USERS_PERFIL eq 'P') or ($prontus_varglb::USERS_PERFIL eq 'E') ) { # Periodista o Editor
            # Mostrar solo las portadas permitidos al usuario conectado.
            $incluir_item = &port_asoc($value);
            # print STDERR "  \nincluir_item[$incluir_item]";
        };

        if ($incluir_item eq 'S') {
            if (! -f "$dir_tpl_port/$value") {
                print "Content-Type: text/html\n\n";
                &glib_html_02::print_pag_result("","Error: Archivo plantilla de portada no existe: $dir_tpl_port/$clave");
                print STDERR "Error: Archivo plantilla de portada no existe: $dir_tpl_port/$clave\n";
                exit;
            };
            $val_display = $value if ($val_display eq '');
            if ( $value eq $valor_clave ) {
                $seleccionado = 'selected="selected"';
            };
            $lista = $lista . '<option value="' . $value . '" ' . $seleccionado . '>';
            $lista = $lista . $val_display . "</option>\n";
        };
    };

    $lista = $lista . q{</select>};

    return $lista;
};


# ---------------------------------------------------------------
sub port_asoc {
    my ($p) = $_[0];
    my ($key2);
    foreach $key2 (keys %prontus_varglb::PORTUSERS) {
        my ($port, $usr) = split /\|/, $key2;
        # print STDERR "\n usr[$usr] y prontus_varglb::USERS_ID[$prontus_varglb::USERS_ID] y port[$port] y p[$p]"; # debug
        if ( ($usr eq $prontus_varglb::USERS_ID) and ($port eq $p) ) {
            return 'S';
        };
    };
    return 'N';
};




# ---------------------------------------------------------------
sub generar_js_spare {
    return ''; # ESTO ES PORQUE LAS SPARES SE DEPRECATEARON
    my($path_dir_port) = shift;
    my($js, $entry, $spares, $port);

    my $path_dir_tport =  $prontus_varglb::DIR_SERVER .
    $prontus_varglb::DIR_TEMP .
    $prontus_varglb::DIR_EDIC .
    $prontus_varglb::DIR_NROEDIC .
    $prontus_varglb::DIR_SPARE;

    # Recorre y genera array de tport.
    foreach $entry (keys %prontus_varglb::PORT_PLTS) {
        if (-f("$path_dir_port/$entry")) {
            $port = $entry;
            $port =~ s/\..*$//; # borrar extension
            $spares = $prontus_varglb::PORT_PLTS{$entry}; # contiene los spare separados por ; <--- P11: AHORA VIENE SOLO UN '1'
            $spares =~ s/;/\,/g;
            $spares =~ s/ +\,/\,/g; # elimina espacios posibles entre medio
            $spares =~ s/\, +/\,/g; # elimina espacios posibles entre medio

            $spares = &spares_validos($spares, $path_dir_tport); # valida q los spares existan, retornando solo los existentes.

            $js .= 'var arr_tport_' . $port . '_label = new Array(' . $spares . ");\n";
            $js .= 'var arr_tport_' . $port . '_value = new Array(' . $spares . ");\n";
        };
    };
    $js .= "var arr_tport_0_label = new Array('                                ');\n";
    $js .= "var arr_tport_0_value = new Array('');\n";

    return $js;
};
# ---------------------------------------------------------------
sub spares_validos {
# devuelve solo los pares existentes.
    my ($spares, $path_dir_tport) = @_;
    my ($k);
    my (@arr_spr) = split(/\,/, $spares);
    $spares = '';
    foreach $k (@arr_spr) {
        if (-f("$path_dir_tport/$k")) {
            $spares .= "'$k',";
        };
    };
    $spares =~ s/\,$//;
    if ($spares eq '') {
        $spares = "''";
    };
    return $spares;
};
# ---------------------------------------------------------------
sub get_elements_tport {
    my ($port, $tipo, $path_dir_tport) = @_;
    my ($elements, $entry, @entries);

    # Abre directorio.
    opendir(DIR, $path_dir_tport) || die "Can't opendir" . $path_dir_tport . $!;
    @entries = readdir(DIR);
    closedir DIR;

    # Ordena
    @entries = sort {lc $a cmp lc $b} (@entries);
    # Recorre y genera elementos.
    foreach $entry (@entries) {
        if ($entry !~ /^\./g) {
            if ((-f("$path_dir_tport/$entry")) and ($entry =~ /^$port\_/)) {
                if ($tipo eq 'label') {
                    $entry =~ s/^$port\_//i;
                    $entry =~ s/\..*$//; # borrar extension
                    $elements .= "'$entry',"
                }
                else { # value
                    $elements .= "'$entry',"
                };
            };
        };
    };
    $elements =~ s/\,$//;
    return $elements;

};

# ---------------------------------------------------------------
sub get_port {
    my ($port, $newer_edic, $dir_tpl_port) = @_;
    if ($port eq '') {
        $port = &get_default_port($newer_edic, $dir_tpl_port);
    };
    # Genera combo html de secciones
    my $html_port = &get_html_port($port, $dir_tpl_port);

    # si aun no hay port definida, toma la 1a. de la combo
    if ($port eq '') {
        $html_port =~ /value="(.+?)"/i;
        $port = $1;
    };
    return ($port, $html_port);

};
# ---------------------------------------------------------------
sub generar_js_base_ports {
    my $bport;
    my $portadas;
    my $js = '';
    foreach $bport (@prontus_varglb::BASE_PORTS) {
    if ((not exists $prontus_varglb::PORT_PLTS{$bport}) and ($bport)) {
        print "Content-Type: text/html\n\n";
        &glib_html_02::print_pag_result("Ha ocurrido un problema","Una o m&aacute;s portadas de la edici&oacute;n base no han sido declaradas como portadas v&aacute;lidas en el archivo de configuraci&oacute;n.");
        exit;
    };
    $portadas .= "'$bport',";

    };
    $portadas =~ s/\,$//;
    if ($portadas) {
        $js = 'var arr_base_ports = new Array(' . $portadas . ");\n";
    }
    else {
        $js = "var arr_base_ports = new Array(' ');\n";
    };
    return $js;
};
# ---------------------------------------------------------------
sub set_ctrl_fecha {
    my $buffer = shift;
    if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
        my $uno = '1';
        $buffer =~ s/%%_CONTROL_FECHA%%/$uno/is;
    }
    else {
        $buffer =~ s/%%_CONTROL_FECHA%%//is;
    };
    return $buffer;
};

# ---------------------------------------------------------------
sub set_multi_vista {
    my $buffer = shift;
    my $multi_vista;
    if (keys(%prontus_varglb::MULTIVISTAS)) {
        $multi_vista = 1;
    };
    my $vistas;
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        $vistas .= "$mv,";
    };
    $vistas =~ s/\,$//;
    $buffer =~ s/%%_MULTI_VISTA%%/$multi_vista/isg;
    $buffer =~ s/%%_VISTAS%%/$vistas/isg;
    return $buffer;

};
# ---------------------------------------------------------------
# a partir de 11.2.17 el rayo va incorporado al guardar portada
sub set_rayo {
    my $buffer = shift;
    $buffer =~ s/<!--rayo-->.*<!--\/rayo-->//isg;
    return $buffer;

    # my $buffer = shift;
    # if (keys(%prontus_varglb::CLUSTERING_SERVER) <= 0) {
        # $buffer =~ s/<!--rayo-->.*<!--\/rayo-->//isg;
    # };
    # return $buffer;
};

# ---------------------------------------------------------------
sub set_admin_port {
    my $buffer = shift;
    if ($prontus_varglb::ADMIN_PORT eq 'NO') {
        $buffer =~ s/<!--ADMIN_PORT-->.*<!--\/ADMIN_PORT-->//isg;
    };
    return $buffer;
};

# ---------------------------------------------------------------
sub get_edic {
    my $dir_edics = shift;
    my $edic;
    my $newer_edic;

    if ($prontus_varglb::MULTI_EDICION eq 'SI') {
        # Generar combo con lista de ediciones.
        $edic = &glib_cgi_04::param('_edic');

        # Si la edicion no viene por parametro, muestra la mas nueva o bien la base.
        if ($edic eq '') {
            if ($prontus_varglb::EDICBASE_INI_SELECTED ne 'SI') {
                $newer_edic = &lib_prontus::get_newer_edic();
                $edic = $newer_edic;
            };

            if ($edic eq '') {
                $edic = $prontus_varglb::DIR_UNICAEDIC;
                $edic =~ s/^\///;
            };
        };

        if ($edic eq '') {
            print "Content-Type: text/html\n\n";
            &glib_html_02::print_pag_result("Error en Prontus Multi-Edici&oacute;n","Para ingresar al Administrador de Art&iacute;culos debe existir a lo menos 1 Edici&oacute;n.");
            exit;
        };
    }
    else {
        $edic = $prontus_varglb::DIR_UNICAEDIC;
        $edic =~ s/^\///; # elimina calificador de directorio (/ al ppio.)
    };

    # Chequea dirs de trabajo de la edicion seleccionada.
    my $dir_dest_edic = "$dir_edics/$edic";
    &lib_prontus::check_dirs_edic($dir_dest_edic);

    return ($edic, $newer_edic);
};
# ---------------------------------------------------------------
sub get_html_ediciones {
    my $dir_edics = shift;
    # Generar cod. html correspondiente a la combo de ediciones
    my $html_ediciones = &lib_prontus::generar_popupdirs_from_dir($dir_edics, 'cmb_edic', $FORM{'_edic'}, 1, '', '', '', $prontus_varglb::NRO_EDICS_WORK, 'STRDESC');
    my $qty_base_ports = @prontus_varglb::BASE_PORTS;
    # warn "qty_base_ports[$qty_base_ports]";
    if (($qty_base_ports <= 0) && ($prontus_varglb::MULTI_EDICION eq 'SI')) {
        $html_ediciones =~ s/<option value="base".*?<\/option>//is; # eliminar de la combo la edic. base.
    };
    return $html_ediciones;
};


# ---------------------END SCRIPT-----------------------
