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

use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_fildir_02;
use lib_prontus;
use glib_cgi_04;
use glib_hrfec_02;
use DBI;
use glib_dbi_02;
use lib_tax;
use lib_quota;
use lib_dd;


# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM);

main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();

    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    if ($prontus_varglb::IP_SERVER ne '') {
        &lib_prontus::test_servers($ENV{'HTTP_REFERER'});
    };

    # user check
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();
    if ($prontus_varglb::USERS_ID eq '') {
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    # Validar quota
    my $msg_err_quota = &lib_quota::check_quota_suficiente();
    &glib_html_02::print_json_result(0, $msg_err_quota, 'exit=1,ctype=1') if ($msg_err_quota);


    # nombre de la vista a previsualizar, o nada.
    $FORM{'_vista'} = &glib_cgi_04::param('_vista');
    if ($FORM{'_vista'} !~ /^\w+$/) {
        &glib_html_02::print_json_result(0, 'Vista no válida.', 'exit=1,ctype=1') if ($FORM{'_vista'} ne '');
    };

    # fecha preview
    my $ts_preview;
    if ($prontus_varglb::CONTROL_FECHA eq 'SI') {
        $FORM{'_fecha_preview'} = &glib_cgi_04::param('_fecha_preview');
        $FORM{'_hora_preview'} = &glib_cgi_04::param('_hora_preview');
        $ts_preview = &get_ts_preview($FORM{'_fecha_preview'}, $FORM{'_hora_preview'});
    };

    # Accion a realizar : preview || update
    $FORM{'_accion'} = &glib_cgi_04::param('_accion');

    # Edicion
    $FORM{'_edic'} = &glib_cgi_04::param('_edic');
    if ($FORM{'_edic'} eq '') {
        $FORM{'_edic'} = $prontus_varglb::DIR_UNICAEDIC;
        $FORM{'_edic'} =~ s/^\///;
    } else {
        if ($FORM{'_edic'} !~ /^\w+$/) {
            &glib_html_02::print_json_result(0, 'Edición no válida.', 'exit=1,ctype=1');
        };
    };

    # Arch. de tpl. de portada. , con extension y sin path. (El Nombre del archivo correspondiente a la portada publicada es el mismo)
    $FORM{'_port'} = &glib_cgi_04::param('_port');
    if ($FORM{'_port'} !~ /^[\w\-]+\.\w+$/) {
        &glib_html_02::print_json_result(0, 'Portada no válida.', 'exit=1,ctype=1');
    };

    # Arma dirs de trabajo
    if (! &set_dirs() ) {
        &glib_html_02::print_json_result(0, '901-Error al componer directorios', 'exit=1,ctype=1');
    };

    # Cargar paraemtros en lib_dd
    &cargar_parametros();
    
    # Detectar portadas.
    my %portadas = &detectar_portadas();

    foreach my $port (keys(%portadas)) {
        #~ print STDERR "port[$port]\n";
        $port =~ /(.*?)\.(.*?)/is;
        my $port_xml_filename = "$1.xml";
        my $port_xml_path = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_EDIC . "/$edic/xml/$port_xml_filename";
        &lib_dd::cargar_areas($port_xml_path, '', $port);
        my $mv = '';
        &lib_prontus::make_portada("$DST_SEC/$port", $DST_TSEC . "/$port", $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
            $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
            $FORM{'_edic'}, '', $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
            '', $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $prontus_varglb::USERS_PERFIL);

        # Ahora proceso multivistas
        foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
            &lib_prontus::make_portada("$DST_SEC/$port", $DST_TSEC . "/$port", $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
            $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
            $FORM{'_edic'}, '1', $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
            '', $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $prontus_varglb::USERS_PERFIL);
        };

        &exec_postproceso($port); # postprocesos de la portada.
        &lib_prontus::write_log('Actualizar', 'Portada', "$DST_SEC/$port");
        use FindBin '$Bin';
        &call_clustering("$DST_SEC/$port", $Bin);
    };
        
    # Vuelve a refrescar la pagina de administracion.
    my $path_conf_rel = $FORM{'_path_conf'}; # 1.3
    $path_conf_rel =~ s/$prontus_varglb::DIR_SERVER//i; # Deja el path de conf. relativo al sitio. # 1.3

    &glib_html_02::print_json_result(1, '', 'exit=1,ctype=1');

};
# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------
sub call_clustering {
    my $fullpath_port = shift;
    my $rutaScript = shift;

    if (keys(%prontus_varglb::CLUSTERING_SERVER) > 0) {
        my $cmd = "$rutaScript/prontus_cluster_port.cgi $fullpath_port >/dev/null 2>&1 &";
        print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
        system $cmd;
    };
};
# ---------------------------------------------------------------

sub get_ts_preview {
    my ($fecha_preview) = $_[0];
    my ($hora_preview) = $_[1];

    if ($fecha_preview =~ /^\d{2}\/\d{2}\/\d{4}$/) {
        my $fprev_iso = &glib_hrfec_02::normaliza_fecha($fecha_preview);
        my $hhmm_prev;
        if ($hora_preview =~ /^(\d\d):(\d\d)$/) {
            $hhmm_prev = $1 . $2 . '00';
        } else {
            $hhmm_prev = '000000';
        };
        my $ts_preview = "$fprev_iso$hhmm_prev";
        return $ts_preview;
    } else {
        &glib_html_02::print_json_result(0, 'Fecha preview no es válida.', 'exit=1,ctype=1') if ($fecha_preview ne '');
    };
};

