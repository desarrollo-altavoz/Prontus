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
# prontus_secc_guardar.cgi.
#
# ---------------------------------------------------------------
# UBICACION.
# -----------
# /prontus/.
#
# ---------------------------------------------------------------
# PROPOSITO.
# -----------
# Mantencion Secciones. Crea, actualiza y/o elimina.
#
# ---------------------------------------------------------------
# LLAMADAS A SCRIPTS.
# ------------------------------
# Location: prontus_secc_admin.cgi (Administrador de Secciones).
#
# ---------------------------------------------------------------
# INVOCACIONES ACEPTADAS.
# ------------------------
# Desde pagina 'Administrador de Secciones' (/prontus4_nots/cpan/core/mant_seccs/prontus_secc_admin.html) boton 'Guardar'.
#
# ---------------------------------------------------------------
# ARCHIVOS DE ENTRADA.
# ------------------------
# Plantillas: /prontus4_nots/cpan/core/mant_seccs/mensajes.html (para mensajes de error).
#
# ---------------------------------------------------------------
# ARCHIVOS DE SALIDA.
# ------------------------
# Paginas web: No registra.
#
# ---------------------------------------------------------------
# Tablas.
# -------------------
# SECC - TEMAS - SUBTEMAS.
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# HISTORIAL DE VERSIONES.
# ---------------------------
# 1.0 - 16/10/2003 - YCH - Primera version.
# ---------------------------------------------------------------


# -------------------------------BEGIN SCRIPT---------------
# ---------------------------------------------------------------
# DIRECTIVAS DE COMPILACION.
# ------------------------

BEGIN {
    # Captura STDERR
    use lib_stdlog;
    &lib_stdlog::set_stdlog($0, 51200);
};

use DBI;

use prontus_varglb; &prontus_varglb::init();
use glib_dbi_02;
use glib_html_02;
use glib_cgi_04;
use glib_str_02;
#use lib_secc;
use lib_tags;

use lib_prontus;
use strict;



# ---------------------------------------------------------------
# MAIN.
# -------------

my (%FORM, $BD);


my %DATA_VISTAS;

main: {

    # Rescatar parametros recibidos.
    &glib_cgi_04::new();
    $FORM{'_path_conf'} = &glib_cgi_04::param('_path_conf');
    # Ajusta path_conf para completar path y/o cambiar \ por /
    $FORM{'_path_conf'} = &lib_prontus::ajusta_pathconf($FORM{'_path_conf'});

    # Carga variables de configuracion.
    &lib_prontus::load_config($FORM{'_path_conf'});  # Prontus 6.0
    $FORM{'_path_conf'} =~ s/^$prontus_varglb::DIR_SERVER//;

    # Control de usuarios obligatorio
    ($prontus_varglb::USERS_ID, $prontus_varglb::USERS_PERFIL) = &lib_prontus::check_user();

    # user no valido
    if ($prontus_varglb::USERS_ID eq '') {
        #~ &glib_html_02::print_pag_result('Error',$prontus_varglb::USERS_PERFIL, 1, 'exit=1,ctype=1');
        &glib_html_02::print_json_result(0, $prontus_varglb::USERS_PERFIL, 'exit=1,ctype=1');
    };

    # Acceso permitido solo para admin o editor
    if ($prontus_varglb::USERS_PERFIL eq 'P') {
      &glib_html_02::print_pag_result('Acceso a Area Restringida','La funcionalidad requerida no está disponible para perfil Redactor',1,'exit=1,ctype=1');
    };


    $FORM{'_id'}= &glib_cgi_04::param('_id');
    if ($FORM{'_id'} ne '') {
        if (($FORM{'_id'} !~ /^[0-9]+$/) || (!$FORM{'_id'})) {
            &glib_html_02::print_json_result(0, 'Id no válido', 'exit=1,ctype=1');
        };
    };

    $FORM{'_nom'} = &glib_str_02::trim(&glib_cgi_04::param('_nom'));
    if ($FORM{'_nom'} eq '') {
        &glib_html_02::print_json_result(0, 'Por favor, ingresa el nombre del ítem', 'exit=1,ctype=1');
    };
    $FORM{'_nom'} = &lib_prontus::despulga_item_tax($FORM{'_nom'});
    if ($FORM{'_nom'} eq '') {
        &glib_html_02::print_json_result(0, 'Debe ingresar por lo menos dos letras en el nombre del ítem', 'exit=1,ctype=1');
    } else {
        my $strlen = length($FORM{'_nom'});
        if ($strlen < 2) {
            &glib_html_02::print_json_result(0, 'Debe ingresar por lo menos dos letras en el nombre del ítem', 'exit=1,ctype=1');
        };
    };

    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        my $k = '_nom' . "-$mv"; # ej: _nom-pda
        my $nom = &glib_cgi_04::param($k);
        $nom = &lib_prontus::despulga_item_tax(&glib_str_02::trim($nom));
        $nom = $FORM{'_nom'} if (!$nom);
        my $strlen_mv = length($nom);
        if ($strlen_mv < 2) {
            &glib_html_02::print_json_result(0, 'Debe ingresar por lo menos dos letras en el nombre del ítem de la vista ' . $mv, 'exit=1,ctype=1');
        };
    };

    # Conectar a BD
    my $msg_err_bd;
    ($BD, $msg_err_bd) = &lib_prontus::conectar_prontus_bd();
    if (! ref($BD)) {
        &glib_html_02::print_json_result(0, $msg_err_bd, 'exit=1,ctype=1');
    };

    my $new_id;
    my $msg;
    if ($FORM{'_id'}) {
        $msg = &do_update();
        $new_id = $FORM{'_id'};
    } else {
        ($msg, $new_id) = &do_insert();
    };
    &glib_html_02::print_json_result(0, $msg, 'exit=1,ctype=1') if ($msg);

    $BD->disconnect;

    my $resp;
    $resp->{'status'} = 1;
    $resp->{'theId'} = $new_id;
    $resp->{'theName'} = &lib_prontus::escape_xml($FORM{'_nom'});

    # En el caso de existir multivista, devolver tambien.
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        my $k = '_nom' . "-$mv"; # ej: _nom-pda
        my $nom = &glib_cgi_04::param($k);
        $nom = &lib_prontus::despulga_item_tax(&glib_str_02::trim($nom));
        $nom = $FORM{'_nom'} if (!$nom);
        $resp->{'theName_' . $mv} = &lib_prontus::escape_xml($nom);
    };

    # Se libera el caché de los tags del fid
    &lib_tags::clear_cache($prontus_varglb::PRONTUS_ID);

    # utf8::encode($resp->{'theName'});

    # binmode(STDOUT, ":utf8");

    # Se usa este metodo porque la glib_html_02 no puede imprimir Hashs, sólo strings.
    print "Content-Type: text/html\n\n";
    # my $json = new JSON;
    # $json->to_json($resp);
    print &JSON::to_json($resp);
    exit;

}; # main.

