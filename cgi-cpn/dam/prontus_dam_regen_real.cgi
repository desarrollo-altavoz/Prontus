#!/usr/bin/perl



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
    $pathLibsProntus = $Bin;
    unshift(@INC,$pathLibsProntus);
    $pathLibsProntus =~ s/\/dam$//;
    unshift(@INC,$pathLibsProntus); # Para dejar disponibles las librerias de prontus
};
use prontus_varglb; &prontus_varglb::init();
use glib_html_02;
use glib_fildir_02;
use glib_cgi_04;
use lib_prontus;
use lib_tax;
use glib_hrfec_02;
use lib_logproc;
use lib_dam;

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
print STDERR "------- comenzando el proceso -------\n";
if ($ARGV[0]) {
    close STDOUT;
    $PATH_CONF = $ARGV[0];

    # Fix Dir Server
    my $dir_server = $Bin;
    $dir_server =~ s/\/[^\/]+\/dam$//;
    $prontus_varglb::DIR_SERVER = $dir_server;

    print STDERR "DIR_SERVER: [$prontus_varglb::DIR_SERVER]\n";
    print STDERR "PATH_CONF: [$PATH_CONF]\n";

} else {
    &glib_cgi_04::new(); # Rescata parametros
    $PATH_CONF = &glib_cgi_04::param('path_conf');

    # Ajusta path_conf para completar path y/o cambiar \ por /
    $PATH_CONF = &lib_prontus::ajusta_pathconf($PATH_CONF);
    $MODO_WEB = 1;
    print "Content-Type: text/html\n\n";
    $| = 1;
};

print STDERR "Load Config... $PATH_CONF\n";
# Carga variables de configuracion.
&lib_prontus::load_config($PATH_CONF);
&lib_prontus::write_log('Actualiz. masiva', 'Articulo', '');

# Establece log file
$lib_logproc::LOG_FILE = "$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/procs/prontus_dam_regen_log.html";
$lib_logproc::MODO_WEB = $MODO_WEB;

print STDERR "Log File... $lib_logproc::LOG_FILE\n";

# Init
&lib_logproc::flush_log();
&lib_logproc::writeRule();
&lib_logproc::add_to_log_count("INICIANDO PROCESO DE ACTUALIZACION DE MULTIMEDIA");

# reparsea articulos en base a su tpl.
&regenera_dam();

&lib_logproc::add_to_log_count("PROCESO DE ACTUALIZACION DE MULTIMEDIA FINALIZADO");
&lib_logproc::writeRule();

$TOT_REGS = '0' if ($TOT_REGS eq '');
$TOT_REGS_CON_ERR = '0' if ($TOT_REGS_CON_ERR eq '');

&lib_logproc::add_to_log("Nro. de registros procesados: $TOT_REGS\nRegistros con Errores: $TOT_REGS_CON_ERR");
&lib_logproc::add_to_log_finish("Operaci&oacute;n finalizada.");

&finishLoading('', $TOT_REGS);
print STDERR "------- proceso terimado -------\n\n";
exit;


# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------

sub regenera_dam {
# Recorre todos los articulos via file system y repobla la BD.

    # Inicia conexion a BD
    my ($base, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($base)) {
        &finishLoading("Error: $msg_err_bd\nProceso abortado.");
        &lib_logproc::handle_error("Error: $msg_err_bd\nProceso abortado.");
    };

    my ($ruta_dir) = $prontus_varglb::DIR_SERVER
                   . $prontus_varglb::DIR_CONTENIDO
                   . $prontus_varglb::DIR_ARTIC;

    my (@lisdir, $dirfecha);
    print STDERR "Leyendo XMLs... $ruta_dir\n";
    @lisdir = &glib_fildir_02::lee_dir($ruta_dir);

    @lisdir = grep !/^\./, @lisdir; # Elimina directorios . y ..
    @lisdir = grep !/edic/, @lisdir; # Elimina directorios edic

    @lisdir = sort {$a <=> $b} (@lisdir);



    # Para cada dirfecha procesa los articulos
    my $dircounter = 0;
    foreach $dirfecha (@lisdir) {
        if (-d "$ruta_dir/$dirfecha/xml") {
            $dircounter++;
            &messageLoading('Vista: <b>Default</b>, Directorios Procesados: <b>' . $dircounter . '</b>');
            &lib_logproc::add_to_log_count("Procesando DIR [$dirfecha/xml]");
            print STDERR "  Procesando DIR [$dirfecha/xml]\n";
            &procesa_files("$ruta_dir/$dirfecha/xml", $dirfecha, $base);
        };
    };

    $base->disconnect;
    &finishLoading('');
};

# ---------------------------------------------------------------
sub procesa_files {
# Lee todos los articulos del directorio y los reparsea en base a su tpl.

    my ($nom_campo, $val_campo, $dir_adjunto, $estilo);
    my ($ruta_dir_xml, $art_dirfecha, $base) = @_;

    my @lisfile = &glib_fildir_02::lee_dir($ruta_dir_xml);
    @lisfile = grep !/^\./, @lisfile; # Elimina directorios . y ..
    my $count_files_in_dir = 0;
    my ($prontus_id, $dir_server, $ip_server) = ($prontus_varglb::PRONTUS_ID, $prontus_varglb::DIR_SERVER, $prontus_varglb::IP_SERVER);
    foreach my $k_xml (@lisfile) {

        # Valida q el XML exista con largo <> 0 y que ademas su nombre corresponda a un timestamp valido.
        if ((-s "$ruta_dir_xml/$k_xml") && (! -d "$ruta_dir_xml/$k_xml") && ($k_xml =~ /^(\d{14})\.(xml)$/)) {
            $count_files_in_dir++;
            my $ts_artic = $1;
            &lib_dam::procesa_artic($ts_artic, , $prontus_id, $dir_server, $ip_server, $base);
            $TOT_REGS++;  # Total de articulos procesados, las iteraciones de multivista no se cuentan.
        };# if

    };# foreach
    &lib_logproc::add_to_log("\t\t\t\t$count_files_in_dir archivos procesados en el DIR") if ($count_files_in_dir);
};

# ---------------------------------------------------------------
sub finishLoading {

    my ($msg, $total) = ($_[0], $_[1]);
    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_dam_regen.js";
    if($total) {
      $msg = '{"status":1, "msg":"'.$msg.'", "total": "'.$total.'"}';
    } else {
      $msg = '{"status":1, "msg":"'.$msg.'"}';
    }
    &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
};

# ---------------------------------------------------------------
sub messageLoading {

    my ($msg) = ($_[0]);
    my $result_file = "$prontus_varglb::DIR_CPAN/procs/result_dam_regen.js";
    if($msg) {
      $msg = '{"status":0, "inprogress":"'.$msg.'"}';
      &glib_fildir_02::write_file("$prontus_varglb::DIR_SERVER$result_file", $msg);
    }
};
# -------------------------------END SCRIPT----------------------
