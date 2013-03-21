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

# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------

# ---------------------------------------------------------------
# INVOCACIONES REALIZADAS.
# ------------------------

# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------

# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------

# ---------------------------------------------------------------
# Tablas.
# ------------------------
# No utiliza.

# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------

# ---------------------------------------------------------------
# Prontus 9.0 - YCH - Ver detalles en /release_prontus9.txt

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

use glib_html_02;
use glib_fildir_02;
use lib_prontus;

use glib_cgi_04;
use strict;

# ---------------------------------------------------------------
# MAIN.
# ---------------------------------------------------------------
my (%FORM);


main: {
    # Rescatar parametros recibidos
    &glib_cgi_04::new();

    $FORM{'NEW_PORT'} = &glib_cgi_04::param('NEW_PORT'); # nombre c/ext. y sin path de la nueva portada.

    $FORM{'Lst_PORTACT'} = &glib_cgi_04::param('Lst_PORT3');

    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    $FORM{'portada_base'} = &glib_cgi_04::param('portada_base');

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # Acceso permitido solo para admin
    if (($prontus_varglb::ADMIN_PORT ne 'SI') or ($prontus_varglb::USERS_PERFIL ne 'A')) {
        &glib_html_02::print_pag_result("Acceso a Area Restringida","La funcionalidad requerida está disponible sólo para el administrador del sistema, siempre que ésta haya sido previamente configurada.");
        exit;
    };

    my $origen;

    my $dir_port = $prontus_varglb::DIR_SERVER .
                 $prontus_varglb::DIR_TEMP .
                 $prontus_varglb::DIR_EDIC .
                 $prontus_varglb::DIR_NROEDIC .
                 $prontus_varglb::DIR_SECC;

    $origen = "$dir_port/" . $FORM{'Lst_PORTACT'};

    if (!(-s $origen)) {
        &glib_html_02::print_json_result(0, 'Plantilla seleccionada no es válida', 'exit=1,ctype=1');
        exit;
    };

    my ($msg);

    # Si el nombre nuevo no trae extension, poner la de la plt de origen.
    if ($FORM{'NEW_PORT'} !~ /\.\w+$/) {
        my $extension_aux;
        $FORM{'Lst_PORTACT'} =~ /(\.\w+)$/;
        $extension_aux = $1;
        $FORM{'NEW_PORT'} = $FORM{'NEW_PORT'} . $extension_aux;
    };

    if ($FORM{'NEW_PORT'} !~ /^[a-z\_0-9][a-z\_\-0-9]*\.[a-z\_0-9\-]+$/) {
        &glib_html_02::print_json_result(0, 'Nombre de plantilla no válido', 'exit=1,ctype=1');
    };

    # Copia template origen a destino
    my $destino = "$dir_port/" . $FORM{'NEW_PORT'};

    # Valida q no exista una portada con el mismo nombre.
    if (-s $destino) {
        $msg = "Ya existe otra plantilla de portada con el nombre: $FORM{'NEW_PORT'}. Por favor escoja uno distinto.";
        &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1');
    } else { # duplicar
        my $portada = &glib_fildir_02::read_file($origen);
        &glib_fildir_02::check_dir($dir_port);
        &glib_fildir_02::write_file($destino, $portada);
        #print STDERR "dir_port[$dir_port], destino[$destino], origen[$origen], portada[$portada]\n";
        if (-s $destino) { # verifica q se haya grabado la nueva plantilla
            &update_cfg();
            # Duplica vistas
            my $mv;
            foreach $mv (keys %prontus_varglb::MULTIVISTAS) {
                my $origen_mv = "$dir_port-$mv/" . $FORM{'Lst_PORTACT'};
                my $destino_mv = "$dir_port-$mv/" . $FORM{'NEW_PORT'};
                my $portada_mv = &glib_fildir_02::read_file($origen_mv);
                &glib_fildir_02::check_dir("$dir_port-$mv");
                &glib_fildir_02::write_file($destino_mv, $portada_mv);
            };
            # CVI - 10/01/2012 - Se Logea esta accion
            &lib_prontus::write_log('Duplicar', 'Portada', $FORM{'Lst_PORTACT'} . ' -> '. $destino);

            $msg = "La Plantilla seleccionada ha sido duplicada correctamente con el nombre: $FORM{'NEW_PORT'}";
            &glib_html_02::print_json_result(1, $msg, 'exit=1,ctype=1');
        } else {
            $msg = "No se pudo grabar la nueva portada: $FORM{'NEW_PORT'}";
            &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1');
            unlink $destino; # borra por si quedo con largo cero.
        };
    };
};

# ---------------------------------------------------------------
sub update_cfg {
    # nom_port --> nombre con extension y sin path.

    my $nomcfg;
    if ($FORM{'_path_conf'} =~ /(.*)\.cfg$/) {
        $nomcfg = $1;
    };

    #print STDERR "nomcfg[$nomcfg]";

    my ($buffer) = &glib_fildir_02::read_file("$nomcfg-port.cfg");

    # Respalda antes de aplicar cambios.
    my ($bak) = "$nomcfg-port.cfg";
    my $dir_bak = $bak;
    $dir_bak =~ s/\/$prontus_varglb::PRONTUS_ID\-port\.cfg$//;
    $dir_bak .= '/_unused';
    &glib_fildir_02::check_dir($dir_bak);

    $bak =~ s/\/cpan\/$prontus_varglb::PRONTUS_ID\-port\.cfg$/\/cpan\/_unused\/$prontus_varglb::PRONTUS_ID\-port\.bak/i;
    &glib_fildir_02::write_file($bak, $buffer);

    my ($crlf) = qr/\x0a\x0d|\x0d\x0a|\x0a|\x0d/;

    $buffer =~ s/$crlf/\x0a/sg;

    # Duplica linea del cfg
    $buffer =~ /( *PORT_PLTS *= *['"]$FORM{'Lst_PORTACT'}(\(.*\)){0,3}['"].*\n?)/i;
    my $newline = $1;
    $newline =~ s/(PORT_PLTS *= *['"])$FORM{'Lst_PORTACT'}((\(.*\)){0,3}['"].*\n?)/\1$FORM{'NEW_PORT'}\2/i;
    if($newline =~ /PORT_PLTS *= *['"](.*?)\((.*?)\)\((.*?)\)\((.*?)\)['"]/i) {
		$newline = "PORT_PLTS = \"$1($1)($3)($4)\"";
	};
    print STDERR "[newline]$newline";
    $buffer =~ s/( *PORT_PLTS *= *['"]$FORM{'Lst_PORTACT'}(\(.*\)){0,3}['"].*\n?)/\1$newline/i;
    # Configurar portada como base si es q se requiere.
    if (($FORM{'portada_base'} == '1') && ($prontus_varglb::MULTI_EDICION eq 'SI')) {
        if ($buffer =~ /( *BASE_PORTS *= *['"].*?['"])/i) {
            # print STDERR "ENTRA\n";
            my $newline = $1;

            $newline =~ s/(['"]).*?(['"])/\1$FORM{'NEW_PORT'}\2/i;
            if ($buffer =~ s/( *BASE_PORTS *= *['"].*?['"])/\1\n$newline/i) {
              # print STDERR "ok\n";
            };
        } else {
            my $newline = "BASE_PORTS = '$FORM{'NEW_PORT'}'";
            $buffer .= "\n\n$newline";
        };
    };
    
  # Guarda el archivo cfg.
  &glib_fildir_02::write_file("$nomcfg-port.cfg", $buffer);
  # print STDERR "CFG[$buffer]\n";
};
# ----------------------------END-SCRIPT-----------------------------------
