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
# Actualiza todos los articulos de un publicador en base a su template
# El path al archivo de configuracion va en duro en el script.

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------

BEGIN {

    use FindBin '$Bin';
    unshift(@INC,$Bin); # Para dejar disponibles las librerias

};
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_fildir_02;
use glib_cgi_04;
use lib_prontus;
use lib_tax;
use glib_hrfec_02;
use lib_logproc;

use strict;

# Captura STDERR
use lib_stdlog;
&lib_stdlog::set_stdlog($0, 51200);

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------

my ($TOT_REGS, $LOG_FILE, $PATH_CONF, $TOT_REGS_CON_ERR);
my ($MODO_WEB) = 0;
my (%TAXONOMIAS_TO_REGEN);
my ($DIRFECHA_INI); # DIR FECHA A PARTIR DEL CUAL EL SCRIPT DEBE PROCESAR

my ($FID_TYPES_STR);
my ($MULTIVISTAS_STR);

my (%FID_TYPES);
my (%MULTIVISTAS_REGEN);

my ($MULTIVISTAS_DEFAULT) = 0;
my ($FECHAINI_MAYORQUE) = 0;
my ($FECHAINI_MENORQUE) = 0;

# ------------------------------------------------------------------------------
# Los nuevos parametros de entrada son:
# $ARGV[0] -> Path absoluto al CFG, desde la raiz de la máquina
# $ARGV[1] -> Puede ser: >yyyymmdd  o <yyyymmdd  Ejemplo: '>20120101'
#    Si se usa yyyymmdd: se tomará >yyyymmdd
#    Si se usa @all: yyyymmdd, se tomará vacio
# $ARGV[2] -> Fids separados por coma. Ejemplo: fid_general,fid_link
#    En caso se quererlos todos, se puede usar: @all
# $ARGV[3] -> Multivistas separadas por coma. Ejemplo: movil,en
#    Para la vista principal se usa: @default
#    En caso se quererlos todos, se puede usar: @all o bien dejar vacio
# ------------------------------------------------------------------------------


# Parametros de entrada
if ($ARGV[0]) {
    close STDOUT;
    $PATH_CONF          = $ARGV[0];
    $DIRFECHA_INI       = $ARGV[1];
    $FID_TYPES_STR      = $ARGV[2];
    $MULTIVISTAS_STR    = $ARGV[3];

    print STDERR "DIR_SERVER: [$prontus_varglb::DIR_SERVER]\n";
    print STDERR "PATH_CONF: [$PATH_CONF]\n";
    print STDERR "DIRFECHA_INI: [$DIRFECHA_INI]\n";
    print STDERR "FID_TYPES_STR: [$FID_TYPES_STR]\n";
    print STDERR "MULTIVISTAS_STR: [$MULTIVISTAS_STR]\n";

} else {

    &glib_cgi_04::new(); # Rescata parametros
    $PATH_CONF = &glib_cgi_04::param('path_conf');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $PATH_CONF = &lib_prontus::ajusta_pathconf($PATH_CONF);
    $MODO_WEB = 1;
    print "Content-Type: text/html\n\n";
    $| = 1;
};

# Carga variables de configuracion.
&lib_prontus::load_config($PATH_CONF);
&lib_prontus::write_log('Actualiz. masiva', 'Articulo', '');

# Establece log file
$lib_logproc::LOG_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/prontus_art_regen_log.html";
$lib_logproc::MODO_WEB = $MODO_WEB;

# Init
&lib_logproc::flush_log();
&lib_logproc::writeRule();
&lib_logproc::add_to_log_count("INICIANDO PROCESO DE ACTUALIZACION DE ARTICULOS");

# Valida las fechas
&valida_y_ajusta_fechaini();

# Valida las multivistas
&valida_y_ajusta_multivistas();

# Valida los FIDs
&valida_y_ajusta_fids();

# reparsea articulos en base a su tpl.
&reparsea_artic();

&lib_logproc::add_to_log_count("PROCESO DE ACTUALIZACION DE ARTICULOS FINALIZADO");
&lib_logproc::writeRule();

$TOT_REGS = '0' if ($TOT_REGS eq '');
$TOT_REGS_CON_ERR = '0' if ($TOT_REGS_CON_ERR eq '');

print STDERR "TOT_REGS[$TOT_REGS]\n";
print STDERR "TOT_REGS_CON_ERR[$TOT_REGS_CON_ERR]\n";

&lib_logproc::add_to_log("Nro. de registros procesados: $TOT_REGS\nRegistros con Errores: $TOT_REGS_CON_ERR");
&lib_logproc::add_to_log_finish("Operaci&oacute;n finalizada.");

&finishLoading('', $TOT_REGS);
exit;


# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------

