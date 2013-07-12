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
    unshift(@INC,$Bin); # Para dejar disponibles las librerias
};

use prontus_varglb; &prontus_varglb::init();

use lib_prontus;
use lib_logproc;

use glib_fildir_02;

$| = 1;

my %PORTS_EDIC;
my %BASE_PORTS;
my $DIR_EDICS;
my $DIR_EDICS_TPL;
my $TABULADOR = "        ";

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

# ---------------------------------------------------------------
# MAIN.
# -------------
my %FORM;
my $TOT_REGS;
my $TOT_REGS_CON_ERR;

main : {

    close STDOUT;

    $FORM{'path_conf'} = $ARGV[0];
    $FORM{'check_pp'}  = $ARGV[1];
    $FORM{'operador'}  = $ARGV[2];
    $FORM{'cmb_edic'}  = $ARGV[3];

    #TODO - Por ahora sólo hay modo script, no hay modo Web

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'path_conf'});
    &lib_prontus::write_log('Actualiz. masiva', 'Portadas', '');

    # Establece log file
    $lib_logproc::LOG_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/prontus_port_regen_log.html";
    $lib_logproc::JS_FILE = "$prontus_varglb::DIR_CPAN/procs/result_port_regen.js";
    $lib_logproc::MODO_WEB = 0;

    # Init
    &lib_logproc::flush_log();
    &lib_logproc::writeRule();
    &lib_logproc::add_to_log_count("INICIANDO PROCESO DE ACTUALIZACION DE PORTADAS");

    $DIR_EDICS = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CONTENIDO$prontus_varglb::DIR_EDIC";
    $DIR_EDICS_TPL = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_TEMP$prontus_varglb::DIR_EDIC";

    &valida_param();
    &carga_portadas();

    #~ print STDERR "Procesando... $FORM{'operador'} $FORM{'cmb_edic'}\n";
    my (@ediciones) = &get_edics4update($FORM{'cmb_edic'}, $FORM{'operador'});
    foreach my $edic (@ediciones) {
        &regenerar_portadas($edic);
    };

    # Borra cache de listas de articulos del cpan
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");

    &lib_logproc::add_to_log_count("PROCESO DE ACTUALIZACION DE PORTADAS FINALIZADO");
    &lib_logproc::writeRule();

    $TOT_REGS = '0' if ($TOT_REGS eq '');
    $TOT_REGS_CON_ERR = '0' if ($TOT_REGS_CON_ERR eq '');

    print STDERR "TOT_REGS[$TOT_REGS]\n";
    print STDERR "TOT_REGS_CON_ERR[$TOT_REGS_CON_ERR]\n";

    &lib_logproc::add_to_log("Nro. de portadas procesadas: $TOT_REGS\nRegistros con Errores: $TOT_REGS_CON_ERR");
    &lib_logproc::add_to_log_finish("Operaci&oacute;n finalizada.");

    &lib_logproc::finishLoading('', $TOT_REGS);
    exit;

}; # main



# -------------------------------------------------------------------------------------------------#
# SUB-RUTINAS.
# -------------
sub valida_param {

    if($FORM{'cmb_edic'} ne '' && $FORM{'cmb_edic'} ne 'base' && $FORM{'cmb_edic'} !~ /\d+_\d+_\d+_\d+/) {
        &lib_logproc::finishLoading("Error: Edición indicada no es válida");
        &lib_logproc::handle_error("Error: Edición indicada no es válida");
    };

    if(! -d "$DIR_EDICS/$FORM{'cmb_edic'}") {
        &lib_logproc::finishLoading("Error: La edición indicada no existe");
        &lib_logproc::handle_error("Error: La edición indicada no existe");
    };

    if($FORM{'operador'} ne '' && $FORM{'operador'} !~ /igual|mayor|menor/) {
        &lib_logproc::finishLoading("Error: El parámetro operador no es válido");
        &lib_logproc::handle_error("Error: El parámetro operador no es válido");
    };
};

