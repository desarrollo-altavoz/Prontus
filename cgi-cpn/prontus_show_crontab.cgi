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
# Desplegar pagina con imagen de mapa de portada.
# ---------------------------------------------------------------
# LLAMADAS A ARCHIVOS EXTERNOS.
# ------------------------------
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# http://192.168.6.24/cgi-cpn/prontus_show_crontab.cgi?path_conf=/prontus_toolbox/cpan/prontus_toolbox.cfg
# ---------------------------------------------------------------
# PLANTILLAS HTML UTILIZADAS.
# ------------------------

# ---------------------------------------------------------------

# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 03/07/2006 - Primera Version.

# -------------------------------BEGIN SCRIPT--------------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ---------------------------
BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};
use prontus_varglb; &prontus_varglb::init();
use glib_fildir_02;
use lib_prontus;
use glib_html_02;

use glib_cgi_04;

use DBI;
use glib_dbi_02;
use lib_secc;

# ---------------------------------------------------------------
# MAIN.
# -------------

my ($BD, %FORM);

#  print "Content-Type: text/html\n\n"; # debug
# Rescatar parametros recibidos.
&glib_cgi_04::new();
$FORM{'nomport'} = &glib_cgi_04::param('nomport'); # onda portada.html
$FORM{'path_conf'} = &glib_cgi_04::param('path_conf');
# Ajusta path_conf para completar path y/o cambiar \ por /
$FORM{'path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'path_conf'});

# print STDERR "BD[$prontus_varglb::NOM_BD]";

&lib_prontus::load_config($FORM{'path_conf'});
$FORM{'path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

my $plantilla = $prontus_varglb::DIR_SERVER . $prontus_varglb::DIR_CORE . "/prontus_show_crontab.html";

my $pagina = &glib_fildir_02::read_file($plantilla);

$pagina =~ s/%%REL_PATH_PRONTUS%%/$prontus_varglb::RELDIR_BASE\/$prontus_varglb::PRONTUS_ID/ig;
$pagina =~ s/%%_PRONTUS_ID%%/$prontus_varglb::PRONTUS_ID/ig;

$cron_buffer = `crontab -l`;
@cron_lines = split(/\n+/, $cron_buffer);
my $lines;
foreach $line (@cron_lines) {
    next if ($line !~ /\w/);
    next if ($line =~ /^#/);
    next if ($line !~ /prontus/);
    $line =~ s/\/usr\/bin\/perl//isg;
    $line =~ s/\/usr\/local\/bin\/php//isg;
    $line =~ s/\/[\w\.\-_\/]+\///isg;
    $line =~ s/ +/ /isg;
    $lines .= "$line\n";
};
$lines = "\nNo hay scripts Prontus ingresados en Crontab\n" if (!$lines);
$pagina =~ s/%%_crontab%%/$lines/ig;

print "Content-Type: text/html\n\n";
print $pagina;



# ---------------------------------------------------------------
# SUB-RUTINAS.
# -------------


# -------------------------------END SCRIPT----------------------
