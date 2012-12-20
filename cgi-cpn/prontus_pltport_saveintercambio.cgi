#!/usr/bin/perl

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

    $FORM{'Lst_PORT1'} = &glib_cgi_04::param('Lst_PORT1');
    $FORM{'Lst_PORT2'} = &glib_cgi_04::param('Lst_PORT2');

    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta _path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});

    # Control de usuarios obligatorio chequeando la cookie contra el dbm.
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # Acceso permitido solo para admin
    if (($prontus_varglb::ADMIN_PORT ne 'SI') or ($prontus_varglb::USERS_PERFIL ne 'A')) {
        &glib_html_02::print_json_result(0, 'La funcionalidad requerida está disponible sólo para el administrador del sistema, siempre que ésta haya sido previamente configurada.', 'exit=1,ctype=1');
    };


    my $dir_port = $prontus_varglb::DIR_SERVER .
    $prontus_varglb::DIR_TEMP .
    $prontus_varglb::DIR_EDIC .
    $prontus_varglb::DIR_NROEDIC .
    $prontus_varglb::DIR_SECC;

    my $port1 = "$dir_port/" . $FORM{'Lst_PORT1'};
    my $port2 = "$dir_port/" . $FORM{'Lst_PORT2'};

    if ((! -s $port1) || (! -s $port2))  {
        &glib_html_02::print_json_result(0, 'Portadas no válidas', 'exit=1,ctype=1');
    };

    # intercambiar plantillas
    my $ret = &intercambiar_files($port1, $port2);
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        $port1 = "$dir_port-$mv/" . $FORM{'Lst_PORT1'};
        $port2 = "$dir_port-$mv/" . $FORM{'Lst_PORT2'};
        $ret = &intercambiar_files($port1, $port2);
    };


    # intercambiar contenido en todas las vistas
    my $dst_port = $prontus_varglb::DIR_SERVER .
    $prontus_varglb::DIR_CONTENIDO .
    $prontus_varglb::DIR_EDIC .
    "/base" .
    $prontus_varglb::DIR_SECC;

    $port1 = "$dst_port/" . $FORM{'Lst_PORT1'};
    $port2 = "$dst_port/" . $FORM{'Lst_PORT2'};

    $ret = &intercambiar_files($port1, $port2);

    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        $port1 = "$dst_port-$mv/" . $FORM{'Lst_PORT1'};
        $port2 = "$dst_port-$mv/" . $FORM{'Lst_PORT2'};
        $ret = &intercambiar_files($port1, $port2);
    };

    # Intercambiar XML
    # Directorio de destino de los xml de port
    my $dst_xml = $prontus_varglb::DIR_SERVER .
    $prontus_varglb::DIR_CONTENIDO .
    $prontus_varglb::DIR_EDIC .
    "/base" .
    '/xml';

    # compone nombre de xml
    my $nomport1_xml = $FORM{'Lst_PORT1'};
    $nomport1_xml =~ s/\.\w+$/\.xml/;

    my $nomport2_xml = $FORM{'Lst_PORT2'};
    $nomport2_xml =~ s/\.\w+$/\.xml/;


    $port1 = "$dst_xml/" . $nomport1_xml;
    $port2 = "$dst_xml/" . $nomport2_xml;

    $ret = &intercambiar_files($port1, $port2);



    # Intercambiar salida RSS
    # Directorio de destino de los xml de port
    my $dst_rss = $prontus_varglb::DIR_SERVER .
    $prontus_varglb::DIR_CONTENIDO .
    $prontus_varglb::DIR_EDIC .
    "/base" .
    '/rss';

    $port1 = "$dst_rss/" . $nomport1_xml;
    $port2 = "$dst_rss/" . $nomport2_xml;

    $ret = &intercambiar_files($port1, $port2);



    # Intercambiar plantilla RSS
    my $dst_rss_plt = $prontus_varglb::DIR_SERVER .
    $prontus_varglb::DIR_TEMP .
    $prontus_varglb::DIR_EDIC .
    $prontus_varglb::DIR_NROEDIC .
    '/rss';

    $port1 = "$dst_rss_plt/" . $nomport1_xml;
    $port2 = "$dst_rss_plt/" . $nomport2_xml;

    $ret = &intercambiar_files($port1, $port2);
    # CVI - 10/01/2012 - Se Logea esta accion
    &lib_prontus::write_log('Intercambiar', 'Portada', $FORM{'Lst_PORT1'} . ' <-> '. $FORM{'Lst_PORT2'});

    # CVI - 17/03/2011 - Borra cache de no publicados
    &glib_fildir_02::borra_dir("$prontus_varglb::DIR_SERVER$prontus_varglb::DIR_CPAN/data/cache");

    &glib_html_02::print_json_result(1, 'Las portadas seleccionadas fueron intercambiadas correctamente', 'exit=1,ctype=1');
};





sub intercambiar_files {
    my ($path1, $path2) = @_;

    print STDERR "[$path1] [$path2]\n\n";

    if ((! -f $path1) || (! -f $path2)) {
        return 0;
    };



    my $buffer1 = &glib_fildir_02::read_file($path1);
    my $buffer2 = &glib_fildir_02::read_file($path2);

    # Pisa path1 con path2
    &glib_fildir_02::write_file($path1, $buffer2);

    # Pisa path2 con buffer1
    &glib_fildir_02::write_file($path2, $buffer1);


};




# ----------------------------END-SCRIPT-----------------------------------