# -------------------------------------------------------------------------------------------------#
sub get_edics4update {

    my $cmb_edic = shift;
    my $operador = shift;
    my @ediciones;

    #~ &lib_logproc::add_to_log_count("LEYENDO LAS EDICIONES A PROCESAR:");

    if($prontus_varglb::MULTI_EDICION ne 'SI') {
        &lib_logproc::add_to_log_count("No hay multiedición, solo se procesa edición [base]");
        push @ediciones, 'base';
        return @ediciones;
    };



    if($cmb_edic eq '') {
        &lib_logproc::add_to_log_count("Se toman ediciones base, vigente y ultima");
        @ediciones = &lib_prontus::get_edics4update();

    } else {
        if($operador ne 'mayor' && $operador ne 'menor') {
            &lib_logproc::add_to_log_count("Se toma exactamente la edición indicada [$cmb_edic]");
            push @ediciones, $cmb_edic;
            return @ediciones;
        } else {
            if($operador eq 'menor') {
                &lib_logproc::add_to_log_count("Se toman ediciones MENOR o igual a [$cmb_edic]");
            } else {
                &lib_logproc::add_to_log_count("Se toman ediciones MAYOR o igual a [$cmb_edic]");
            }
        }

        # Abre directorio.
        opendir(DIR, $DIR_EDICS) || die "Can't opendir" . $DIR_EDICS . $!;
        my @entries = readdir(DIR);
        closedir DIR;
        # Descendentemente.
        my @totentries = sort {$b cmp $a} (@entries);

        $nro_elem = 0;
        foreach my $edic (@totentries) {
            next if($edic =~ /^\./);
            next unless((-d("$DIR_EDICS/$edic")) and ($nro_elem < $prontus_varglb::NRO_EDICS_WORK));
            if ($operador eq 'menor') {
                if (($edic cmp $cmb_edic) > 0) {
                    #~ print STDERR "$edic (descartada)\n";
                    next;
                }
            } else {
                if (($edic cmp $cmb_edic) < 0) {
                    #~ print STDERR "$edic (descartada)\n";
                    next;
                };
            }
            #~ print STDERR "$edic (push)\n";
            push @ediciones, $edic;
            $nro_elem = $nro_elem + 1;
        }
    }
    return @ediciones;
};
# -------------------------------------------------------------------------------------------------#
# Regenera todas las portadas publicadas, segun las ediciones indicadas
sub regenerar_portadas {

    my $edic = shift;

    &lib_logproc::add_to_log_count("Procesando Edicion [$edic]");

    if(!-d "$DIR_EDICS/$edic") {
        # Si no hay carpeta, no hay xmls... no se puede hacer nada
        &lib_logproc::add_to_log_count("${TABULADOR}Error: No existe la carpeta de la edición [$edic]");
        return;
    };

    my %port2process;

    # Selector para ver que portadas se actualizaran
    if($edic eq 'base') {
        %port2process = %BASE_PORTS;
    } else {
        %port2process = %PORTS_EDIC;
    };

    foreach $portada (sort keys %port2process) {

        my $buffer = &get_xml_buffer($portada, $edic);
        if($buffer eq '') {
            $TOT_REGS_CON_ERR++;
            next;
        } else {
            &lib_logproc::add_to_log_count("${TABULADOR}Regenerando portada [$portada]");
            $TOT_REGS++;
        };

        # Rescatar la info de c/artic de la seccion correspondiente
        while ($buffer =~ /<rowartic>[ \n]*?<dir>(\d+?)<\/dir>[ \n]*?<file>(.*?)<\/file>[ \n]*?<area>(\d*?)<\/area>[ \n]*?<ord>(\d*?)<\/ord>[ \n]*?(<vb>(\w*?)<\/vb>)?[ \n]*?<?i?n?>?([\w\/\-]*?)<?\/?i?n?>?[ \n]*?<?o?u?t?>?([\w\/\-]*?)<?\/?o?u?t?>?[ \n]*?<?p?u?b?>?(\d?)<?\/?p?u?b?>?[ \n]*?<\/rowartic>/isg) {

            my ($dirfecha,$art,$area,$prio,$pub,$ext_art,$vb) = '';
            ($dirfecha,$art,$area,$prio,$vb,$pub) = ($1,$2,$3,$4,$6,$9);

            $lib_prontus::AREA{$art} = $area;      # Asocia area al articulo.
            $lib_prontus::PRIO{$art} = $prio;      # Asocia prioridad correspondiente.
            if ($vb eq '') { $vb = 1; };
            $lib_prontus::VB{$art} = $vb;      # Asocia VoBo correspondiente.
            $lib_prontus::DIR_FECHA{$art} = $dirfecha;
        };

        my $EDIC_SITE = "$DIR_EDICS/$edic/port";
        my $EDIC_TMPL = "$DIR_EDICS_TPL/nroedic/port";

        # Primero para la vista por defecto (o sea, sin vista)
        my $mv = '';
        my $sin_regen_xml = 0;
        my $ts_preview = '';
        my $users_perfil = 'A';
        &lib_prontus::make_portada("$EDIC_SITE/$portada", "$EDIC_TMPL/$portada", $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
                               $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
                               $EDIC, $sin_regen_xml, $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
                               $ts_preview, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $users_perfil);

        # Ahora proceso multivistas
        $sin_regen_xml = 1; # para no reescribir el xml
        $ts_preview = '';
        $users_perfil = 'A';
        foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
            &lib_prontus::make_portada("$EDIC_SITE/$portada", $DST_TSEC . "$EDIC_TMPL/$portada", $prontus_varglb::DIR_SERVER, $prontus_varglb::PRONTUS_ID,
                                     $mv, $prontus_varglb::PUBLIC_SERVER_NAME, $prontus_varglb::PRONTUS_KEY, $prontus_varglb::STAMP_DEMO,
                                     $EDIC, $sin_regen_xml, $prontus_varglb::STAMP_DEMO_RSS, $prontus_varglb::CONTROL_FECHA,
                                     $ts_preview, $prontus_varglb::CONTROLAR_ALTA_ARTICULOS, $users_perfil);
        };

        &lib_prontus::write_log('Actualizar', 'Portada (regen)', "$EDIC_SITE/$portada");

        %lib_prontus::AREA = ();
        %lib_prontus::PRIO = ();
        %lib_prontus::VB = ();
        %lib_prontus::DIR_FECHA = ();

        if($FORM{'check_pp'} eq 'si') {
            &exec_postproceso("$EDIC_SITE/$portada", "$EDIC_TMPL/$portada");
        };

    };
};