# ---------------------------------------------------------------
sub captura_area_orden {
    # Recopila areas, prioridades e identificadores de articulos a insertar
    # en la portada (AREA_id,PRIO_id). id es el nombre del archivo del articulo con extension y sin path.
    my @campos = &glib_cgi_04::param();
    foreach my $cod (@campos) {
        if ($cod =~ m/^_area_(\d{14})/) {
            my $ts = $1;
            $lib_prontus::AREA{$ts} = &glib_cgi_04::param($cod);      # Asocia area a id del articulo.
            $lib_prontus::PRIO{$ts} = &glib_cgi_04::param("_orden_$ts"); # Asocia prioridad correspondiente.
            $lib_prontus::VB{$ts} = &glib_cgi_04::param("_vb_$ts");
            my $is_corrupt = &glib_cgi_04::param("_corrupt_$ts"); # '1' | ''

            # Si no se especifica area o prioridad, los articulos no se publican en la portada
            if ( ($lib_prontus::PRIO{$ts} eq '') || ($lib_prontus::PRIO{$ts} eq '0')
                    || ($lib_prontus::AREA{$ts} eq '') || ($lib_prontus::AREA{$ts} eq '0') || ($is_corrupt == 1)) {
                $lib_prontus::AREA{$ts} = '';
                $lib_prontus::PRIO{$ts} = '';
                $lib_prontus::VB{$ts} = '';
            };
            # print STDERR "ts[$ts] area[$lib_prontus::AREA{$ts}] orden[$lib_prontus::PRIO{$ts}]\n";
            # Validar que para areas y prioridades se especifiquen solo digitos.
            if ( ($lib_prontus::AREA{$ts} !~ /^[0-9]+$/) || ($lib_prontus::PRIO{$ts} !~ /^[0-9]+$/) ) {
                $lib_prontus::AREA{$ts} = '';
                $lib_prontus::PRIO{$ts} = '';
            };
        };
    };
};

sub detectar_portadas {
    my @campos = &glib_cgi_04::param();
    my %portadas;
    foreach my $key (@campos) {
        if ($key =~ /^_port_(\d{14})/) {
            my $value = &glib_cgi_04::param($key);
            if (!$portadas{$value}) {
                $portadas{$value} = 1;
            };
        };
    };

    return %portadas;
};

# ---------------------------------------------------------------
sub exec_postproceso {
    my $port = $_[0];
    # 8.0 POST-PROCESO
    # Una vez escrito la portada, ubica el nombre del script de post-proceso (con extension y con path absoluto completo) y lo ejecuta.
    # Script de postproceso es optativo y puede ir en cualquier parte de la portada

    # LEE PORT
    $buffer = &glib_fildir_02::read_file("$DST_TSEC/$port");
    if ($buffer !~ /\n/) { # 8.0
        $buffer =~ s/\r/\n/sg;
    };


    my ($post_proceso, $postProcesoLista);

    while ($buffer =~ /<!--POST_PROCESO=(.+?)-->/isg) {
        $postProcesoLista .= "$1\t";
    };

    use FindBin '$Bin';
    my $rutaScript = $Bin;

    # Ejecuta en bground el proceso pasandole x param. el path completo a la portada.
    my @postProcesos = split(/\t/, $postProcesoLista);
    foreach my $pp (@postProcesos) {
        # para que sea un script valido debe ubicarse en el mismo dir. de cgi del prontus o a lo mas un nivel hacia arriba.
        if ( ($pp =~ /^\w/) or ($pp =~ /^\.\.(\/|\\)\w/) ) {
            
            my $cmd = "$rutaScript/$pp $DST_SEC/$port $prontus_varglb::PUBLIC_SERVER_NAME >/dev/null 2>&1 &";
            print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
            system $cmd;
        };
    };
};

# --------------------------------------------------------------------
sub set_dirs {


    $DDIR = $prontus_varglb::DIR_CONTENIDO . $prontus_varglb::DIR_ARTIC . '/%%DIR_FECHA%%';
    # Directorio de Secciones existentes
    $DST_SEC = $prontus_varglb::DIR_SERVER .
    $prontus_varglb::DIR_CONTENIDO .
    $prontus_varglb::DIR_EDIC .
    "/$FORM{'_edic'}" .
    $prontus_varglb::DIR_SECC;

    # Directorio de destino de los xml de port
    $DST_XML = $prontus_varglb::DIR_SERVER .
    $prontus_varglb::DIR_CONTENIDO .
    $prontus_varglb::DIR_EDIC .
    "/$FORM{'_edic'}" .
    '/xml';

    # Path absoluto al dir. donde residen los templates de portadas.
    $DST_TSEC = $prontus_varglb::DIR_SERVER .
    $prontus_varglb::DIR_TEMP .
    $prontus_varglb::DIR_EDIC .
    $prontus_varglb::DIR_NROEDIC .
    $prontus_varglb::DIR_SECC;

    # Path relativo (al sitio) hacia directorio de ubicacion de las portadas publicadas.
    $REL_SEC = $prontus_varglb::DIR_CONTENIDO .
    $prontus_varglb::DIR_EDIC .
    "/$FORM{'_edic'}" .
    $prontus_varglb::DIR_SECC;


    # Chequea la existencia de los directorios.
    if ( ! (&glib_fildir_02::check_dir($DST_SEC)) ) { return 0; };
    if ( ! (&glib_fildir_02::check_dir($DST_XML)) ) { return 0; };
    # print STDERR "paso3[$DST_XML]\n";
    if ( ! (&glib_fildir_02::check_dir($DST_TSEC)) ) { return 0; };
    # print STDERR "paso4\n";


    return 1;
};

sub cargar_parametros {
    my @campos = &glib_cgi_04::param();
    foreach my $cod (@campos) {
        $lib_dd::FORM{$cod} = &glib_cgi_04::param($cod);
    };
};


# -------------------------------END SCRIPT----------------------