# ---------------------------------------------------------------
# SUB-RUTINAS.
# ---------------------------------------------------------------

# ---------------------------------------------------------------
sub do_insert {

    # Comprobar si el nombre ya existe.
    my $msg = &lib_tags::check_nom($BD, 0, $FORM{'_nom'});
    return ($msg, 0) if ($msg ne '');

    # Inserta registro en la tabla.
    my $nom_quoted = $BD->quote($FORM{'_nom'});
    my $nom4vistas = &get_nom4vistas();
    $nom4vistas = $BD->quote($nom4vistas);

    my $sql;
    $sql = "insert into TAGS values(NULL, $nom_quoted, 0, '1', $nom4vistas)";
    my $id = &lib_prontus::insert_dev_id($sql, $BD, $prontus_varglb::MOTOR_BD);
    return ('', $id);

}; # guardar_new_entidad.

# ---------------------------------------------------------------
sub do_update {
    # Comprobar si el nombre ya existe.
    my $msg = &lib_tags::check_nom($BD, $FORM{'_id'}, $FORM{'_nom'});
    return ($msg, 0) if ($msg ne '');

    # Update registro en la tabla.
    my $nom_quoted = $BD->quote($FORM{'_nom'});
    my $nom4vistas = &get_nom4vistas();
    $nom4vistas = $BD->quote($nom4vistas);

    my $sql;
    $sql = "update TAGS set TAGS_TAG = $nom_quoted, TAGS_NOM4VISTAS = $nom4vistas where TAGS_ID = $FORM{'_id'}";
    # print STDERR "sql-u[$sql]\n";
    $BD->do($sql) || return &lib_prontus::handle_internal_error($BD->errstr, 'Error actualizando ítem en la base de datos', 'exit=0');
    return '';
};
# ---------------------------------------------------------------
sub get_nom4vistas {
    my $nom4vistas;
    foreach my $mv (keys %prontus_varglb::MULTIVISTAS) {
        my $k = '_nom' . "-$mv"; # ej: _nom-pda
        my $nom = &glib_cgi_04::param($k);
        $nom = &lib_prontus::despulga_item_tax(&glib_str_02::trim($nom));
        $nom = $FORM{'_nom'} if (!$nom);
        $nom4vistas .= "$mv\t$nom\n";
    };
    $nom4vistas =~ s/\n$//; # elimina \n sobrante
    return $nom4vistas;
};


# ----------------------------END SCRIPT---------------------