# ---------------------------------------------------------------
sub exec_postproceso {
  # 8.0 POST-PROCESO
  # Una vez escrito la portada, ubica el nombre del script de post-proceso (con extension y con path absoluto completo) y lo ejecuta.
  # Script de postproceso es optativo y puede ir en cualquier parte de la portada

    my $port_site = shift;
    my $port_tmpl = shift;

    # LEE PORT
    $buffer = &glib_fildir_02::read_file($port_tmpl);
    if ($buffer !~ /\n/) { # 8.0
        $buffer =~ s/\r/\n/sg;
    };

    my $dir_macros = "$prontus_varglb::DIR_SERVER/$prontus_varglb::PRONTUS_ID/plantillas/edic/nroedic/macros";
    $buffer = &lib_prontus::add_macros($buffer, $dir_macros);
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

            my $cmd = "$rutaScript/$pp $port_site $prontus_varglb::PUBLIC_SERVER_NAME >/dev/null 2>&1 &";
            print STDERR "[" . &glib_hrfec_02::get_dtime_pack4() . "]$cmd\n";
            system $cmd;
        };
    };
};
# -------------------------------------------------------------------------------------------------#
sub get_xml_buffer {

    my $portada = shift;
    my $edic = shift;

    my $xml = $portada;
    $xml =~ s/\.\w+$/.xml/;
    my $rutaxml = "$DIR_EDICS/$edic/xml/$xml";
    if(!-f $rutaxml) {
        &lib_logproc::add_to_log_count("${TABULADOR}Error: No existe xml de portada [$xml]");
        return '';
    };
    my $buffer = &glib_fildir_02::read_file($rutaxml);
    return $buffer;
}
# -------------------------------------------------------------------------------------------------#
# Obtiene de la lista de tpls. de portadas la primera cuyo nombre sin extension coincida con el q viene por param.
sub get_nom_port {

    my $port_xml = $_[0];
    my $dir_tpl_seccs = $DST_TSEC;

    $port_xml =~ s/\.\w+$//;
    my ($entry);
    foreach $entry (keys %prontus_varglb::PORT_PLTS) {
        if ((-s "$dir_tpl_seccs/$entry") and (! -d "$dir_tpl_seccs/$entry")) {
            # print "entry[$entry] - port_xml[$port_xml]\n";
            if ($entry =~ /^$port_xml\.\w+$/) {
                return $entry;
            };
        };
    };
    return '';
};

# -------------------------------------------------------------------------------------------------#
sub carga_portadas {

    if($prontus_varglb::MULTI_EDICION ne 'SI') {
        %BASE_PORTS = %prontus_varglb::PORT_PLTS;
        return;
    };

    foreach my $port (@prontus_varglb::BASE_PORTS) {
        $BASE_PORTS{$port} = 1;
    };
    foreach my $port (keys %prontus_varglb::PORT_PLTS) {
        next if($BASE_PORTS{$port});
        $PORTS_EDIC{$port} = 1;
    };
    return;
};