sub reparsea_artic {
# Recorre todos los articulos via file system y repobla la BD.

    # Conectar a BD
    my $msg_err_bd;
    my $base;
    ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        &finishLoading("Error: $msg_err_bd\nProceso abortado.");
        &lib_logproc::handle_error("Error: $msg_err_bd\nProceso abortado.");
    };

    my ($ruta_dir) = $prontus_varglb::DIR_SERVER
                   . $prontus_varglb::DIR_CONTENIDO
                   . $prontus_varglb::DIR_ARTIC;

    my (@lisdir, $dirfecha);

    @lisdir = &glib_fildir_02::lee_dir($ruta_dir);

    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    @lisdir = grep !/edic/, @lisdir; # Elimina directorios edic

    # @lisdir = grep /^\d{8}$/, @lisdir; # Deja sólo los directorios con Dirfecha
    @lisdir = sort {$b <=> $a} (@lisdir);

    # Para cada dirfecha, primero procesa vista normal.
    my $dircounter = 0;
    foreach $dirfecha (@lisdir) {
        if ($DIRFECHA_INI ne '') {
            if ($FECHAINI_MAYORQUE == 1) {
                next if ($dirfecha < $DIRFECHA_INI);
            } elsif ($FECHAINI_MENORQUE == 1) {
                next if ($dirfecha > $DIRFECHA_INI);
            }
        }
        #~ print STDERR "$ruta_dir/$dirfecha/xml\n";
        if (-d "$ruta_dir/$dirfecha/xml") {
            $dircounter++;
            &messageLoading('Directorios Procesados: <b>' . $dircounter . '</b>');
            &lib_logproc::add_to_log_count("Procesando DIR [$dirfecha/xml]");
            # print STDERR "Procesando DIR [$dirfecha/xml]\n";
            &procesa_files("$ruta_dir/$dirfecha/xml", $dirfecha);
        };
    };

    # regenera taxonomia (artics relacionados)
    if ($prontus_varglb::TAXONOMIA_NIVELES =~ /^[1-3]$/) {
        &lib_logproc::writeRule();
        &lib_logproc::add_to_log_count("Regenerando art&iacute;culos relacionados...");
        &regen_taxonomia(\%TAXONOMIAS_TO_REGEN, $base);
        &lib_logproc::add_to_log_count("Art&iacute;culos relacionados...OK");
    };

    $base->disconnect;
    &finishLoading('');
};

# ---------------------------------------------------------------
sub procesa_files {
# Lee todos los articulos del directorio y los reparsea en base a su tpl.

    my ($nom_campo, $val_campo, $dir_adjunto, $estilo);
    my ($ruta_dir_xml) = $_[0];
    my ($art_dirfecha) = $_[1];
    # my ($mv) = $_[2];

    my @lisfile = &glib_fildir_02::lee_dir($ruta_dir_xml);
    @lisfile = grep !/^\./, @lisfile; # Elimina directorios . y ..
    my $count_files_in_dir = 0;
    foreach my $k_xml (@lisfile) {
        $count_files_in_dir++;
        # Valida q el XML exista con largo <> 0 y que ademas su nombre corresponda a un timestamp valido.
        if ((-s "$ruta_dir_xml/$k_xml") && ($k_xml =~ /^(\d{14})\.(xml)$/) && (! -d "$ruta_dir_xml/$k_xml")) {
            my $ts = $1;

            my $artic_obj = Artic->new(
                            'prontus_id'        => $prontus_varglb::PRONTUS_ID,
                            'public_server_name'=> $prontus_varglb::PUBLIC_SERVER_NAME,
                            'cpan_server_name'  => $prontus_varglb::IP_SERVER,
                            'document_root'     => $prontus_varglb::DIR_SERVER,
                            'ts'                => $ts,
                            'campos'=>{}) || &registra_artic_error("\t\t\t\tError inicializando objeto articulo: $Artic::ERR TS[$ts]");

            next if (!ref($artic_obj));

            # Carga hash de taxonomias para luego regenerar relacionados
            my %campos_xml = $artic_obj->get_xml_content();


            if($FID_TYPES_STR eq '' || $FID_TYPES{$campos_xml{'_fid'}}) {

                if($MULTIVISTAS_DEFAULT) {
                    # Generar vista (a partir del xml)
                    $artic_obj->generar_vista_art('', $prontus_varglb::STAMP_DEMO, $prontus_varglb::PRONTUS_KEY)
                            || &registra_artic_error("\t\t\t\tError: $Artic::ERR");

                }

                foreach my $mv (keys %MULTIVISTAS_REGEN) {
                    # Generar vista (a partir del xml)
                    $artic_obj->generar_vista_art($mv, $prontus_varglb::STAMP_DEMO, $prontus_varglb::PRONTUS_KEY)
                            || &registra_artic_error("\t\t\t\tError: $Artic::ERR");
                }

                my $secc4tax = $campos_xml{'_seccion1'};
                my $tem4tax = $campos_xml{'_tema1'};
                my $stem4tax = $campos_xml{'_subtema1'};
                $secc4tax = '0' if ($secc4tax eq '');
                $tem4tax = '0' if ($tem4tax eq '');
                $stem4tax = '0' if ($stem4tax eq '');
                $TAXONOMIAS_TO_REGEN{$secc4tax . '_' . $tem4tax . '_' . $stem4tax} = '1';

                # $TOT_REGS++ if (!$mv);  # Total de articulos procesados, las iteraciones de multivista no se cuentan.
                $TOT_REGS++;
            }
        };# if

    };# foreach
    &lib_logproc::add_to_log("\t\t\t\t$count_files_in_dir archivos procesados en el DIR") if ($count_files_in_dir);
};

# --------------------------------------------------------------------
sub regen_taxonomia {
# Regenera art. relacionados
    my ($taxonomia, $base) = @_;
    my ($secc, $tem, $stem);
    my ($tripleta);

    &lib_tax::set_vars($prontus_varglb::DIR_CONTENIDO,
                        $prontus_varglb::DIR_ARTIC,
                        $prontus_varglb::DIR_PAG,
                        $prontus_varglb::DIR_TEMP,
                        $prontus_varglb::DIR_TAXONOMIA,
                        $prontus_varglb::NUM_RELAC_DEFAULT,
                        $prontus_varglb::CONTROLAR_ALTA_ARTICULOS);

    foreach $tripleta (keys %$taxonomia) {
        ($secc, $tem, $stem) = split(/_/, $tripleta);
        $secc = '' if($secc eq '0');
        $tem = '' if($tem eq '0');
        $stem = '' if($stem eq '0');
        &lib_tax::generar_relacionados($secc, $tem, $stem, $base, '');

        # Ahora parsea art relacionados para MVs
        my $mv;
        foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
            &lib_tax::generar_relacionados($secc, $tem, $stem, $base, $mv);
        };
    };
};

# ---------------------------------------------------------------
sub registra_artic_error {
    my $msg = $_[0];
    $TOT_REGS_CON_ERR++;
    &lib_logproc::add_to_log($msg);
};

# ---------------------------------------------------------------
sub finishLoading {

    my ($msg, $total) = ($_[0], $_[1]);
    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_art_regen.js";
    if($total) {
      $msg = '{"status":1, "msg":"'.$msg.'", "total": "'.$total.'"}';
    } else {
      $msg = '{"status":1, "msg":"'.$msg.'", "total": "0"}';
    }
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
};

# ---------------------------------------------------------------
sub messageLoading {

    my ($msg) = ($_[0]);
    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_art_regen.js";
    if($msg) {
      $msg = '{"status":0, "inprogress":"'.$msg.'"}';
      &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
    }
};

# ---------------------------------------------------------------
sub valida_y_ajusta_fechaini {

    $DIRFECHA_INI =~ s/"//sig;

    if ($DIRFECHA_INI =~ /^([<>]?)(\d{8})$/) { # 20120412 - jor - agrega "" a er
        $DIRFECHA_INI = $2;
        my $signo = $1;
        if($signo eq '>' || $signo eq '') {
            $FECHAINI_MAYORQUE = 1;

        } elsif($signo eq '<') {
            $FECHAINI_MENORQUE = 1;

        } else {
            $DIRFECHA_INI = '';

        }

    } else {
        $DIRFECHA_INI = '';
    }
    print STDERR "FECHAINI_MAYORQUE[$FECHAINI_MAYORQUE]\n";
    print STDERR "FECHAINI_MENORQUE[$FECHAINI_MENORQUE]\n";
}

# ---------------------------------------------------------------
sub valida_y_ajusta_multivistas {

    $MULTIVISTAS_STR =~ s/\s//g;

    if($MULTIVISTAS_STR eq '' || $MULTIVISTAS_STR eq '@all') {
        %MULTIVISTAS_REGEN = %prontus_varglb::MULTIVISTAS;
        $MULTIVISTAS_DEFAULT = 1;
        return;
    }

    my @splitresult = split(/,/, $MULTIVISTAS_STR);
    foreach my $mv (@splitresult) {
        if($prontus_varglb::MULTIVISTAS{$mv}) {
            $MULTIVISTAS_REGEN{$mv} = 1;

        } elsif($mv eq '@normal') {
            $MULTIVISTAS_DEFAULT = 1;
        }
    }
}

# ---------------------------------------------------------------
sub valida_y_ajusta_fids {

    $FID_TYPES_STR =~ s/\s//g;

    # print STDERR "chequeando fids: FID_TYPES[$FID_TYPES]\n";
    if($FID_TYPES_STR eq '@all' || $FID_TYPES_STR eq '') {
        $FID_TYPES_STR = '';
        return;
    }

    my %form_plts_tmp;
    foreach my $fidkey (keys %prontus_varglb::FORM_PLTS) {
        $fidkey =~ /^(.*?):.*?/;
        my $fid = $1;
        $form_plts_tmp{$fid} = 1;
    }

    my @splitresult = split(/,/, $FID_TYPES_STR);
    foreach my $fid (@splitresult) {
        if($form_plts_tmp{$fid}) {
            $FID_TYPES{$fid} = 1;
        }
    }
}

# -------------------------------END SCRIPT----------------------
